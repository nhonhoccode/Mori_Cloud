import os
import time
from drf_yasg import openapi
from datetime import datetime
from django.utils import timezone
from .models import Search_history
from .faiss_search import FaissSearch
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.openapi import TYPE_STRING, TYPE_FILE
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

searcher = FaissSearch()

class BaseSearchPhotosAI(APIView):
    permission_classes = (permissions.AllowAny,)
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = []

    @swagger_auto_schema(
        operation_summary="Tìm kiếm ảnh",
        operation_description="Tìm kiếm ảnh dựa trên mô tả văn bản hoặc hình ảnh đầu vào bằng FAISS.",
        manual_parameters=[
            openapi.Parameter(
                name="mode",
                in_=openapi.IN_QUERY,
                description="Loại tìm kiếm ('text' để tìm kiếm theo văn bản, 'image' để tìm kiếm theo hình ảnh).",
                type=openapi.TYPE_STRING,
                required=False,
                default="text",
                enum=["text", "image"]
            ),
            openapi.Parameter(
                name="query",
                in_=openapi.IN_QUERY,
                description="Chuỗi văn bản mô tả ảnh (chỉ dùng khi mode=text).",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'photo',
                openapi.IN_FORM,
                description="Ảnh tải lên (chỉ dùng khi mode=image).",
                type=openapi.TYPE_FILE,
                required=False
            ),
            openapi.Parameter(
                name="k",
                in_=openapi.IN_QUERY,
                description="Số lượng ảnh cần tìm (mặc định là 5).",
                type=openapi.TYPE_INTEGER,
                required=False,
                default=5
            ),
        ]
    )
    def post(self, request):
        start_time = time.perf_counter()
        mode = request.query_params.get("mode", "text")
        user = request.user if request.user.is_authenticated else None
        k = int(request.query_params.get("k", 5))
        if mode == "text":
            start_time = time.perf_counter()
            print(f"Mode search: text")
            query = request.query_params.get("query")
            if not query:
                return Response({"error": "Thiếu query văn bản"}, status=400)
            searcher = FaissSearch(user)
            if user:
                results = searcher.search_for_user(query, mode, k)
                liked_images = [
                    {
                        **result,
                        'created_at': result['created_at'].isoformat() if isinstance(result['created_at'], datetime) else result['created_at'],
                        'updated_at': result['updated_at'].isoformat() if isinstance(result['updated_at'], datetime) else result['updated_at'],
                    }
                    for result in results if 'id_photo' in result
                ]
                Search_history.objects.create(
                    search_query=query if mode == "text" else "image_search",
                    search_type=mode,
                    user=user,
                    search_date=timezone.now(),
                    liked_images = liked_images
                )
            else:
                results = searcher.search_global(query, mode, k)

        elif mode == "image":
            print(f"Mode search: image")
            if "photo" not in request.FILES:
                return Response({"error": "Thiếu file ảnh để tìm kiếm"}, status=400)
            uploaded_photo = request.FILES["photo"]
            temp_dir = "/tmp/faiss_search"
            os.makedirs(temp_dir, exist_ok=True)
            image_path = os.path.join(temp_dir, uploaded_photo.name)

            with open(image_path, "wb") as f:
                for chunk in uploaded_photo.chunks():
                    f.write(chunk)

            searcher = FaissSearch(user)
            if user:
                results = searcher.search_for_user(image_path, mode, k)
                liked_images = [
                    {
                        **result,
                        'created_at': result['created_at'].isoformat() if isinstance(result['created_at'], datetime) else result['created_at'],
                        'updated_at': result['updated_at'].isoformat() if isinstance(result['updated_at'], datetime) else result['updated_at'],
                    }
                    for result in results if 'id_photo' in result
                ]
                Search_history.objects.create(
                    search_query=query if mode == "text" else "image_search",
                    search_type=mode,
                    user=user,
                    search_date=timezone.now(),
                    liked_images = liked_images
                )
            else:
                results = searcher.search_global(image_path, mode, k)
            os.remove(image_path)
        end_time = time.perf_counter()
        print(f"✅ Thời gian tổng search: {end_time - start_time:.5f} giây")
        return Response({"results": results})

class SearchPhotosPublicAI(BaseSearchPhotosAI):
    """API tìm kiếm ảnh công khai (chỉ tìm ảnh có `is_public=True`)"""
    permission_classes = []


class SearchPhotosForUserAI(BaseSearchPhotosAI):
    """API tìm kiếm ảnh dành cho người dùng (yêu cầu đăng nhập)"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Tìm kiếm ảnh dành cho người dùng",
        operation_description="Tìm kiếm ảnh thuộc sở hữu của người dùng (cần đăng nhập).",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                name="mode",
                in_=openapi.IN_QUERY,
                description="Loại tìm kiếm ('text' để tìm kiếm theo văn bản, 'image' để tìm kiếm theo hình ảnh).",
                type=openapi.TYPE_STRING,
                required=False,
                default="text",
                enum=["text", "image"]
            ),
            openapi.Parameter(
                name="query",
                in_=openapi.IN_QUERY,
                description="Chuỗi văn bản mô tả ảnh (chỉ dùng khi mode=text).",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'photo',
                openapi.IN_FORM,
                description="Ảnh tải lên (chỉ dùng khi mode=image).",
                type=openapi.TYPE_FILE,
                required=False
            ),
            openapi.Parameter(
                name="k",
                in_=openapi.IN_QUERY,
                description="Số lượng ảnh cần tìm (mặc định là 5).",
                type=openapi.TYPE_INTEGER,
                required=False,
                default=5
            ),
        ]
    )
    def post(self, request):
        """API tìm kiếm ảnh dành cho người dùng (chỉ ảnh thuộc sở hữu của user)"""
        return super().post(request)

class SearchPhotosCommunityForUserAI(BaseSearchPhotosAI):
    """
    API tìm kiếm ảnh cộng đồng (yêu cầu đăng nhập, tìm ảnh công khai, có lưu lịch sử)
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Tìm kiếm ảnh cộng đồng (cần đăng nhập)",
        operation_description="Tìm kiếm ảnh công khai (is_public=True), lưu lịch sử tìm kiếm cho người dùng.",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token xác thực (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                name="mode",
                in_=openapi.IN_QUERY,
                description="Loại tìm kiếm ('text' hoặc 'image')",
                type=openapi.TYPE_STRING,
                required=False,
                default="text",
                enum=["text", "image"]
            ),
            openapi.Parameter(
                name="query",
                in_=openapi.IN_QUERY,
                description="Chuỗi mô tả văn bản (khi mode=text)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'photo',
                openapi.IN_FORM,
                description="Ảnh tải lên (khi mode=image)",
                type=openapi.TYPE_FILE,
                required=False
            ),
            openapi.Parameter(
                name="k",
                in_=openapi.IN_QUERY,
                description="Số lượng ảnh cần tìm (mặc định là 5)",
                type=openapi.TYPE_INTEGER,
                required=False,
                default=5
            ),
        ]
    )
    def post(self, request):
        user = request.user
        mode = request.query_params.get("mode", "text")
        k = int(request.query_params.get("k", 5))
        start_time = time.perf_counter()

        if mode == "text":
            query = request.query_params.get("query")
            if not query:
                return Response({"error": "Thiếu query văn bản"}, status=400)

            searcher = FaissSearch()
            results = searcher.search_global(query, mode, k)

        elif mode == "image":
            if "photo" not in request.FILES:
                return Response({"error": "Thiếu file ảnh để tìm kiếm"}, status=400)

            uploaded_photo = request.FILES["photo"]
            temp_dir = "/tmp/faiss_search"
            os.makedirs(temp_dir, exist_ok=True)
            image_path = os.path.join(temp_dir, uploaded_photo.name)

            with open(image_path, "wb") as f:
                for chunk in uploaded_photo.chunks():
                    f.write(chunk)

            searcher = FaissSearch()
            results = searcher.search_global(image_path, mode, k)
            os.remove(image_path)
        else:
            return Response({"error": "Chế độ tìm kiếm không hợp lệ"}, status=400)

        # Lưu lịch sử tìm kiếm
        Search_history.objects.create(
            search_query=query if mode == "text" else "image_search",
            search_type=mode,
            user=user,
            search_date=timezone.now(),
            liked_images=[
                {
                    **result,
                    'created_at': result['created_at'].isoformat() if isinstance(result['created_at'], datetime) else result['created_at'],
                    'updated_at': result['updated_at'].isoformat() if isinstance(result['updated_at'], datetime) else result['updated_at'],
                }
                for result in results if 'id_photo' in result
            ]
        )

        end_time = time.perf_counter()
        print(f"✅ Tổng thời gian tìm kiếm: {end_time - start_time:.5f} giây")
        return Response({"results": results})
