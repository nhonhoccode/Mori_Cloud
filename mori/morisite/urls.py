from .views import *
from .adminAPI import *
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .searchAI import SearchPhotosPublicAI, SearchPhotosForUserAI, SearchPhotosCommunityForUserAI
from .forgetPass import ForgotPasswordView, profile, custom_login_view, home_page, redirect_landing

schema_view = get_schema_view(
   openapi.Info(
      title="Your API",
      default_version='v1==1.0.0',
      description="Description of your API",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
   # ui
   path("", redirect_landing, name='landing'),
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
   # photo
   path('photo/', PhotoView.as_view(), name='photo'),
   path('photo/user/public/', PhotoPublicUserView.as_view(), name='photo'),
   path('photo/<int:pk>/', PhotoPutView.as_view(), name='photo'),
   path('photo/info/', PhotoInfoView.as_view(), name='upload-multiple-photos'),
   path('photo/delete/', PhotoDeleteListView.as_view(), name='upload-multiple-photos'),
   # album
   path('album/', AlbumView.as_view(), name='album'),   
   path('album/<int:pk>/', AlbumDetailView.as_view(), name='album'),   
   path('album/all/', AlbumDetailALLView.as_view(), name='album'),   
   # get trash
   path('trash/', TrashView.as_view(), name='trash'),   
   path('trash/restores/', RestorePhotoListView.as_view(), name='restore-photo-list'),
   # get favorite 
   path('favorite/', FavoriteView.as_view(), name='favorite'),
   path('favorite/<int:pk>/', FavoriteUpdateView.as_view(), name='favorite'),
   # get search history
   path('search-history/', SearchHistoryView.as_view(), name='search-history'),
   path('search-history/<int:pk>/', SearchHistoryDetailView.as_view(), name='search-historyid'),
   # user 
   path('user/', GetUserView.as_view(), name='get-user'),
   path('user/info/', GetUserInfoView.as_view(), name='get-user'),
   path('user/login/', LoginView.as_view(), name='loginview'),
   path('user/register/', UserRegistrationView.as_view(), name='register'),
   path('user/album/', GetAblumUser.as_view(), name="user_album_all"),
   # search anh, user, filter, album
   path('search/user/', SearchDetailUser.as_view(), name='search-user'),
   path('search/album/', SearchAlbum.as_view(), name='search-album'),
   path('search/history/', SearchHistory.as_view(), name='search-history'),
   path('search/photo/normal/', SearchPhoto.as_view(), name='search-history'),
   # photo public
   path('photo-public/<int:pk>/', PhotoCommunityDetailView.as_view(), name='photo-communityid'),
   path('photo-public/', RandomPulicPhotoListView.as_view(), name='photo-public'),
   # photopublic for user
   path('photo-public-user/<int:pk>/', PhotoCommunityUserDetailView.as_view(), name='photo-communityid'),
   path('photo-public-user/', RandomPulicUserPhotoListView.as_view(), name='photo-public'),
   # avatar 
   path('avatar/', AvatarView.as_view(), name='avatar'),
   # like
   path('like/', LikeView.as_view(), name='like'),
   # AI 
   path('search/photos/', SearchPhotosPublicAI.as_view(), name='search_photos_ai'),
   path('search/photos/user/', SearchPhotosForUserAI.as_view(), name='search_photos_ai_for_user'),
   path('search/photos/community/user/', SearchPhotosCommunityForUserAI.as_view(), name='search_photos_ai_community_user'),
   # Profile
   path('profile/', profile, name='profile'),
   path("login/", custom_login_view, name="custom_login"),  
   path("mori/", home_page, name="home_page"),  
   path('user/forgot/', ForgotPasswordView.as_view(), name='forgot-password'),
   path(
         'reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
               template_name='registration/password_reset_confirm.html'
         ),
         name='password_reset_confirm'
      ),
   path(
      'reset/done/',
      auth_views.PasswordResetCompleteView.as_view(
         template_name='registration/password_reset_complete.html'
      ),
      name='password_reset_complete'
   ),
   # comment 
   path('comments/', CommentView.as_view(), name='comment-view'),
   path('comments/photo/', CommentPushView.as_view(), name='comment-view'),
   path('comments/<int:comment_id>/like/', LikeCommentView.as_view(), name='like-comment'),
   path('comments/<int:comment_id>/unlike/', UnlikeCommentView.as_view(), name='unlike-comment'),
   path('comments/photo/<int:pk>', CommentDetailView.as_view(), name='comment-detail-view'),
   path('comments/<int:pk>', CommentDeletedlView.as_view(), name='comment-deleted-view'),
   #Noti 
   path('notifications/', NotificationView.as_view(), name='notification-view'),
   path('notifications/<int:pk>', NotificationDetailView.as_view(), name='notification-view'),
   path('notifications/photo/<int:pk>', NotiPhotoDetailView.as_view(), name='notification-delete-view'),
   # change password
   path('change-password/', ChangePasswordView.as_view(), name='change-password'),
   # admin
   path('api/admin/change-password/', ChangePassworAdmindView.as_view(), name='change-password-admin'),
   path('api/admin/photouploadnow/', PhotoUploadAdminNowView.as_view(), name='photo-upload-admin-now'),
   path('api/admin/photouploadall/', PhotoUploadAllAdminView.as_view(), name='photo-upload-admin-now'),
   path('api/admin/photofilter/', PhotoUploadAdminFilterView.as_view(), name='photo-upload-admin-now'),
   path('api/admin/count/', CountImagePublic.as_view(), name='count-image-public'), 
   path('api/admin/users/', GetUserAdminView.as_view(), name='get-user-admin'),
   path('api/admin/defineimage/', PhotoInfoAdminView.as_view(), name='photo-info-admin'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

