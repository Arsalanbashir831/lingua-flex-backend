from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    # Campaign CRUD
    path('teacher/campaigns/', views.TeacherCampaignListCreateView.as_view(), name='teacher-campaign-list-create'),
    path('teacher/campaigns/<int:pk>/', views.TeacherCampaignDetailView.as_view(), name='teacher-campaign-detail'),
    
    # Campaign actions
    path('teacher/campaigns/<int:campaign_id>/send/', views.CampaignSendView.as_view(), name='campaign-send'),
    path('teacher/campaigns/<int:campaign_id>/send-to-students/', views.CampaignSendToSpecificStudentsView.as_view(), name='campaign-send-to-students'),
    path('teacher/campaigns/<int:campaign_id>/preview/', views.campaign_preview, name='campaign-preview'),
    
    # Campaign statistics and student management
    path('teacher/campaigns/stats/', views.CampaignStatsView.as_view(), name='campaign-stats'),
    path('teacher/students/', views.get_available_students, name='available-students'),
]
