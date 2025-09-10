from django.urls import path
from .views import RegisterView, LoginView, PasswordResetView, PasswordResetConfirmView, TokenRefreshView, ResendVerificationView
from .views import FileUploadView, UserFilesView, UserFileDeleteView
from .views import UserProfileView, UserProfilePictureUploadView, UserProfilePictureGetView
from .oauth_views import (
    GoogleOAuthInitiateView, 
    GoogleOAuthCallbackView, 
    GoogleOAuthCompleteProfileView,
    GoogleOAuthStatusView
)

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

    # Google OAuth Authentication
    path('auth/google/initiate/', GoogleOAuthInitiateView.as_view(), name='google_oauth_initiate'),
    path('auth/google/callback/', GoogleOAuthCallbackView.as_view(), name='google_oauth_callback'),
    path('auth/google/complete-profile/', GoogleOAuthCompleteProfileView.as_view(), name='google_oauth_complete_profile'),
    path('auth/google/status/', GoogleOAuthStatusView.as_view(), name='google_oauth_status'),

    # File Management
    path('user-files/', UserFilesView.as_view(), name='user_files_list'),
    path('files/upload/', FileUploadView.as_view(), name='file_upload'),
    path('user-files/<str:file_name>/', UserFileDeleteView.as_view(), name='user_file_delete'),
]


