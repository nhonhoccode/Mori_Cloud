from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import *
from .adminSerializers import *

class PhotoUploadAdminFilterView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    @swagger_auto_schema(
        operation_description="Xac thuc",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'start_time',
                openapi.IN_QUERY,
                description="Thời gian bắt đầu (ISO 8601) vd: 2025-03-12 16:19:08.851 +0700",
                type=openapi.TYPE_STRING,
                format='date-time',
                required=False
            ),
            openapi.Parameter(
                'end_time',
                openapi.IN_QUERY,
                description="Thời gian kết thúc (ISO 8601) vd: 2025-04-12 16:19:08.851 +0700",
                type=openapi.TYPE_STRING,
                format='date-time',
                required=False
            ),
        ],
        responses={
            201: openapi.Response(description="Confirmed successfully"),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def get(self, request):
        serializer = PhotoFilterSerializer(data=request.query_params, context={'request': request})
        if serializer.is_valid():  
            results, count = serializer.get_photos()
            return Response({"count": count,"results": [PhotoAblumSerializer(photo).data for photo in results]}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ChangePassworAdmindView(APIView):
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
        request_body=ChangePasswordAdminSerializer, 
        responses={
            201: openapi.Response(description="Change Password", schema=ChangePasswordSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return Response({'error': 'Bạn không có quyền truy cập'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ChangePasswordAdminSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Đổi mật khẩu thành công.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PhotoUploadAdminNowView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Xac thuc",
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
            201: openapi.Response(description="Confirmed successfully"),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        if user.is_superuser == False:
            return Response({'error': 'Bạn không có quyền truy cập'}, status=status.HTTP_403_FORBIDDEN)
        photos = Photo.objects.filter(is_public=True, updated_at__date=today)
        serializer = PhotoSerializer(photos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class PhotoUploadAllAdminView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Xac thuc",
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
            201: openapi.Response(description="Confirmed successfully"),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        if user.is_superuser == False:
            return Response({'error': 'Bạn không có quyền truy cập'}, status=status.HTTP_403_FORBIDDEN)
        photos = Photo.objects.filter(is_public=True).order_by('created_at')
        serializer = PhotoSerializer(photos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CountImagePublic(APIView):
    permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Xac thuc",
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
            201: openapi.Response(description="Confirmed successfully"),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def get(self, request):
        """
        photo_total : Tổng số ảnh
        photo_deleted_count : Tổng số ảnh đã xóa
        photo_favorited_count : Tổng số ảnh đã yêu thích
        photo_liked_today : Tổng số ảnh đã được thích hôm nay
        trash_count_today : Tổng số ảnh đã được xóa hôm nay
        count_public : Tổng số ảnh công khai
        count_public_today : Tổng số ảnh công khai hôm nay
        user_count : Tổng số người dùng
        active_users_count : Tổng số người dùng đang hoạt động
        users_with_avatar : Tổng số người dùng có avatar
        user_regis_count : Tổng số người dùng đã đăng ký hôm nay
        search_history_count : Tổng số lịch sử tìm kiếm hôm nay
        comment_count : Tổng số bình luận
        comment_today : Tổng số bình luận hôm nay
        favorite_total : Tổng số ảnh yêu thích
        notification_today : Tổng số thông báo hôm nay
        notification_total : Tổng số thông báo
        """
        today = timezone.now().date()
        result = {
            'photo_total': Photo.objects.count(),
            'photo_deleted_count': Photo.objects.filter(is_deleted=True).count(),
            'photo_favorited_count': Photo.objects.filter(is_favorited=True).count(),
            'photo_liked_today': Like.objects.filter(created_at__date=today).count(),
            'trash_count_today': Trash.objects.filter(created_at__date=today).count(),
            'count_public': Photo.objects.filter(is_public=True).count(),
            'count_public_today': Photo.objects.filter(is_public=True, updated_at__date=today).count(),
            'user_count': User.objects.count(),
            'active_users_count': User.objects.filter(is_active=True).count(),
            'users_with_avatar': Avatar.objects.exclude(avatar='avatar/default_image/default.jpg').count(),
            'user_regis_count': User.objects.filter(created_at__date=today).count(),
            'search_history_count': Search_history.objects.filter(created_at__date=today).count(),
            'comment_count': Comment.objects.count(),
            'comment_today': Comment.objects.filter(created_at__date=today).count(),
            'favorite_total': Favorite.objects.count(),
            'notification_today': Notification.objects.filter(created_at__date=today).count(),
            'notification_total': Notification.objects.count(),
        }
        return Response(result, status=status.HTTP_200_OK)
    
class GetUserAdminView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Lấy thông tin người dùng",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token cho xác thực (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def get(self, request):
        user = request.user
        if user.is_superuser == False:
            return Response({'error': 'Bạn không có quyền truy cập'}, status=status.HTTP_403_FORBIDDEN)
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Xóa người dùng",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token cho xác thực (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        request_body=UserForm
    )
    def delete(self, request, format=None):
        user = request.user
        if not user.is_superuser:
            return Response({'error': 'Bạn không có quyền truy cập'}, status=status.HTTP_403_FORBIDDEN)
        serializer = UserForm(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                deleted_ids = serializer.perform_delete()
                return Response({'Deleted user': deleted_ids}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Thay đổi thông tin user",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token for authentication (format: Token <your_token>)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=UserBulkUpdateSerializer, 
        responses={
            201: openapi.Response(description="Created successfully", schema=PhotoSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return Response({'error': 'Bạn không có quyền truy cập'}, status=status.HTTP_403_FORBIDDEN)
        serializer = UserBulkUpdateSerializer(data=request.data)
        if serializer.is_valid():
            updated_users = serializer.save()
            return Response({'updated_users': [UserSerializer(u).data for u in updated_users]}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PhotoInfoAdminView(APIView):
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
        request_body=PhotoBulkUpdateAdminSerializer(many=True),
        responses={
            201: openapi.Response(description="Created successfully", schema=PhotoBulkUpdateSerializer),
            400: openapi.Response(description="Invalid data"),
        },
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return Response({'error': 'Bạn không có quyền truy cập'}, status=status.HTTP_403_FORBIDDEN)
        if not isinstance(request.data, list):
            return Response({"error": "Dữ liệu phải là danh sách JSON."}, status=status.HTTP_400_BAD_REQUEST)
        photo_ids = [data.get("id_photo") for data in request.data if "id_photo" in data]
        photos = Photo.objects.filter(id_photo__in=photo_ids) 
        existing_ids = set(photos.values_list("id_photo", flat=True))
        not_found_ids = [pid for pid in photo_ids if pid not in existing_ids] 
        if not photos.exists():
            return Response({"error": "Không tìm thấy ảnh nào hợp lệ để cập nhật."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PhotoBulkUpdateAdminSerializer(photos, data=request.data, context={'request': request}, many=True)
        if serializer.is_valid():
            updated_photos = serializer.update(photos, serializer.validated_data)
            if not_found_ids:
                return Response(
                    {
                        "updated_photos": updated_photos,
                        "not_found_ids": not_found_ids
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "updated_photos": updated_photos
                    },
                    status=status.HTTP_200_OK
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  