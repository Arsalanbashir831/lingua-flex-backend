from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Blog
from .serializers import (
    BlogListSerializer,
    BlogDetailSerializer,
    BlogCreateUpdateSerializer,
)
from .utils import handle_blog_thumbnail_upload
from accounts.models import TeacherProfile


class BlogPagination(PageNumberPagination):
    """Custom pagination for blogs"""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class TeacherBlogListCreateView(generics.ListCreateAPIView):
    """
    List and create blogs for authenticated teachers
    GET: List teacher's blogs with filtering and search
    POST: Create new blog (supports both JSON and thumbnail file upload)
    """

    permission_classes = [IsAuthenticated]
    pagination_class = BlogPagination
    parser_classes = [
        JSONParser,
        MultiPartParser,
        FormParser,
    ]  # Support both JSON and file uploads

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BlogCreateUpdateSerializer
        return BlogListSerializer

    def get_queryset(self):
        """Get blogs for the authenticated teacher or admin with filtering"""
        user = self.request.user
        is_admin = user.is_superuser or user.is_staff or getattr(user, "role", None) == "ADMIN"

        if is_admin:
            queryset = Blog.objects.all().select_related(
                "author__user_profile__user"
            )
        else:
            try:
                teacher_profile = TeacherProfile.objects.get(
                    user_profile__user=user
                )
            except TeacherProfile.DoesNotExist:
                return Blog.objects.none()

            queryset = Blog.objects.filter(author=teacher_profile).select_related(
                "author__user_profile__user"
            )

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)


        # Search in title and content
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(content__icontains=search)
                | Q(tags__icontains=search)
            )

        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        """Custom create method to handle thumbnail file upload"""
        user = request.user
        is_admin = user.is_superuser or user.is_staff or getattr(user, "role", None) == "ADMIN"

        if not is_admin:
            # Ensure user is a teacher
            try:
                TeacherProfile.objects.get(
                    user_profile__user=user
                )
            except TeacherProfile.DoesNotExist:
                return Response(
                    {"error": "Only teachers or administrators can create blogs"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Prepare data for serializer
        blog_data = request.data.copy()

        # Handle thumbnail file upload if provided
        if "thumbnail" in request.FILES:
            thumbnail_url, error_res = handle_blog_thumbnail_upload(
                request.FILES["thumbnail"], user.id
            )
            if error_res:
                return error_res
            blog_data["thumbnail"] = thumbnail_url

        # Create the blog using the serializer
        serializer = self.get_serializer(data=blog_data)
        if serializer.is_valid():
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherBlogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, and delete specific blog for authenticated teacher
    GET: Get blog details
    PUT/PATCH: Update blog (supports both JSON and thumbnail file upload)
    DELETE: Delete blog
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [
        JSONParser,
        MultiPartParser,
        FormParser,
    ]  # Support both JSON and file uploads

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return BlogCreateUpdateSerializer
        return BlogDetailSerializer

    def get_queryset(self):
        """Get blogs for the authenticated teacher or admin"""
        user = self.request.user
        is_admin = user.is_superuser or user.is_staff or getattr(user, "role", None) == "ADMIN"

        if is_admin:
            return Blog.objects.all().select_related(
                "author__user_profile__user"
            )
        else:
            try:
                teacher_profile = TeacherProfile.objects.get(
                    user_profile__user=user
                )
                return Blog.objects.filter(author=teacher_profile).select_related(
                    "author__user_profile__user"
                )
            except TeacherProfile.DoesNotExist:
                return Blog.objects.none()

    def update(self, request, *args, **kwargs):
        """Custom update method to handle thumbnail file upload"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Prepare data for serializer
        blog_data = request.data.copy()

        # Handle thumbnail file upload if provided
        if "thumbnail" in request.FILES:
            thumbnail_url, error_res = handle_blog_thumbnail_upload(
                request.FILES["thumbnail"], request.user.id
            )
            if error_res:
                return error_res
            blog_data["thumbnail"] = thumbnail_url

        # Update the blog using the serializer
        serializer = self.get_serializer(instance, data=blog_data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Custom delete with confirmation"""
        blog = self.get_object()
        blog_title = blog.title
        blog.delete()
        return Response(
            {"message": f'Blog "{blog_title}" has been deleted successfully.'},
            status=status.HTTP_200_OK,
        )


class PublicBlogListView(generics.ListAPIView):
    """
    Public endpoint to list published blogs (no authentication required)
    """

    serializer_class = BlogListSerializer
    pagination_class = BlogPagination
    permission_classes = []  # No authentication required

    def get_queryset(self):
        """Get only published blogs for public viewing"""
        queryset = Blog.objects.filter(
            status=Blog.StatusChoices.PUBLISHED
        ).select_related("author__user_profile__user")


        # Search in title and content
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(content__icontains=search)
                | Q(tags__icontains=search)
            )

        # Filter by tags
        tags_filter = self.request.query_params.get("tags")
        if tags_filter:
            tag_list = [tag.strip().lower() for tag in tags_filter.split(",")]
            for tag in tag_list:
                queryset = queryset.filter(tags__icontains=tag)

        return queryset.order_by("-published_at")


class PublicBlogDetailView(generics.RetrieveAPIView):
    """
    Public endpoint to view a specific published blog
    Also tracks views for analytics
    """

    serializer_class = BlogDetailSerializer
    permission_classes = []  # No authentication required
    lookup_field = "slug"

    def get_queryset(self):
        """Get only published blogs"""
        return Blog.objects.filter(status=Blog.StatusChoices.PUBLISHED).select_related(
            "author__user_profile__user"
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve blog and increment view count"""
        instance = self.get_object()
        # Use F() expression to avoid race conditions and atomicity
        from django.db.models import F
        Blog.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        # Refresh instance from DB to get the new view_count for the serializer
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
