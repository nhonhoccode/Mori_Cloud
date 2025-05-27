import os
import logging
from .models import *
from .serializers import *
from drf_yasg import openapi
from datetime import datetime
from django.http import Http404
from knox.models import AuthToken
from rest_framework.views import APIView
from drf_yasg.views import get_schema_view
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from knox.views import LoginView as KnoxLoginView 
from drf_yasg.openapi import TYPE_STRING, TYPE_ARRAY
from django.contrib.auth import get_user_model, login
from rest_framework.decorators import permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.serializers import AuthTokenSerializer

logger = logging.getLogger(__name__)
User = get_user_model()
schema_view = get_schema_view(
   openapi.Info(
      title="Your API",
      default_version='v1',
      description="Description of your API",
      terms_of_service="https://www.example.com/policies/terms/",
      contact=openapi.Contact(email="contact@example.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

class GetUserView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Retrieve user details using an Authorization token",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: UserSerializer, 401: "Unauthorized"}
    )
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=200)

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404("User không tồn tại.")

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Xóa tải khoản",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token cho xác thực (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        request_body=UserItemForm
    )
    def delete(self, request, format=None):
        user = self.get_object(request.data['id_user'])
        if user:
            user.delete()
            result = {
                'status': 'success',
                'Deleted user':request.data['id_user']
            }
            return Response(result ,status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "Xóa tài khoản không thành công"}, status=status.HTTP_404_NOT_FOUND)
class GetUserInfoView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=UserPutSerializer, 
        responses={
            201: openapi.Response(description="Created successfully", schema=PhotoSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, data= request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)
    @swagger_auto_schema(
        operation_description="Info about the login",
        request_body=ExampleloginSerializer,
        responses={
            201: openapi.Response(description="Login successfully", schema=ExampleloginSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def post(self, request, *args, **kwargs):
        if User.objects.filter(email=request.data['username']).exists():
            data = User.objects.get(email=request.data['username'])
            
            if data.is_email:
                return Response({"error": "Tài khoản này chỉ đăng nhập bằng google."}, status=status.HTTP_400_BAD_REQUEST)
            serializer = AuthTokenSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']

            login(request, user)
            _, token = AuthToken.objects.create(user)
            data = {
                "message": "Đăng nhập thành công!",
                "token": token
            }
            print("đăng nhập thành công thong qua gmail")
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Tài khoản không tồn tại."}, status=status.HTTP_400_BAD_REQUEST)

class UserRegistrationView(APIView):
    permission_classes = (permissions.AllowAny,)
    @swagger_auto_schema(
        operation_description="Info about the login",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(description="Register successfully", schema=ExampleSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if AuthToken.objects.filter(user=user).exists():
                AuthToken.objects.filter(user=user).delete()

            _, token = AuthToken.objects.create(user)
            request.session['token'] = token
            data = {
                "user": UserSerializer(user).data,
                "token": token
            }
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PhotoPublicUserView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(description="Created successfully", schema=PhotoSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def get(self, request):
        user = request.user
        photos = Photo.objects.filter(album__user=user, is_deleted=False, is_public=True)
        serializer = PhotoAblumSerializer(photos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class PhotoView(APIView):   
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(description="Created successfully", schema=PhotoSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )

    def get(self, request):
        user = request.user
        photos = Photo.objects.filter(album__user=user, is_deleted=False)
        serializer = PhotoAblumSerializer(photos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    @swagger_auto_schema(
        operation_description="Put avatar cho người dùng",
        manual_parameters=[
            openapi.Parameter(
                'photos', openapi.IN_FORM, type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_FILE),
                description="Danh sách ảnh tải lên",
                example="file image: png/jpg"
            ),
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        request_body=None,
        responses={201: openapi.Response('Thành công', PhotoUploadSerializer)}
    )
    def post(self, request):
        """Xử lý tạo album và upload nhiều ảnh"""
        serializer = PhotoUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            response_data = serializer.create(serializer.validated_data) 

            result = PhotoAblumSerializer(response_data, many=True)
            return Response(result.data,
                             status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_object(self, pk, user):
        try:
            photo = Photo.objects.get(pk=pk)
            if photo.album.user != user:
                return "not_owned"  
            if photo.is_deleted:
                return "already_deleted"  
            return photo  
        except Photo.DoesNotExist:
            return None  

class AlbumView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(description="Created successfully", schema=AlbumSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )

    def get(self, request):
        user = request.user
        album = Album.objects.filter(user=user)
        serializer = AlbumSerializer(album, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=AlbumCreateSerializer(many=True),
        responses={
            201: openapi.Response(description="Created successfully", schema=ExampleSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = AlbumCreateSerializer(data=request.data, context={'request': request}, many=True)
        if serializer.is_valid():
            albums = serializer.save()
            return Response(
                {
                    "albums": [
                        {
                            "id": album.id_album,
                            "title": album.title,
                            "description": album.description,
                            "user_id": album.user.id_user,
                            "created_at": album.created_at,
                            "updated_at": album.updated_at
                        }
                        for album in albums
                    ]
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_object(self, pk, user):
        try:
            album = Album.objects.get(pk=pk)
            if album.user != user:
                raise Http404("Album không thuộc user sở hữu")
            return album
        except Album.DoesNotExist:
            raise Http404("Album không tồn tại hoặc đã bị xóa.")

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=ListAlbumsForm,
    )
    def delete(self, request, format=None):
        user = request.user
        deleted_albums = []
        not_found_albums = []
        for pk in request.data['albums']:
            try:
                album = self.get_object(pk, user)
                if album:
                    if album.is_main:
                        return Response({"error": "Không thể xóa album chính."}, status=status.HTTP_400_BAD_REQUEST)
                    photos = Photo.objects.filter(album=album)
                    for photo in photos:
                        photo.album = Album.objects.get(user=user, is_main=True)
                        photo.save()
                    album.delete()
                    deleted_albums.append(pk)
                else:
                    not_found_albums.append(pk)
            except Http404 as e:
                not_found_albums.append(pk)
                pass
        return Response({'Deleted album':deleted_albums, 'Not found albums':not_found_albums},status=status.HTTP_200_OK)
    
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Update alum (titl, description) của user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=AlbumUpdateSerializer(many=True),
        responses={
            200: openapi.Response(description="Cập nhật thành công", schema=AlbumUpdateSerializer),
            404: openapi.Response(description="Album không tồn tại"),
            400: openapi.Response(description="Dữ liệu không hợp lệ"),
        },
    )
    def put(self, request, *args, **kwargs):
        if not isinstance(request.data, list):
            return Response({"error": "Dữ liệu phải là danh sách JSON."}, status=status.HTTP_400_BAD_REQUEST)

        album_ids = [data.get("id_album") for data in request.data if "id_album" in data]
        albums = Album.objects.filter(id_album__in=album_ids, user=request.user)  

        if not albums.exists():
            return Response({"error": "Không tìm thấy album nào hợp lệ để cập nhật."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AlbumBulkUpdateSerializer(albums, data=request.data, context={'request': request}, many=True)

        if serializer.is_valid():
            result = serializer.update(albums, serializer.validated_data)
            return Response(
                {
                    "updated_albums": result["updated_albums"],
                    "errors": result["errors"] if result["errors"] else None
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AlbumDetailView(APIView):
    def get_object(self, pk, user):
        try:
            return Album.objects.get(pk=pk, user=user)
        except Album.DoesNotExist:
            return None
        
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Update alum (titl, description) của user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(description="Cập nhật thành công", schema=AlbumUpdateSerializer),
            404: openapi.Response(description="Album không tồn tại"),
            400: openapi.Response(description="Dữ liệu không hợp lệ"),
        },
    )
    def get(self, request, pk):
        user = request.user
        album = self.get_object(pk, user)
        if album is None:
            return Response({"error": "Không tìm thấy album"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AlbumSerializer(album)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class AlbumALLSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()
    class Meta:
        model = Album
        fields = ['id_album', 'title', 'description', 'user', 'count','created_at', 'updated_at']
        read_only_fields = ['id_album']
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': False},
            'user': {'required': True},
            'created_at': {'required': False},
            'updated_at': {'required': False},
            'count': {'required': False},
       }
        
    def get_count(self, obj):
        album_id = obj.id_album
        photos = Photo.objects.filter(album=album_id, is_deleted=False)
        return photos.count()

class AlbumDetailALLView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="All album for user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(description="Cập nhật thành công", schema=AlbumUpdateSerializer),
            404: openapi.Response(description="Album không tồn tại"),
            400: openapi.Response(description="Dữ liệu không hợp lệ"),
        },
    )
    def get(self, request):
        user = request.user
        albums = Album.objects.filter(user=user)
        serializer = AlbumALLSerializer(albums, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class TrashView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Remove photos forever of user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=TrashActionSerializer,
        responses={
            201: openapi.Response(description="Add photos remove successfully", schema=TrashActionSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def delete(self, request):
        serializer = TrashActionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            deleted_photos, errors = serializer.delete_photos_permanently(request)
            return Response({"deleted photos":deleted_photos,"errors":errors}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FavoriteView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(description="Created successfully", schema=FavoriteSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def get(self, request):
        user = request.user
        favorite = Favorite.objects.filter(photo__album__user=user)
        serializer = FavoriteSerializer(favorite, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Add favorite photos for user ",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=AddFavoriteSerializer,
        responses={
            201: openapi.Response(description="Created successfully", schema=AddFavoriteSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = AddFavoriteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            favorites, invalid_photos, already_favorite = serializer.save()
            return Response(
                {
                    "favorite": [{"favorite id":favorite.id_favorite, "photo id":favorite.photo.id_photo, "note":favorite.note, "updated_at":favorite.updated_at, "created_at":favorite.created_at} for favorite in favorites],
                    "already_favorite": [photo for photo in already_favorite],
                    "invalid_photos" : [photo for photo in invalid_photos],
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Remove photo favorite for user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=RemoveFavoriteSerializer,
    )
    def delete(self, request, format=None):
        photo_ids = request.data.get('id_photos', [])
        if not isinstance(photo_ids, list):
            return Response({"error": "id_photos phải là danh sách các số nguyên."}, status=status.HTTP_400_BAD_REQUEST)
        photo_ids = [data for data in request.data['id_photos']]
        photos = Photo.objects.filter(id_photo__in=photo_ids, album__user=request.user, is_deleted=False)

        if not photos.exists():
            return Response({"error": "Không tìm favorite nào hợp lệ để cập nhật."}, status=status.HTTP_400_BAD_REQUEST)
        
        photos = Photo.objects.filter(id_photo__in=photo_ids, album__user=request.user, is_deleted=False)
        serializer = RemoveFavoriteSerializer(photos, data=request.data, context={'request': request})
        if serializer.is_valid():
            id_remove_sucess, invalid_photos = serializer.deletes_favorite(photos ,photo_ids)
            return Response(
                {
                    "photos removed favorite": id_remove_sucess,
                    "invalid_photos" : invalid_photos,
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Update photo",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=FavoriteListSerializer(many=True),
        responses={
            201: openapi.Response(description="Created successfully", schema=FavoriteListUpdateSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def put(self, request, *args, **kwargs):
        if not isinstance(request.data, list):
            return Response({"error": "Dữ liệu phải là danh sách JSON."}, status=status.HTTP_400_BAD_REQUEST)

        favorite_ids = [data.get("id_favorite") for data in request.data if "id_favorite" in data]
        favorites = Favorite.objects.filter(id_favorite__in=favorite_ids, photo__album__user=request.user)
        if not favorites.exists():
            return Response({"error": "Không tìm favorite nào hợp lệ để cập nhật."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = FavoriteListUpdateSerializer(favorites, data=request.data, context={'request': request}, many=True)
        if serializer.is_valid():
            updated_favorites,  errors= serializer.update(favorites, serializer.validated_data)
            return Response(
                {
                    "updated_favorites": updated_favorites,
                    "errors" : errors
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  
    
class SearchHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(description="Created successfully", schema=SearchHistorySerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def get(self, request):
        user = request.user
        search_history = Search_history.objects.filter(user=user)
        serializer = SearchHistorySerializer(search_history, many=True)
        return Response(serializer.data)
    
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=SearchHistorySerializerCustom,
        responses={
            201: openapi.Response(description="Created successfully", schema=SearchHistorySerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = SearchHistorySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    
class SearchHistoryDetailView(APIView):
    def get_object(self, pk):
        try:
            return Search_history.objects.get(pk=pk)
        except Search_history.DoesNotExist:
            raise Http404
        
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(description="Created successfully", schema=SearchHistorySerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def get(self, request, pk):
        user = request.user
        search_history = self.get_object(pk)
        if search_history.user != user:
            return Response({"error": "Không có quyền truy cập"}, status=status.HTTP_403_FORBIDDEN)
        serializer = SearchHistorySerializer(search_history)
        return Response(serializer.data)

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(description="Created successfully", schema=SearchHistorySerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def delete(self, request, pk, *args, **kwargs):
        search_history = self.get_object(pk)
        if search_history.user != request.user:
            return Response({"error": "Không có quyền truy cập"}, status=status.HTTP_403_FORBIDDEN)
        search_history.delete()
        return Response({'Deleted search history': pk},status=status.HTTP_200_OK)
    
class GetUserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(description="Created successfully", schema=SearchHistorySerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def get(self, request):
        user = request.user
        search_histories =  Search_history.objects.filter(user=user)
        serializer = SearchHistorySerializer(search_histories, many=True)
        return Response(serializer.data)
    
class RestorePhotoListView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Restore photos for user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=TrashActionSerializer,
        responses={
            201: openapi.Response(description="Add photos remove successfully", schema=TrashActionSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = TrashActionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            restored_photos, errors = serializer.restore_photos(request)
            restored = [PhotoAblumSerializer(photo).data for photo in restored_photos]
            return Response({"restored":restored, "errors": errors}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetAblumUser(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Create an example",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(description="Created successfully", schema=AlbumDetailSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def get(self, request):
        user = request.user 
        albums = Album.objects.filter(user=user)
        serializer =  AlbumDetailSerializer(albums, many=True)
        return Response(serializer.data)

class SearchDetailUser(APIView):
    permission_classes = (permissions.AllowAny,)
    parser_classes = [JSONParser]
    @swagger_auto_schema(
        operation_description="Search User",
        request_body=FormSearch,
        responses={
            201: openapi.Response(description="Search filter completed", schema=FormSearch),
            400: openapi.Response(description="Validation errors"),
        },
    )
    def post(self, request):
        search_text = request.data.get('search_text', '')
        users = get_user_model().objects.filter(name__icontains=search_text)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
class SearchAlbum(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    @swagger_auto_schema(
        operation_description="Retrieve user details using an Authorization token",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=FormSearch,
        responses={200: UserSerializer, 401: "Unauthorized"}
    )
    def post(self, request):
        search_text = request.data.get('search_text', '')
        list_album = Album.objects.filter(title__icontains=search_text)
        serializer = AlbumSerializer(list_album, many=True)
        return Response(serializer.data)
    
class SearchHistory(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    @swagger_auto_schema(
        operation_description="Retrieve user details using an Authorization token",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=FormSearch,
        responses={200: UserSerializer, 401: "Unauthorized"}
    )
    def post(self, request):
        search_text = request.data.get('search_text', '')
        list_search_history = Search_history.objects.filter(search_query__icontains=search_text)
        serializer = SearchHistorySerializer(list_search_history, many=True)
        return Response(serializer.data)
    
class SearchPhoto(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    @swagger_auto_schema(
        operation_description="Retrieve user details using an Authorization token",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=FormSearch,
        responses={200: UserSerializer, 401: "Unauthorized"}
    )
    def post(self, request):
        search_text = request.data.get('search_text', '')
        user = request.user
        list_search_history = Photo.objects.filter(name__icontains=search_text, album__user=user)
        liked_images = [
            {
                **photo,
                'created_at': photo['created_at'].isoformat() if isinstance(photo['created_at'], datetime) else photo['created_at'],
                'updated_at': photo['updated_at'].isoformat() if isinstance(photo['updated_at'], datetime) else photo['updated_at'],
            }
            for photo in PhotoInviCommunitySerializer(list_search_history, many=True).data
        ]
        Search_history.objects.create(
            search_query=search_text,
            search_type='normal',
            user=user,
            search_date=timezone.now(),
            liked_images=liked_images
        )
        serializer = PhotoAblumSerializer(list_search_history, many=True)
        return Response(serializer.data)

class FavoriteUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Update note of a favorite photo",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=FavoriteListSerializer,
        responses={
            200: openapi.Response(description="Favorite updated successfully", schema=UpdateFavoriteSerializer),
            400: openapi.Response(description="Invalid data"),
            404: openapi.Response(description="Favorite not found"),
        },
    )
    def put(self, request, pk):
        favorite = get_object_or_404(Favorite, id_favorite=pk)
        serializer = UpdateFavoriteSerializer(favorite, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "id_favorite": favorite.id_favorite,
                    "photo_id": favorite.photo.id_photo,
                    "note": favorite.note,
                    "updated_at": favorite.updated_at,
                    "created_at": favorite.created_at
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LikePhotoView(APIView):
    permission_classes = [IsAuthenticated]  
    def post(self, request, pk):
        """API để like ảnh"""
        user = request.user

        try:
            photo = Photo.objects.get(pk=pk, is_public=True)
        except Photo.DoesNotExist:
            raise Http404
        
        like, created = Like.objects.get_or_create(user=user, photo=photo)

        if created:
            photo.increate_like += 1 
            photo.save()
            return Response({'message': 'Photo liked successfully', 'like_count': photo.like_count}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'You already liked this photo'}, status=status.HTTP_400_BAD_REQUEST)
        
class RandomPulicUserPhotoListView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Get of photo public for user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def get(self, request):
        serializer = RandomPhotoUserListSerializer(context={'request': request})
        result = serializer.get_obj(serializer.data)
        if result:
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class AvatarView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Get Avatar of user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def get(self, request):
        user = request.user
        avatar = Avatar.objects.filter(user=user).first()
        if avatar:
            serializer = AvatarSerializer(avatar)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "Không tìm thấy avatar"}, status=status.HTTP_404_NOT_FOUND)
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  
    @swagger_auto_schema(
        operation_description="Put avatar cho người dùng",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'avatar',
                openapi.IN_FORM,
                description="Ảnh avatar tải lên",
                type=openapi.TYPE_FILE,
                required=True
            ),
        ],
        responses={201: "Avatar uploaded successfully", 400: "Validation error"}
    )
    def put(self, request):
        user = request.user
        if Avatar.objects.filter(user=user).exists():
            avatar = Avatar.objects.filter(user=user).first()
            if avatar:
                file_path = avatar.avatar.path
                if os.path.exists(file_path):
                    if str(avatar.avatar.url) != '/store/avatar/default_image/default.jpg':
                        os.remove(file_path) 
            serializer = AvatarPostSerializer(avatar, data=request.data, context={'request': request})
            if serializer.is_valid():
                result = serializer.save()
                return Response(AvatarPostSerializer(result).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "Không tìm thấy avatar"}, status=status.HTTP_404_NOT_FOUND)

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  
    @swagger_auto_schema(
        operation_description="Put avatar cho người dùng",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )]
        )
    def delete(self, request):
        user = request.user
        avatar = Avatar.objects.filter(user=user).exists()
        if avatar:
            avatar = Avatar.objects.filter(user=user).first()
            if avatar:
                file_path = avatar.avatar.path
                if os.path.exists(file_path):
                    if str(avatar.avatar.url) != '/store/avatar/default_image/default.jpg':
                        os.remove(file_path)
                    else:
                        return Response({"error": "Không thể xóa ảnh mặc định"}, status=status.HTTP_400_BAD_REQUEST) 
                    avatar.avatar = 'avatar/default_image/default.jpg'
                    avatar.save()
                    return Response({"message": "Avatar deleted successfully"}, status=status.HTTP_200_OK)
        return Response({"error": "Không tìm thấy avatar"}, status=status.HTTP_404_NOT_FOUND)

class PhotoPutView(APIView):
    permission_classes = [IsAuthenticated]  
    parser_classes = [MultiPartParser, FormParser]  
    @swagger_auto_schema(
        operation_description="Upload avatar cho người dùng",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'photo',
                openapi.IN_FORM,
                description="Ảnh avatar tải lên",
                type=openapi.TYPE_FILE,
                required=True
            ),
        ],
        responses={201: "Avatar uploaded successfully", 400: "Validation error"}
    )
    def put(self, request, pk):
        """Xử lý tạo album và upload nhiều ảnh"""
        request.data['id'] = pk
        serializer = PhotoUploadSerializertt(data=request.data, context={'request': request})
        if serializer.is_valid():
            response_data = serializer.create(serializer.validated_data) 
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_object(self, pk, user):
        try:
            return Photo.objects.get(album__user=user, id_photo=pk, is_deleted=False)
        except Photo.DoesNotExist:
            return None
    permission_classes = [IsAuthenticated]  
    @swagger_auto_schema(
        operation_description="Upload avatar cho người dùng",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={201: "Avatar uploaded successfully", 400: "Validation error"}
    )
    def get(self, request, pk):
        user = request.user
        photo = self.get_object(pk, user)     
        if photo is None:
            return Response({'error':'Khong tim thay thong tin anh cua user'}, status=status.HTTP_404_NOT_FOUND)
        return Response(PhotoAblumSerializer(photo).data, status=status.HTTP_200_OK) 

class PhotoInfoView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Update photo",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=PhotoBulkUpdateSerializer(many=True),
        responses={
            201: openapi.Response(description="Created successfully", schema=PhotoBulkUpdateSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def put(self, request, *args, **kwargs):
        """
        API cập nhật nhiều ảnh cùng lúc.
        """
        if not isinstance(request.data, list):
            return Response({"error": "Dữ liệu phải là danh sách JSON."}, status=status.HTTP_400_BAD_REQUEST)

        photo_ids = [data.get("id_photo") for data in request.data if "id_photo" in data]
        photos = Photo.objects.filter(id_photo__in=photo_ids, album__user=request.user)  

        if not photos.exists():
            return Response({"error": "Không tìm thấy ảnh nào hợp lệ để cập nhật."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PhotoBulkUpdateSerializer(photos, data=request.data, context={'request': request}, many=True)

        if serializer.is_valid():
            updated_photos, errors = serializer.update(photos, serializer.validated_data)
            return Response(
                {
                    "updated_photos": updated_photos,
                    "errors": errors
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PhotoDeleteListView(APIView):
    def get_object(self, pk, user):
        try:
            photo = Photo.objects.get(pk=pk)
            if photo.album.user != user:
                return "not_owned"
            if photo.is_deleted == True:
                return "already_deleted"
            return photo
        except Photo.DoesNotExist:
            return None
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Xóa ảnh của user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=ListForm,
    )
    def delete(self, request, format=None): 
        user = request.user
        deleted_photos = []
        already_deleted_photos = []
        not_found_photos = []
        not_owned_photos = []
        for pk in request.data['photos']:
            photo = self.get_object(pk, user)
            if photo == "already_deleted":
                already_deleted_photos.append(pk) 
                continue
            if photo == "not_owned":
                not_owned_photos.append(pk) 
                continue
            if photo:
                photo.is_deleted = True
                photo.updated_at = timezone.now()
                trash = Trash.objects.create(user=user, photo=photo)
                trash.deleted_at = timezone.now()
                photo.save()
                trash.save()
                deleted_photos.append(trash)
                continue
            else:
                not_found_photos.append(pk)
        deleted_photos = [TrashSeriizer(trash).data for trash in deleted_photos]
        return Response(
            {
                "Deleted photos": deleted_photos,  
                "Already deleted photos": already_deleted_photos,  
                "Not owned photos": not_owned_photos,  
                "Not found photos": not_found_photos  
            },
            status=status.HTTP_207_MULTI_STATUS
        )
   
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Thùng rác của user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def get(self, request):
        user = request.user
        photos = Photo.objects.filter(album__user=user, is_deleted=True)
        serializer = PhotoSerializer(photos, many=True)
        return Response(serializer.data, status=200)
    
class LikeView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Thùng rác của user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def get(self, request):
        user = request.user
        likes = Like.objects.filter(user=user)
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data, status=200)

    def get_object(self, pk):
        try:
            return Photo.objects.get(pk=pk, is_deleted=False, is_public=True)
        except Photo.DoesNotExist:
            return None
        
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Thùng rác của user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=ListForm,
    )
    def post(self, request):
        user = request.user
        not_found_photos = []
        likes = []
        exited_likes = []
        for pk in request.data['photos']:
            photo = self.get_object(pk)
            if photo:
                if not Like.objects.filter(user=user, photo=photo).exists():
                    photo.like_count += 1
                    photo.save()
                    like = Like.objects.create(user=user, photo=photo)
                    likes.append(like)
                    messageSend = f'{user.name} đã thích ảnh của bạn'
                    if photo.album.user != user:
                        Notification.objects.create(recipient=photo.album.user,
                                                            sender=user,
                                                            notif_type='like_photo',
                                                            photo=photo,
                                                            comment=None,
                                                            message=messageSend,
                                                            created_at=timezone.now())
                else:
                    exited_likes.append(Like.objects.filter(user=user, photo=photo).first())
            else:
                not_found_photos.append(pk)
                continue
        return Response(
            {
                "Liked photos": [LikeSerializer(like).data for like in likes],
                "Exited liked": [LikeSerializer(like).data for like in exited_likes], 
                "Not found photos": not_found_photos
            },
            status=status.HTTP_207_MULTI_STATUS
        )
    
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Thùng rác của user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=ListForm,
    )
    def delete(self, request):
        user = request.user
        not_found_photos = []
        photo_unliked = []
        for pk in request.data['photos']:
            photo = self.get_object(pk)
            if photo:
                like = Like.objects.filter(photo=photo, user=user).exists()
                if like:
                    photo.like_count -= 1
                    photo.save()
                    like = Like.objects.get(photo=photo, user=user)
                    like.delete()
                    photo_unliked.append(photo.id_photo)
                else: 
                    not_found_photos.append(pk)    
            else:
                not_found_photos.append(pk)
                continue
        return Response(
            {
                "Unliked photos": photo_unliked,
                "Not found photos": not_found_photos
            },
            status=status.HTTP_207_MULTI_STATUS
        )

class RandomPulicPhotoListView(APIView):
    def get(self, request):
        serializer = RandomPhotoListSerializer(context={'request': request})
        result = serializer.get_obj(serializer.data)
        if result:
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class PhotoCommunityDetailView(APIView):
    def get_object(self, pk):
        try:
            return Photo.objects.get(pk=pk, is_public=True, is_deleted=False)
        except Photo.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        photo = self.get_object(pk)
        serializer = PhotoDynamicSerializer(photo)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class PhotoCommunityUserDetailView(APIView):
    def get_object(self, pk):
        try:
            return Photo.objects.get(pk=pk, is_public=True, is_deleted=False)
        except Photo.DoesNotExist:
            raise Http404
            
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Lấy bài post của user khi đăng nhập ",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def get(self, request, pk):
        photo = self.get_object(pk)
        serializer = PhotoDynamicUserSerializer(photo, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class CommentView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Thêm comment mới cho ảnh",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token cho xác thực (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: "Comment được tạo thành công",
            400: "Dữ liệu không hợp lệ",
            401: "Không xác thực"
        }
    )
    def get(self, request):
        user = request.user
        comments = Comment.objects.filter(user=user)
        serializer = CommentSerilizer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CommentPushView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Thêm comment mới cho ảnh",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token cho xác thực (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=CommentSerilizerDetail,
        responses={
            201: "Comment được tạo thành công",
            400: "Dữ liệu không hợp lệ",
            401: "Không xác thực"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = CommentSerilizerDetail(data=request.data, context={'request': request})
        if serializer.is_valid():
            comment = serializer.save()
            return Response(CommentSerilizer(comment).data,status=status.HTTP_201_CREATED)
        else:
            return Response({"errors": serializer.errors},status=status.HTTP_400_BAD_REQUEST)

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Thùng rác của user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=CommentPutSerilizerDetail,
        responses={
            201: "Comment được chỉnh sửa thành công",
            400: "Dữ liệu không hợp lệ",
            401: "Không xác thực"
        }
    )
    def put(self, request):
        serializer = CommentPutSerilizerDetail(data= request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            comment = serializer.save()
            return Response(CommentSerilizer(comment).data,status=status.HTTP_201_CREATED)
        else:
            return Response({"errors": serializer.errors},status=status.HTTP_400_BAD_REQUEST)

class CommentDeletedlView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Xóa comment của user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def delete(self, request, pk):
        user = request.user
        comment = Comment.objects.filter(user=user, id_comment=pk).first()
        if comment:
            comment.delete()
            return Response({'Deleted comment': pk}, status=status.HTTP_200_OK)
        return Response({'error': 'Không tìm thấy comment hoặc bạn không có quyền xóa'}, status=status.HTTP_404_NOT_FOUND)

class CommentDetailView(APIView):
    def get_photo(self, pk):
        try:
            return Photo.objects.filter(id_photo=pk, is_deleted=False, is_public=True).first()
        except Photo.DoesNotExist:
            return None
    
    def get_object(self, pk):
        try:
            photo = self.get_photo(pk=pk)
        except Photo.DoesNotExist:
            return None
        comments = Comment.objects.filter(photo = photo)
        if len(comments) == 0:
            return None
        return comments
        
    permission_classes = [AllowAny]
    def get(self, request, pk):
        comments = self.get_object(pk=pk)
        if comments is None:
            return Response({'error': 'khong co binh luan cho bai anh'}, status=status.HTTP_200_OK)
        serializer = CommentSerilizer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class LikeCommentView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Like comment",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id_comment=comment_id)
        user = request.user
        if comment.is_liked_by_user(user):
            return Response(
                {"message": "Bạn đã like comment này rồi."},
                status=status.HTTP_400_BAD_REQUEST
            )
        messageSend = f'{user.name} đã thích bình luận của bạn'
        comment.increase_like(user)
        if comment.user == user:
            serializer = LikeCommentSerializer(comment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        Notification.objects.create(recipient=comment.user,
                                           sender=user,
                                           notif_type='like_comment',
                                           photo=comment.photo,
                                           comment=comment,
                                           message=messageSend,
                                           created_at=timezone.now()
        )
        serializer = LikeCommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class UnlikeCommentView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Like comment",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id_comment=comment_id)
        user = request.user

        if not comment.is_liked_by_user(user):
            return Response(
                {"message": "Bạn chưa like comment này."},
                status=status.HTTP_400_BAD_REQUEST
            )
        comment.decrease_like(user)
        serializer = LikeCommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Notification of user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def get(self, request):
        user = request.user
        notifications = Notification.objects.filter(recipient=user).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Notification of user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def delete(self, request):
        user = request.user
        Notification.objects.all().delete()
        return Response({'message': 'Deleted all notifications'}, status=status.HTTP_200_OK)

class NotificationDetailView(APIView):
    def get_object(self, pk, user):
        try:
            return Notification.objects.get(id=pk, recipient=user)
        except Notification.DoesNotExist:
            return None
        
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Notification of user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def get(self, request, pk):
        notification = self.get_object(pk, request.user)
        if notification is None:
            return Response({'error': 'Không tìm thấy thông báo'}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Notification of user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def delete(self, request, pk):
        notification = self.get_object(pk, request.user)
        if notification is None:
            return Response({'error': 'Không tìm thấy thông báo'}, status=status.HTTP_404_NOT_FOUND)
        notification.delete()
        return Response({'message': 'Deleted notification'}, status=status.HTTP_202_ACCEPTED)
    
class NotiPhotoDetailView(APIView):
    def get_object(self, pk):
        try:
            return Photo.objects.get(id_photo=pk, is_public=True, is_deleted=False)
        except Photo.DoesNotExist:
            return None

    def get(self, request, pk):
        photo = self.get_object(pk)
        if photo is None:
            return Response({'error': 'Không tìm thấy bài viết'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PhotoInviCommunitySerializer(photo, context={"hide_album_info": True}).data
        return Response(serializer, status=status.HTTP_202_ACCEPTED)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Thay đổi mật khẩu",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=ChangePasswordSerializer, 
        responses={
            201: openapi.Response(description="Change Password", schema=ChangePasswordSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def put(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Đổi mật khẩu thành công.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
