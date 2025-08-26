from django.urls import path
from . import views

app_name = 'blogs'

urlpatterns = [
    # Teacher blog management endpoints
    path('teacher/blogs/', views.TeacherBlogListCreateView.as_view(), name='teacher-blog-list-create'),
    path('teacher/blogs/<int:pk>/', views.TeacherBlogDetailView.as_view(), name='teacher-blog-detail'),
    path('teacher/blogs/stats/', views.teacher_blog_stats, name='teacher-blog-stats'),
    path('teacher/blogs/<int:blog_id>/duplicate/', views.duplicate_blog, name='duplicate-blog'),
    path('teacher/blogs/bulk-update/', views.bulk_update_blog_status, name='bulk-update-blog-status'),
    path('teacher/blogs/upload-thumbnail/', views.BlogThumbnailUploadView.as_view(), name='blog-thumbnail-upload'),
    path('teacher/blogs/<int:blog_id>/update-thumbnail/', views.BlogThumbnailUpdateView.as_view(), name='blog-thumbnail-update'),
    
    # Public blog endpoints (no authentication required)
    path('view/', views.PublicBlogListView.as_view(), name='public-blog-list'),
    path('view/<slug:slug>/', views.PublicBlogDetailView.as_view(), name='public-blog-detail'),
    
    # Blog categories
    path('categories/', views.BlogCategoryListCreateView.as_view(), name='blog-category-list-create'),
]
