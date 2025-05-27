from django.utils import timezone
from rest_framework import serializers
from .models import *

class PhotoListAdminSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data_list):
        updated_photos = []
        photo_dict = {photo.id_photo: photo for photo in instances}
        for validated_data in validated_data_list:
            photo_id = validated_data.get("id_photo")
            if not photo_id or photo_id not in photo_dict:
                continue
            photo = photo_dict[photo_id]
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
        return updated_photos

class PhotoAdminSerializer(serializers.ModelSerializer):
    id_photo = serializers.IntegerField(required=True)  
    class Meta:
        model = Photo
        fields = ['id_photo', 'name', 'location', 'caption', 'tags', 'colors', 'objects_photo', 'description', 'photo', 'is_public', 'created_at', 'updated_at']
        extra_kwargs = {
            'name': {'required': False},
            'location': {'required': False},
            'caption': {'required': False},
            'tags': {'required': False},
            'colors': {'required': False},
            'objects_photo': {'required': False},
            'description': {'required': False},
            'photo': {'required': False},
            'is_public': {'required': False},
            'created_at' : {'required': False},
            'updated_at' : {'required': False},
        }

class PhotoBulkUpdateAdminSerializer(PhotoAdminSerializer):
    class Meta(PhotoAdminSerializer.Meta):
        list_serializer_class = PhotoListAdminSerializer

class PhotoFilterSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(required=False)
    end_time = serializers.DateTimeField(required=False)

    def get_photos(self):
        user = self.context['request'].user
        if not user.is_superuser:
            raise serializers.ValidationError("Bạn không có quyền truy cập")
        start_time = self.validated_data.get(
            'start_time',
            timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_time = self.validated_data.get(
            'end_time',
            timezone.now()
        )
        photos = Photo.objects.filter(
            is_public=True,
            updated_at__range=(start_time, end_time)
        )
        count = photos.count()
        return photos, count

class ChangePasswordAdminSerializer(serializers.Serializer):
    id_user = serializers.IntegerField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_id_user(self, id_user):
        if not User.objects.filter(id_user=id_user).exists():
            raise serializers.ValidationError("Người dùng không tồn tại.")
        if User.objects.filter(id_user=id_user).first().is_superuser:
            raise serializers.ValidationError("Không thể thay đổi mật khẩu của người dùng quản trị.")
        return id_user  

    def save(self, **kwargs):
        id_user = self.validated_data['id_user']
        new_password = self.validated_data['new_password']
        user = User.objects.get(id_user=id_user)
        user.set_password(new_password)
        user.save()
        return user
    