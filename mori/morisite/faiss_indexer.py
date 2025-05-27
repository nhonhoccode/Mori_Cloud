import os
import torch
import faiss
import numpy as np
from PIL import Image
import open_clip
from django.conf import settings
from sentence_transformers import SentenceTransformer
from concurrent.futures import ThreadPoolExecutor
from .models import Photo
import time
import logging
from tqdm import tqdm
from django.utils import timezone

class FaissImageIndexer:
    def __init__(self, user=None, model_name='ViT-L-14', pretrained='datacomp_xl_s13b_b90k', feature_dim=768, batch_size=32, num_workers=8):
        self.device = "cpu"
        self.feature_dim = feature_dim
        self.user = user
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                    model_name, device=self.device, pretrained=pretrained
                )
        self.tokenizer = open_clip.get_tokenizer(model_name)
        with torch.no_grad():
            dummy = torch.randn(1, 3, 224, 224).to(self.device)
            dummy_feat = self.model.encode_image(dummy)
        if dummy_feat.shape[-1] != self.feature_dim:
            print(f"⚠️ Feature dimension ({dummy_feat.shape[-1]}) không khớp với {self.feature_dim}, cập nhật.")
            self.feature_dim = dummy_feat.shape[-1]

        self.index = self.load_faiss_index()

    @property
    def faiss_index_path(self):
        if self.user:
            file_name = f"faiss_index_user_{self.user.id_user}.bin"
        else:
            file_name = "faiss_index_global.bin"
        return os.path.join(settings.MEDIA_ROOT, file_name)

    def create_faiss_index(self):
        """Tạo FAISS Index mới"""
        print(f"⚠️ Tạo mới FAISS Index tại {self.faiss_index_path}")
        index = faiss.IndexFlatIP(self.feature_dim)
        self.save_faiss_index(index)  
        time.sleep(0.2)  
        return index

    def load_faiss_index(self):
        """Tải hoặc tạo FAISS index riêng cho từng user hoặc global"""
        try:
            if os.path.exists(self.faiss_index_path):
                index = faiss.read_index(self.faiss_index_path)
                if index.d != self.feature_dim:
                    print(f"⚠️ Kích thước FAISS index ({index.d}) không khớp với feature_dim ({self.feature_dim}), tạo mới.")
                    return self.create_faiss_index()
                print(f"✅ FAISS index loaded từ {self.faiss_index_path}")
                return index
            else:
                print(f"⚠️ Không tìm thấy {self.faiss_index_path}, tạo FAISS index mới.")
                return self.create_faiss_index()
        except Exception as e:
            print(f"❌ Lỗi khi tải FAISS index: {e}")
            return self.create_faiss_index()

    def save_faiss_index(self, index):
        """Lưu FAISS index vào file"""
        try:
            os.makedirs(os.path.dirname(self.faiss_index_path), exist_ok=True)
            faiss.write_index(index, self.faiss_index_path)
            print(f"✅ FAISS index đã được lưu vào {self.faiss_index_path}")
        except Exception as e:
            print(f"❌ Lỗi khi lưu FAISS index: {e}")

    def load_and_preprocess(self, path):
        try:
            if not os.path.exists(path):
                print(f"❌ Ảnh không tồn tại: {path}")
                return None, path
            image = Image.open(path).convert("RGB")
            return self.preprocess(image), path
        except Exception as e:
            print(f"❌ Lỗi đọc ảnh {path}: {e}")
            return None, path

    def extract_image_features_batch(self, image_paths):
        images = []
        valid_paths = []

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            results = list(executor.map(self.load_and_preprocess, image_paths))

        for img_preprocessed, path in results:
            if img_preprocessed is not None:
                images.append(img_preprocessed)
                valid_paths.append(path)

        if len(images) == 0:
            print("❌ Không có ảnh hợp lệ trong batch!")
            return None, None

        image_input = torch.stack(images).to(self.device)

        with torch.no_grad():
            image_features = self.model.encode_image(image_input)

        image_features /= image_features.norm(dim=-1, keepdim=True)

        return image_features.cpu().numpy().astype(np.float32), valid_paths


    def add_photo_to_faiss(self, photo):
        try:
            if not os.path.exists(photo.photo.path):
                print(f"❌ Ảnh không tồn tại: {photo.photo.path}")
                return False

            features, valid_paths = self.extract_image_features_batch([photo.photo.path])
            if features is None or len(features) == 0:
                print(f"⚠️ Ảnh {photo.id_photo} không thể trích xuất đặc trưng.")
                return False

            if features.shape[1] != self.feature_dim:
                print(f"❌ Kích thước vector của ảnh {photo.id_photo} ({features.shape[1]}) "
                      f"không khớp với FAISS ({self.feature_dim}) → Bỏ qua ảnh này.")
                return False

            faiss_id = self.index.ntotal
            self.index.add(features)

            if self.user is None:
                print(f"FAISS index global: {faiss_id}")
                photo.faiss_id_public = faiss_id
            else:
                print(f"FAISS index user {self.user.id_user}: {faiss_id}")
                photo.faiss_id = faiss_id
            photo.save()

            if photo.faiss_id is None and self.user is not None:
                raise ValueError(f"❌ Không thể cập nhật faiss_id cho ảnh {photo.id_photo}")

            self.save_faiss_index(self.index)
            print(f"✅ Ảnh {photo.id_photo} đã được thêm vào FAISS với ID: {faiss_id}")
            return faiss_id
        except Exception as e:
            print(f"❌ Lỗi khi thêm ảnh vào FAISS: {e}")
            return False

    def add_images(self, photos):
        """Thêm nhiều ảnh vào FAISS index"""
        image_paths = [photo.photo.path for photo in photos]
        print(f"🔄 Bắt đầu trích xuất & thêm vào FAISS index với batch size = {self.batch_size}")
        for i in tqdm(range(0, len(image_paths), self.batch_size), desc="🔄 Trích xuất & Thêm chunk"):
            chunk_paths = image_paths[i:i + self.batch_size]
            chunk_photos = photos[i:i + self.batch_size]
            try:
                features, valid_paths = self.extract_image_features_batch(chunk_paths)
                if features is None:
                    continue
                start_id = self.index.ntotal
                self.index.add(features)
                for j, photo in enumerate(chunk_photos):
                    if photo.photo.path in valid_paths:
                        faiss_id = start_id + valid_paths.index(photo.photo.path)
                        if self.user is None:
                            photo.faiss_id_public = faiss_id
                        else:
                            photo.faiss_id = faiss_id
                        photo.save()
                        print(f"✅ Ảnh {photo.id_photo} đã được thêm vào FAISS với ID: {faiss_id}")
            except Exception as e:
                print(f"❌ Lỗi khi xử lý chunk {chunk_paths}: {e}")
        self.save_faiss_index(self.index)