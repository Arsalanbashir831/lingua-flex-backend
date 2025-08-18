from django.urls import path
from .views import RegisterView, LoginView, PasswordResetView, PasswordResetConfirmView, TokenRefreshView, ResendVerificationView
from .views import FileUploadView, UserFilesView, UserFileDeleteView
from .views import UserProfileView, UserProfilePictureUploadView, UserProfilePictureGetView

urlpatterns = [
    # User Management
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/profile/', UserProfileView.as_view(), name='user_profile'),
    path('user/profile-picture/', UserProfilePictureUploadView.as_view(), name='user_profile_picture_upload'),
    path('user/profile-picture-url/', UserProfilePictureGetView.as_view(), name='user_profile_picture_get'),

    # File Management
    path('user-files/', UserFilesView.as_view(), name='user_files_list'),
    path('files/upload/', FileUploadView.as_view(), name='file_upload'),
    path('user-files/<str:file_name>/', UserFileDeleteView.as_view(), name='user_file_delete'),
]


