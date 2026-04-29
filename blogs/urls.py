from django.urls import path
from . import views

app_name = "blogs"

urlpatterns = [
    # Teacher blog management endpoints
    path(
        "teacher/blogs/",
        views.TeacherBlogListCreateView.as_view(),
        name="teacher-blog-list-create",
    ),
    path(
        "teacher/blogs/<int:pk>/",
        views.TeacherBlogDetailView.as_view(),
        name="teacher-blog-detail",
    ),
    # Public blog endpoints (no authentication required)
    path("view/", views.PublicBlogListView.as_view(), name="public-blog-list"),
    path(
        "view/<slug:slug>/",
        views.PublicBlogDetailView.as_view(),
        name="public-blog-detail",
    ),
]
