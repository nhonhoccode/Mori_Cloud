import os
import time
import random
from .models import *
from PIL import Image
from io import BytesIO
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError

# AI
from .faiss_indexer import FaissImageIndexer
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id_user', 'email', 'name', 'is_active', 'is_staff', 'avatar','created_at', 'updated_at']
        read_only_fields = ['id_user', 'created_at', 'updated_at']
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
            'is_active': {'required': False},
            'is_staff': {'required': False},
        }
    def get_avatar(self, obj):
        avatar_instance = Avatar.objects.filter(user=obj).first()
        if avatar_instance and avatar_instance.avatar:
            return avatar_instance.avatar.url
        return None
    
    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Email already exists')
        return email

    def validate(self, data):
        if 'email' in data:
            validate_email(data['email'])
        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class UserPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields =  ['email', 'name']
        extra_kwargs = {
            'email': {'required': False},
            'name': {'required': False},
        }
    def validate_email(self, email):
        user = self.instance 
        if User.objects.exclude(id_user=user.id_user).filter(email=email).exists():
            raise serializers.ValidationError("Email đã tồn tại trong hệ thống.")
        return email
    
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

class UserPutAminSerializer(serializers.ModelSerializer):
    id_user = serializers.IntegerField(required=True)
    class Meta:
        model = User
        fields =  ['name', 'id_user', 'is_staff', 'is_superuser']
        extra_kwargs = {
            'name': {'required': False},
            'id_user': {'required': True},
            'is_staff': {'required': False},
            'is_superuser': {'required': False},
        }    
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            print("*"*100)
            print(key, value)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
class UserBulkUpdateSerializer(serializers.Serializer):
    users = UserPutAminSerializer(many=True)
    def update(self, instance, validated_data):
        updated_users = []
        try:
            with transaction.atomic():  
                for user_data in validated_data['users']:
                    try:
                        user_instance = User.objects.get(id_user=user_data['id_user'])
                    except User.DoesNotExist:
                        raise serializers.ValidationError(f"Không tìm thấy người dùng với id_user={user_data['id_user']}")
                    serializer = UserPutAminSerializer(instance=user_instance, data=user_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    updated_users.append(serializer.instance)
        except Exception as e:
            raise serializers.ValidationError(f"Đã xảy ra lỗi: {str(e)}")
        return updated_users
    
    def create(self, validated_data):
        return self.update(None, validated_data)

class PhotoSerializer(serializers.ModelSerializer):
    id_photo = serializers.IntegerField(required=True)  
    album = serializers.PrimaryKeyRelatedField(queryset=Album.objects.all(), required=False)
    id_trash = serializers.SerializerMethodField()
    class Meta:
        model = Photo
        fields = ['id_photo', 'album','name', 'location', 'caption', 'tags', 'colors', 'objects_photo', 'description', 'photo', 'is_public', 'id_trash','created_at', 'updated_at']
        extra_kwargs = {
            'name': {'required': False},
            'location': {'required': False},
            'caption': {'required': False},
            'tags': {'required': False},
            'colors': {'required': False},
            'objects_photo': {'required': False},
            'description': {'required': False},
            'photo': {'required': False},
            'album': {'required': False},
            'is_public': {'required': False},
            'created_at' : {'required': False},
            'updated_at' : {'required': False},
            'id_trash': {'required': False},
        }
    def get_id_trash(self, obj):
        trash = Trash.objects.filter(photo=obj, user=obj.album.user).exists()
        if trash:
            trash = Trash.objects.get(photo=obj, user=obj.album.user)
            return trash.id_trash
        else:
            return False

class PhotoListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data_list):
        user = self.context['request'].user
        updated_photos = []
        errors = []
        user_albums = set(Album.objects.filter(user=user).values_list("id_album", flat=True))
        photo_dict = {photo.id_photo: photo for photo in instances}
        temp = False
        for validated_data in validated_data_list:
            if not validated_data.get("album"):
                errors.append({"id_photo": validated_data.get("id_photo"), "error": "Không tìm thấy Album"})
                continue
            album_id = int(validated_data.get("album").id_album)
            photo_id = validated_data.get("id_photo")
            temp = True
            
            if not photo_id or photo_id not in photo_dict:
                errors.append({"id_photo": photo_id, "error": "Ảnh không tồn tại hoặc không thuộc quyền sở hữu."})
                continue

            if album_id and album_id not in user_albums:
                errors.append({"id_album": album_id, "error": "Album không thuộc quyền sở hữu."})
                continue

            photo = photo_dict[photo_id]

            if photo.album.user != user:
                errors.append({"id_photo": photo_id, "error": "Bạn không có quyền chỉnh sửa ảnh này."})
                continue
            if temp:
                photo.album = validated_data.get("album")
            photo.name = validated_data.get('name', photo.name)
            photo.location = validated_data.get('location', photo.location)
            photo.caption = validated_data.get('caption', photo.caption)
            photo.tags = validated_data.get('tags', photo.tags)
            photo.colors = validated_data.get('colors', photo.colors)
            photo.objects_photo = validated_data.get('objects_photo', photo.objects_photo)
            photo.description = validated_data.get('description', photo.description)
            photo.is_public = validated_data.get('is_public', photo.is_public)
            photo.updated_at = timezone.now()
            photo.save()
            updated_photos.append({
                "id": photo.id_photo,
                "album": photo.album.id_album,
                "name": photo.name,
                "location": photo.location,
                "caption": photo.caption,
                "tags": photo.tags,
                "colors": photo.colors,
                "objects_photo": photo.objects_photo,
                "description": photo.description,
                "photo": photo.photo.path,
                "is_public": photo.is_public,
                "created_at": photo.created_at,
                "updated_at": photo.updated_at,
            })
        return updated_photos, errors

class PhotoListSerializerDemo(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['name', 'location', 'caption', 'tags', 'colors', 'objects_photo', 'description', 'photo']
        extra_kwargs = {
            'name': {'required': False},
            'location': {'required': False},
            'caption': {'required': False},
            'tags': {'required': False},
            'colors': {'required': False},
            'objects_photo': {'required': False},
            'description': {'required': False},
            'photo': {'required': False},
        }

class Tese(serializers.Serializer):
    photos = PhotoListSerializerDemo(many=True)

class Test(serializers.Serializer):
    photos = PhotoListSerializerDemo(many=True, read_only=True)
    album_id = serializers.IntegerField(required=True)

class PhotoListUpdateSerializer(PhotoListSerializerDemo):
    class Meta(PhotoListSerializerDemo.Meta):
        list_serializer_class = PhotoListSerializer

class PhotoBulkUpdateSerializer(PhotoSerializer):
    class Meta(PhotoSerializer.Meta):
        list_serializer_class = PhotoListSerializer
        
class TrashSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trash
        fields = ['id_trash', 'photo']
        read_only_fields = ['id_trash']
        extra_kwargs = {
            'photo': {'required': True},
        }

class TrashPostSerializer(serializers.Serializer):
    photo = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of Trash IDs to process"
    )
    
class FavoriteSerializer(serializers.ModelSerializer):
    id_favorite = serializers.IntegerField(required=True)  
    photo = serializers.PrimaryKeyRelatedField(queryset=Photo.objects.all(), required=False)
    class Meta:
        model = Favorite
        fields = ['id_favorite',  'photo', 'note', 'created_at', 'updated_at']
        read_only_fields = ['id_favorite']
        extra_kwargs = {
            'photo': {'required': True},
            'created_at': {'required': False},
            'updated_at': {'required': False},
            'note': {'required': False},
        }

class AlbumDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ['id_album', 'title', 'description', 'user']
        read_only_fields = ['id_album']
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': False},
            'user': {'required': True},
        }
    
class CommentSerilizer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    photo = PhotoSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ['id_comment', 'user', 'photo', 'like_count', 'content', 'parent_comment', 'liked_by','created_at', 'updated_at']
        read_only_fields = ['id_comment']
        extra_kwargs = {
            'user': {'required': True},
            'photo': {'required': True},
            'like_count': {'required': False},
            'content': {'required': False},
            'parent_comment': {'required': False},
            'liked_by': {'required': False},
            'created_at': {'required': False},
            'updated_at': {'required': False},
        }

class CommentSerilizerDetail(serializers.Serializer):
    id_photo = serializers.IntegerField(required=True)
    content = serializers.CharField(required=True) 
    id_parent = serializers.IntegerField(required=False)

    def validate_id_photo(self, value):
        photo = Photo.objects.filter(id_photo=value, is_deleted=False, is_public=True).first()
        if not photo:
            raise serializers.ValidationError("Ảnh không tồn tại hoặc không công khai.")
        return value

    def validate_id_parent(self, value):
        if value:
            parent_comment = Comment.objects.filter(id_comment=value).first()
            if not parent_comment:
                raise serializers.ValidationError("Bình luận gốc không hợp lệ.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        photo = Photo.objects.get(id_photo=validated_data['id_photo'])
        parent_comment = None

        if validated_data.get('id_parent'):
            parent_comment = Comment.objects.get(id_comment=validated_data['id_parent'])
        comment = Comment.objects.create(
            user=user,
            photo=photo,
            parent_comment=parent_comment,
            content=validated_data['content']
        )
        if parent_comment:
            messageSend = f'{parent_comment.user.name} đã trả lời bình luận của bạn.'
            Notification.objects.create(
                recipient=parent_comment.user,
                sender=user,
                notif_type='reply_comment',
                photo=comment.photo,
                comment=comment,
                message=messageSend,
                created_at=timezone.now()
            )            
        messageSend = f'{user.name} đã bình luận ảnh của bạn.'
        if photo.album.user == user:
            return comment
        Notification.objects.create(
            recipient=photo.album.user,
            sender=user,
            notif_type='comment_photo',
            photo=comment.photo,
            comment=comment,
            message=messageSend,
            created_at=timezone.now()
        )
        return comment
    
class CommentPutSerilizerDetail(serializers.Serializer):
    id_comment = serializers.IntegerField(required=True)
    content = serializers.TimeField(required=True)

    def validate_id_comment(self, value):
        comment = Comment.objects.filter(id_comment=value).first()
        if not comment:
            raise serializers.ValidationError("comment không tồn tại")
        return value

    def update(self, validated_data):
        user = self.context['request'].user
        comment = Comment.objects.filter(id_comment=validated_data['id_comment'])
        if comment.user != user:
            raise serializers.ValidationError("Bạn không có quyền chỉnh sửa bình luận này")
        comment.content = validated_data['content']
        comment.updated_at = timezone.now()
        return comment

class PhotoAblumSerializer(serializers.ModelSerializer):
    comments = CommentSerilizer(many=True, read_only=True, source="comment_photo")
    avatar = serializers.SerializerMethodField()
    class Meta:
        model = Photo
        fields = ['id_photo', 'album','name', 'location', 'caption', 'tags', 'colors', 'objects_photo', 'description', 'photo', 'is_favorited','is_public', 'is_deleted', 'like_count', 'faiss_id', 'faiss_id_public','comments','avatar','created_at', 'updated_at']
        read_only_fields = ['id_photo']
        extra_kwargs = {
            'album': {'required': True},
            'name': {'required': False},
            'location': {'required': False},
            'caption': {'required': False},
            'tags': {'required': False},
            'colors': {'required': False},
            'objects_photo': {'required': False},
            'description': {'required': False},
            'photo': {'required': False},
            'is_public': {'required': False},
            'created_at': {'required': False},
            'updated_at': {'required': False},
            'is_deleted': {'required': False},
            'like_count': {'required': False},
            'is_favorited': {'required': False},
            'faiss_id': {'required': False},
            'comments': {'required': False},
            'faiss_id_public': {'required': False},
        }
    def get_avatar(self, obj):
        user = obj.album.user
        avatar_instance = Avatar.objects.filter(user=user).first()
        if avatar_instance and avatar_instance.avatar:
            return avatar_instance.avatar.url
        return None

class AlbumSerializer(serializers.ModelSerializer):
    photos = PhotoAblumSerializer(many=True, read_only=True, source='photo_album')
    count = serializers.SerializerMethodField()
    class Meta:
        model = Album
        fields = ['id_album', 'title', 'description', 'user', 'count','photos', 'created_at', 'updated_at']
        read_only_fields = ['id_album']
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': False},
            'user': {'required': True},
            'count': {'required': False},
            'photos': {'required': False},
            'id_album': {'required': False},
            'created_at': {'required': False},
            'updated_at': {'required': False},
        }

    def validate_title(self, title):
        if len(title) < 2:
            raise ValidationError('Title must be at least 2 characters long')
        return title
    
    def get_count(self, obj):
        album_id = obj.id_album
        photos = Photo.objects.filter(album=album_id, is_deleted=False)
        return photos.count()

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id_user', 'name', 'email', 'password']
        read_only_fields = ['id_user']
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
            'password': {'write_only': True},
        }
    
    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email already exists')
        return email
    
    def validate_name(self, name):
        if len(name) < 2:
            raise ValidationError('Name must be at least 2 characters long')
        return name
    
    def validate_password(self, password):
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        return password

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
        
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

class SearchHistorySerializerCustom(serializers.ModelSerializer):
    class Meta:
        model = Search_history
        fields = ['id_search_history', 'search_query', 'search_type', 'search_date']

class TrashListSerializer(serializers.Serializer):
    photo = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    def validate(self, data):
        photos = data["photo"]
        user = self.context['request'].user 
        valid_photos = []
        for photo_id in photos:
            try:
                photo_obj = Photo.objects.get(id_photo=photo_id)
                if photo_obj.album.user == user and not photo_obj.is_deleted:
                    valid_photos.append(photo_obj)
            except ObjectDoesNotExist:
                pass 

        if not valid_photos:
            raise serializers.ValidationError({"photos": "No valid photos found."})
        return {"photo": valid_photos}

    def create(self, validated_data):
        photos = validated_data['photo']
        for photo in photos:
            photo.is_deleted = True
            photo.save()
            Trash.objects.create(photo=photo)
        return {"photos": [photo.id_photo for photo in photos]}

class PhotoListSerializer(serializers.Serializer):
    id_photo = serializers.IntegerField(required=True)
    note = serializers.CharField(required=False, allow_blank=True)

class AddFavoriteSerializer(serializers.Serializer):
    photos = serializers.ListSerializer(
        child=PhotoListSerializer() 
    )

    def validate(self, data):
        user = self.context['request'].user
        photos = data['photos']

        valid_photos = []
        invalid_photos = []
        already_favorite = []

        for item in photos:
            try:
                photo = Photo.objects.filter(id_photo=item['id_photo'], is_deleted=False, album__user=user).exists()
                if photo:
                    photo = Photo.objects.get(id_photo=item['id_photo'], is_deleted=False, album__user=user)
                    if Favorite.objects.filter(photo=photo).exists():
                        already_favorite.append(item['id_photo'])
                    else:
                        valid_photos.append({photo: item.get('note', '')})
                else:
                    invalid_photos.append(item['id_photo'])
            except Photo.DoesNotExist:
                invalid_photos.append(item['id_photo'])

        data['completed'] = valid_photos
        data['invalid_photos'] = invalid_photos
        data['already_favorite'] = already_favorite
        return data

    def create(self, validated_data):
        photos = validated_data['completed']
        favorites = []
        for photo_dict in photos:
            photo = list(photo_dict.keys())[0]
            note = photo_dict[photo]
            photo.is_favorited = True
            photo.save()
            favorites.append(Favorite.objects.create(photo=photo, note=note))
        return favorites, validated_data['invalid_photos'], validated_data['already_favorite']
    
class RemoveFavoriteSerializer(serializers.Serializer):
    id_photos = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    def validate(self, data):
        user = self.context['request'].user
        id_photos = data['id_photos']
        invalid_photos = []
        already_favorite = []
        for id_photo in id_photos:
            try:
                photo = Photo.objects.get(id_photo=id_photo, is_favorited=True, is_deleted=False)
                if photo.album.user != user:
                    invalid_photos.append(id_photo)
                    continue
                if photo.is_deleted:
                    invalid_photos.append(id_photo)
                    continue
            except Photo.DoesNotExist:
                invalid_photos.append(id_photo)
        data['invalid_photos'] = invalid_photos
        data['already_favorite'] = already_favorite
        return data
    
    def deletes_favorite(self, instances, validated_data):
        photo_dict = {photo.id_photo: photo for photo in instances}
        id_remove_sucess = []
        invalid_photos = []
        for item in validated_data:
            if item in photo_dict:
                photo = photo_dict[item]
                favorie = Favorite.objects.get(photo=photo)
                favorie.delete()
                photo.is_favorited = False
                id_remove_sucess.append(photo.id_photo)
            else:
                invalid_photos.append(item)
        return id_remove_sucess, invalid_photos
    
class AlbumListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data_list):
        user = self.context['request'].user
        
        updated_albums = []
        errors = []
        album_dict = {album.id_album : album for album in instances}
        
        for validated_data in validated_data_list:
            album_id = validated_data.get("id_album")

            if not album_id or album_id not in album_dict:
                errors.append({'id_album': album_id, 'error': "Album không tồn tại hoặc không thuộc quyên sở hữu"})
                continue
            album = album_dict[album_id]
            if album.user != user:
                errors.append({'id_album': album_id, 'error': "Album không thuộc quyên sở hữu cua user hiên tại"})
                continue
            
            album.title = validated_data.get('title', album.title)
            album.description = validated_data.get('description', album.description)
            album.updated_at = timezone.now()
            album.save()
            updated_albums.append({
                'id': album.id_album,
                'title': album.title,
                'description': album.description,
                'user': album.user.id_user,
                'created_at': album.created_at,
                'updated_at': album.updated_at
            })
        return {
            'updated_albums': updated_albums,
            'errors': errors
        }

class AlbumCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ['id_album', 'title', 'description']
        read_only_fields = ['id_album']
        extra_kwargs = {
            'title': {'required': False},
            'description': {'required': False},
            'id_album': {'required': False},
        }

    def create(self, validated_data):
        user = self.context['request'].user

        if isinstance(validated_data, list):
            albums = [Album(user=user, **album_data) for album_data in validated_data]
            return Album.objects.bulk_create(albums)

        validated_data["user"] = user
        return Album.objects.create(**validated_data)
        
class AlbumUpdateSerializer(serializers.ModelSerializer):
    id_album = serializers.IntegerField(required=False)
    class Meta:
        model = Album
        fields = ['id_album', 'title', 'description']
        read_only_fields = ['id_album']
        extra_kwargs = {
            'title': {'required': False},
            'description': {'required': False},
            'id_album': {'required': False},
        }
    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance
    
class AlbumBulkUpdateSerializer(AlbumUpdateSerializer):
    class Meta(AlbumUpdateSerializer.Meta):
        list_serializer_class = AlbumListSerializer

class TrashActionSerializer(serializers.Serializer):
    photo_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of photo id to process"
    )

    def validate_trash_ids(self, photo_ids):
        if not all(isinstance(photo_id, int) for photo_id in photo_ids):
            raise serializers.ValidationError("All trash_ids must be integers.")
        return photo_ids

    def is_photo_in_trash(self, photo_id, user):
        return Trash.objects.filter(user=user,photo__id_photo=photo_id).exists()

    def restore_photos(self, request):
        """Khôi phục ảnh từ Trash"""
        photo_ids = self.validated_data.get('photo_ids', [])
        restored_photos = []
        errors = []
        user = request.user

        for photo_id in photo_ids:
            photo = Photo.objects.filter(id_photo=photo_id, is_deleted=True, album__user=user).exists()
            if not photo:
                errors.append({'photo_id': photo_id, 'error': 'Photo not found or not deleted'})
                continue
            try:
                trash = Trash.objects.get(user=user, photo__id_photo=photo_id)
            except Trash.DoesNotExist:
                errors.append({'photo_id': photo_id, 'error': 'Photo not found in Trash'})
                continue
            photos = Photo.objects.filter(id_photo=photo_id)
            for photo in photos:
                if not photo.is_deleted:
                    errors.append({'photo_id': photo.id_photo, 'error': 'Photo is not deleted'})
                    continue
                if photo.album.user != user:
                    errors.append({'photo_id': photo.id_photo, 'error': 'You do not have permission to restore this photo'})
                    continue
                restored_photos.append(photo)
                photo.is_deleted = False
                photo.updated_at = timezone.now()
                trash = Trash.objects.get(user=user, photo__id_photo=photo_id)
                trash.delete()
                photo.save()
        return restored_photos, errors

    def delete_photos_permanently(self, request):
        """xoa anh vinh vien từ Trash"""
        photo_ids = self.validated_data.get('photo_ids', [])
        deleted_photos = []
        errors = []
        user = request.user

        for photo_id in photo_ids:
            photo = Photo.objects.filter(id_photo=photo_id, is_deleted=True, album__user=user).exists()
            if not photo:
                errors.append({'photo_id': photo_id, 'error': 'Photo not found or not deleted'})
                continue
            try:
                trash = Trash.objects.filter(user=user, photo__id_photo=photo_id).exists()
            except Trash.DoesNotExist:
                errors.append({'photo_id': photo_id, 'error': 'Photo not found in Trash'})
                continue
            if photo and trash:
                trash = Trash.objects.get(user=user, photo__id_photo=photo_id)
                photo = trash.photo
                file_path = photo.photo.path
                if os.path.exists(file_path):
                    os.remove(file_path)
                deleted_photos.append(photo_id)
                trash.delete()
                photo.delete()
        return deleted_photos, errors

class ExampleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()

class ExampleloginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100)

class FromLogin(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class FormSearch(serializers.Serializer):
    search_text = serializers.CharField()

class ListForm(serializers.Serializer):
    photos = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of Photo IDs to process"
    )

class ListAlbumsForm(serializers.Serializer):
    albums = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of Albums IDs to process"
    )

class UserForm(serializers.Serializer):
    id_users = serializers.ListField(
        child=serializers.IntegerField(),   
        allow_empty=False,
        help_text="List of User IDs to process"
    )
    def perform_delete(self):
        request_user = self.context['request'].user
        deleted_ids = []
        with transaction.atomic():
            for user_id in self.validated_data['id_users']:
                user = User.objects.get(id_user=user_id)
                if user == request_user:
                    raise serializers.ValidationError("Bạn không thể xóa tải khoản quản trị viên")
                if user != request_user:
                    user.delete()
                    deleted_ids.append(user_id)
        return deleted_ids

class UserItemForm(serializers.Serializer):
    id_user = serializers.IntegerField(
        help_text="List of User IDs to process"
    )

class UpdateFavoriteSerializer(serializers.ModelSerializer):
    note = serializers.CharField(required=True, max_length=500)
    class Meta:
        model = Favorite
        fields = ["note"]
    def update(self, instance, validated_data):
        instance.note = validated_data.get("note", instance.note)
        instance.updated_at = timezone.now()
        photo = instance.photo
        photo.is_favorited = True
        photo.save()
        instance.save()
        return instance
    

class UserSeachInfo(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    class Meta:
        model= User
        fields = ['id_user', 'name', 'email', 'avatar']
        read_only_fields = ['id_user']
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
            'avatar': {'required': False}
        }

    def get_avatar(self, obj):
        avatar_instance = Avatar.objects.filter(user=obj).first()
        if avatar_instance and avatar_instance.avatar:
            return avatar_instance.avatar.url
        return None

class PhotoCommunitySerializer(serializers.ModelSerializer):
    user = UserSeachInfo(read_only=True, source='album.user')
    photo = serializers.SerializerMethodField()
    comments = CommentSerilizer(many=True, read_only=True, source="comment_photo")
    class Meta:
        model = Photo
        fields = ['id_photo', 'name', 'location', 'caption', 'tags', 
                  'colors', 'objects_photo', 'description',  'like_count', 'photo', 'user', 'comments','created_at','updated_at']
        extra_kwargs = {
            'name': {'required': False},
            'location': {'required': False},
            'caption': {'required': False},
            'tags': {'required': False},
            'colors': {'required': False},
            'objects_photo': {'required': False},
            'description': {'required': False},
            'user': {'required': False},
            'like_count': {'required': False},
            'created_at': {'required': False},
            'updated_at': {'required': False},
        }
    def get_photo(self, obj):
        return obj.photo.url
    
class PhotoInviCommunitySerializer(serializers.ModelSerializer):
    user = UserSeachInfo(read_only=True, source='album.user')
    photo = serializers.SerializerMethodField()
    comments = CommentSerilizer(many=True, read_only=True, source="comment_photo")
    album_title = serializers.CharField(source='album.title', read_only=True)
    album_description = serializers.CharField(source='album.description', read_only=True)
    album_is_main = serializers.BooleanField(source='album.is_main', read_only=True)
    class Meta:
        model = Photo
        fields = ['id_photo', 'name', 'location', 'caption', 'tags', 
                  'colors', 'objects_photo', 'description',  'like_count', 'photo', 'user', 'album', 'album_title', 'album_description', 'album_is_main', 'comments','created_at','updated_at']
    def get_photo(self, obj):
        return obj.photo.url
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if self.context.get("hide_album_info", False):
            rep.pop('album', None)
            rep.pop('album_title', None)
            rep.pop('album_description', None)
            rep.pop('album_is_main', None)
        return rep
    
class SearchHistorySerializer(serializers.ModelSerializer):
    user = UserSeachInfo(read_only=True)

    class Meta:
        model = Search_history
        fields = ['id_search_history', 'search_query', 'search_type', 'user', 'search_date', 'liked_images']
        read_only_fields = ['id_search_history']
        extra_kwargs = {
            'search_query': {'required': True},
            'search_type': {'required': False},
            'user': {'required': False},
            'search_date': {'required': False},
            'liked_images': {'required': False},
        }
    
    def create(self, validated_data):
        user = self.context['request'].user
        search_history = Search_history.objects.create(**validated_data, user = user)
        return search_history
    

class SearchHistoryDetailSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = Search_history
        fields = ['id_search_history', 'search_query', 'search_type', 'user', 'search_date', 'liked_images']
        read_only_fields = ['id_search_history']
        extra_kwargs = {
            'search_query': {'required': True},
            'search_type': {'required': False},
            'user': {'required': True},
            'search_date': {'required': False},
            'liked_images': {'required': False},
        }

    def validate_user(self, user):
        if not User.objects.filter(id=user.id).exists():
            raise ValidationError('User does not exist')
        return user
    
    def update(self, instance, validated_data):
        instance.search_query = validated_data.get('search_query', instance.search_query)
        instance.search_type = validated_data.get('search_type', instance.search_type)
        instance.user = validated_data.get('user', instance.user)
        instance.save()
        return instance
    
class SearchPostRatingSerializer(serializers.Serializer):
    search_history = serializers.IntegerField(required=True)
    photos = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of Photo IDs to process"
    )
    rating = serializers.IntegerField(min_value=1, max_value=5, required=True)
    feedback = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        user = self.context['request'].user
        search_history = Search_history.objects.filter(id_search_history=data['search_history']).first()
        
        if not search_history:
            raise serializers.ValidationError({'search_history': 'Search history does not exist'})
        if search_history.user != user:
            raise serializers.ValidationError({'search_history': 'Search history does not belong to the user'})
        invalid_photos = []
        valid_photos = []
        for photo in data['photos']:
            if Photo.objects.filter(id_photo=photo, album__user=user, is_deleted=False).exists():
                valid_photos.append(photo)
            else:
                invalid_photos.append(photo)
        data['photos'] = valid_photos
        data['invalid_photos'] = invalid_photos
        return data
    
class UserSerializerForUserPublic(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id_user', 'name', 'email', 'avatar']
        read_only_fields = ['id_user']
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
            'avatar': {'required': False},
        }
    def get_avatar(self, obj):
        avatar_instance = Avatar.objects.filter(user=obj).first()
        if avatar_instance and avatar_instance.avatar:
            return avatar_instance.avatar.url
        return None

class PhotoDynamicUserSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializerForUserPublic(source="album.user", read_only=True)  
    liked = serializers.SerializerMethodField()
    photo_path = serializers.SerializerMethodField()
    class Meta:
        model = Photo
        fields = ['id_photo', 'name', 'location', 'caption', 'tags', 'colors', 'like_count', 'objects_photo', 'description', 'is_public', 'is_favorited', 'liked','uploaded_by', 'photo_path', 'created_at', 'updated_at']
    
    def get_photo_path(self, obj):
        return obj.photo.url
    
    def get_liked(self, obj):
        like = Like.objects.filter(photo = obj, user=self.context['request'].user)
        if like:
            return True
        return False
    
class RandomPhotoUserListSerializer(serializers.Serializer):
    PAGE_SIZE = 15
    CACHE_TIMEOUT = 300
    photos = serializers.SerializerMethodField()

    def get_obj(self, obj):
        request = self.context.get('request')
        user = request.user
        previous_photos = cache.get(f"user_{user.id_user}_last_photos", [])
        photos = Photo.objects.filter(is_public=True, is_deleted=False).exclude(id_photo__in=previous_photos)
        if photos.exists():
            cache.delete(f"user_{user.id_user}_last_photos")
            photo_list = list(photos)

            random.shuffle(photo_list)
            selected_photos = photo_list[:self.PAGE_SIZE]
            selected_photo_ids = [photo.id_photo for photo in selected_photos]

            cache.set(f"user_{user.id_user}_last_photos", selected_photo_ids, self.CACHE_TIMEOUT)
            liked_photo_ids = set(Like.objects.filter(user=user).values_list('photo__id_photo', flat=True))
            serialized_photos = PhotoDynamicUserSerializer(
                selected_photos, many=True, context={'request': request, 'liked_photos': liked_photo_ids}
            )
            return serialized_photos.data
        else:
            return []
        
class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = ['id_avatar', 'user',  'updated_at', 'avatar']
        read_only_fields = ['id_avatar']
        extra_kwargs = {
            'user': {'required': True},
            'updated_at': {'required': False},
            'avatar': {'required': False},
        }

    def create(self, validated_data):
        user = validated_data['user']
        avatar = validated_data['avatar']
        return Avatar.objects.create(user=user, avatar=avatar)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance
    
class AvatarPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = ['id_avatar', 'user', 'avatar', 'updated_at'] 
        read_only_fields = ['id_avatar']
        extra_kwargs = {
            'user': {'read_only': True},
            'updated_at': {'required': False},
            'avatar': {'required': True},
            }
    def update(self, instance, validated_data):
        new_avatar = validated_data.get('avatar', None)
        instance.avatar = new_avatar
        instance.updated_at = timezone.now()
        instance.save()
        return instance

class PhotoUploadSerializer(serializers.Serializer):
    photos = serializers.ListField(
        child=serializers.ImageField(), 
        required=True
    )

    def validate_photos(self, photos):
        """Kiểm tra từng file có phải là ảnh hợp lệ không"""
        for photo in photos:
            try:
                img = Image.open(BytesIO(photo.read()))  
                img.verify()
                photo.seek(0) 
            except Exception:
                raise serializers.ValidationError(f"❌ Tập tin `{photo.name}` không phải là ảnh hợp lệ.")
        return photos

    def create(self, validated_data):
        photos = validated_data['photos']
        user = self.context['request'].user
        start_time = time.perf_counter()
        indexer = FaissImageIndexer(user=user)
        global_indexer = FaissImageIndexer(user=None)

        album = Album.objects.filter(is_main=True, user=user).first()
        list_photos = []
        
        for item in photos:
            photo = Photo.objects.create(album=album, photo=item)
            success_id = indexer.add_photo_to_faiss(photo)
            global_faiss_id = global_indexer.add_photo_to_faiss(photo)
            print(f"global_faiss_id: {global_faiss_id}")
            print(f"success_id for user: {success_id}")
            print(f"✅ Thêm ảnh {photo.id_photo} vào Faiss thành công")
            photo.save()
            list_photos.append(photo)
        end_time = time.perf_counter()
        print(f"✅ Thời gian model xử lý thêm ảnh: {end_time - start_time:.5f} giây")
        return list_photos

class PhotoUploadSerializertt(serializers.Serializer):
    photo = serializers.ImageField() 
    id = serializers.IntegerField()

    def validate_photos(self, photo):
        """Kiểm tra từng file có phải là ảnh hợp lệ không"""
        try:
            img = Image.open(BytesIO(photo.read()))  
            img.verify()
            photo.seek(0) 
        except Exception:
            raise serializers.ValidationError(f"❌ Tập tin `{photo.name}` không phải là ảnh hợp lệ.")
        return photo

    def create(self, validated_data):
        photo = validated_data['photo']
        user = self.context['request'].user
        id_photo = validated_data['id']
        album = Album.objects.filter(is_main=True, user=user).first()
        photo_db = Photo.objects.filter(album__user=user, id_photo=id_photo, album=album).first()
        if photo_db:
            file_path = photo_db.photo.path
            if os.path.exists(file_path):
                os.remove(file_path)
            photo_db.photo = photo
            photo_db.updated_at = timezone.now()
            photo_db.save()
            return PhotoSerializer(photo_db).data
        else:
            raise serializers.ValidationError(f"❌ Không tìm thấy ảnh hợp lệ, thao tác thất bại")

class FavoriteListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data_list):
        user = self.context['request'].user
        updated_favorites = []
        errors = []
        favorite_dict = {favorite.id_favorite: favorite for favorite in instances}
        for validated_data in validated_data_list:
            favorite_id = validated_data.get("id_favorite")
            if not favorite_id or favorite_id not in favorite_dict:
                errors.append({"id_favorite": favorite_id, "error": "Favorite không tồn tại hoặc không thuộc quyền sở hữu."})
                continue
            favorite = favorite_dict[favorite_id]
            if favorite.photo.album.user != user:
                errors.append({"id_favorite": favorite_id, "error": "Bạn không có quyền chỉnh sửa favorite này."})
                continue
            favorite.note = validated_data.get('note', favorite.note)
            favorite.updated_at = timezone.now()
            favorite.save()
            updated_favorites.append({
                "id": favorite.id_favorite,
                "photo": favorite.photo.id_photo,
                "note": favorite.note,
                "created_at": favorite.created_at,
                "updated_at": favorite.updated_at
            })
        return updated_favorites, errors

class FavoriteListUpdateSerializer(FavoriteSerializer):
    class Meta(FavoriteSerializer.Meta):
        list_serializer_class = FavoriteListSerializer

class UserSerializerPublic(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id_user', 'name', 'email', 'avatar']
        read_only_fields = ['id_user']
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
            'avatar': {'required': False},
        }

    def get_avatar(self, obj):
        avatar_instance = Avatar.objects.filter(user=obj).first()
        if avatar_instance and avatar_instance.avatar:
            return avatar_instance.avatar.url
        return None

class PhotoDynamicSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializerPublic(source="album.user", read_only=True) 
    photo_path = serializers.SerializerMethodField()
    comments = CommentSerilizer(many=True, read_only=True, source="comment_photo")
    class Meta:
        model = Photo
        fields = ['id_photo', 'name', 'location', 'caption', 'tags', 'colors', 'like_count', 'objects_photo', 'description', 'like_count', 'is_public', 'uploaded_by', 'photo_path', 'comments', 'created_at', 'updated_at']   
    def get_photo_path(self, obj):
        return obj.photo.url

class RandomPhotoListSerializer(serializers.Serializer):
    PAGE_SIZE = 15
    CACHE_TIMEOUT = 300

    photos = serializers.SerializerMethodField()

    def get_obj(self, obj):
        request = self.context.get('request')
        cache_key = "anonymous_last_photos"
        previous_photos = cache.get(cache_key, [])
        photos = Photo.objects.filter(is_public=True, is_deleted=False).exclude(id_photo__in=previous_photos)

        if not photos.exists():
            cache.delete(cache_key)
            previous_photos = []
            photos = Photo.objects.filter(is_public=True, is_deleted=False)

        if not photos.exists():
            return []

        photo_list = list(photos)
        random.shuffle(photo_list)
        selected_photos = photo_list[:self.PAGE_SIZE]
        selected_photo_ids = [photo.id_photo for photo in selected_photos]

        cache.set(cache_key, previous_photos + selected_photo_ids, self.CACHE_TIMEOUT)
        serialized_photos = PhotoDynamicSerializer(
            selected_photos, many=True, context={'request': request}
        )
        return serialized_photos.data

class FavoriteListSerializer(serializers.Serializer):
    id_favorite = serializers.IntegerField()
    note = serializers.CharField()

class TrashSeriizer(serializers.ModelSerializer):
    class Meta:
        model = Trash
        fields = ['id_trash',  'user', 'photo', 'deleted_at','created_at', 'deleted_at']

class PhotoDynamicNotiSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializerPublic(source="album.user", read_only=True) 
    photo_path = serializers.SerializerMethodField()
    class Meta:
        model = Photo
        fields = ['id_photo', 'name', 'location', 'caption', 'tags', 'colors', 'like_count', 'objects_photo', 'description', 'is_public', 'uploaded_by', 'photo_path', 'created_at', 'updated_at']   
    def get_photo_path(self, obj):
        return obj.photo.url
class CommentNotiSerilizer(serializers.ModelSerializer):
    user = UserSerializerPublic(read_only=True)
    class Meta:
        model = Comment
        fields = ['id_comment', 'user', 'photo',  'content', 'parent_comment','created_at', 'updated_at']
        read_only_fields = ['id_comment']
        extra_kwargs = {
            'user': {'required': True},
            'photo': {'required': True},
            'like_count': {'required': False},
            'content': {'required': False},
            'parent_comment': {'required': False},
            'created_at': {'required': False},
            'updated_at': {'required': False},
        }

class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializerPublic(read_only=True)
    sender = UserSerializerPublic(read_only=True)
    photo = PhotoDynamicNotiSerializer(read_only=True)
    comment = CommentNotiSerilizer(read_only=True)
    class Meta:
        model = Notification
        fields = ['id_notification', 'recipient', 'sender', 'notif_type', 'photo', 'comment', 'message', 'created_at']
        read_only_fields = ['id_notification']
        extra_kwargs = {
            'recipient': {'required': True},
            'sender': {'required': True},
            'notif_type': {'required': True},
            'photo': {'required': False},
            'comment': {'required': False},
            'message': {'required': False},
            'created_at': {'required': False},
        }
    
class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializerPublic(read_only=True)
    photo = PhotoDynamicNotiSerializer(read_only=True)
    class Meta:
        model = Like
        fields = ['id_like', 'user', 'photo', 'created_at', 'updated_at']
        read_only_fields = ['id_like']
        extra_kwargs = {
            'user': {'required': False},
            'created_at': {'required': False},
            'updated_at': {'required': False},
            'photo': {'required': False},
        }

class LikeCommentSerializer(serializers.ModelSerializer):
    is_liked = serializers.SerializerMethodField()
    parent_comment = CommentNotiSerilizer(read_only=True)
    user_comment = serializers.SerializerMethodField()
    liked_by = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = ['id_comment', 'user_comment', 'parent_comment','like_count', 'liked_by', 'is_liked']

    def get_is_liked(self, obj):
        user = self.context['request'].user
        return obj.is_liked_by_user(user)
    
    def get_user_comment(self, obj):
        user = obj.user
        return UserSerializerPublic(user).data if user else None
    
    def get_liked_by(self, obj):
        liked_by = []
        for user in obj.liked_by:
            print(user)
            try:
                user_like = User.objects.filter(id_user=int(user)).exists()
                if not user_like:
                    continue
                liked_by.append(UserSerializerPublic(User.objects.filter(id_user=int(user)).first()).data)
            except User.DoesNotExist:
                continue
        return liked_by
    
class UserAdminSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id_user', 'name', 'email', 'avatar']
        read_only_fields = ['id_user']
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
            'avatar': {'required': False}
        }

    def get_avatar(self, obj):
        avatar_instance = Avatar.objects.filter(user=obj).first()
        if avatar_instance and avatar_instance.avatar:
            return avatar_instance.avatar.url
        return None
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError("Mật khẩu cũ không đúng")
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Mật khẩu mới và xác nhận mật khẩu không khớp")
        return data
    
    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
