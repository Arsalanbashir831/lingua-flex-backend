from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.db.models import Q, Count, Sum, Case, When, IntegerField, F
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import uuid
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authentication import TokenAuthentication
from core.authentication import SupabaseTokenAuthentication
from supabase import create_client, Client
from .models import Blog, BlogCategory, BlogView
from .serializers import (
    BlogListSerializer, BlogDetailSerializer, BlogCreateUpdateSerializer,
    BlogCategorySerializer, BlogStatsSerializer
)
from accounts.models import TeacherProfile

# Initialize Supabase client
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_ANON_KEY
)

# Import Supabase client
try:
    from supabase import create_client
except ImportError:
    create_client = None


class BlogPagination(PageNumberPagination):
    """Custom pagination for blogs"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class TeacherBlogListCreateView(generics.ListCreateAPIView):
    """
    List and create blogs for authenticated teachers
    GET: List teacher's blogs with filtering and search
    POST: Create new blog (supports both JSON and thumbnail file upload)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = BlogPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # Support both JSON and file uploads
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BlogCreateUpdateSerializer
        return BlogListSerializer
    
    def get_queryset(self):
        """Get blogs for the authenticated teacher with filtering"""
        # Ensure user is a teacher
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=self.request.user)
        except TeacherProfile.DoesNotExist:
            return Blog.objects.none()
        
        queryset = Blog.objects.filter(author=teacher_profile).select_related(
            'category', 'author__user_profile__user'
        )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by category
        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)
        
        # Search in title and content
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(tags__icontains=search)
            )
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Custom create method to handle thumbnail file upload"""
        # Ensure user is a teacher
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
        except TeacherProfile.DoesNotExist:
            return Response({
                'error': 'Only teachers can create blogs'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle thumbnail file upload if provided
        thumbnail_url = None
        if 'thumbnail' in request.FILES:
            thumbnail_file = request.FILES['thumbnail']
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
            if thumbnail_file.content_type not in allowed_types:
                return Response({
                    'error': 'Invalid thumbnail file type. Only JPEG, PNG, WebP, and GIF images are allowed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if thumbnail_file.size > max_size:
                return Response({
                    'error': 'Thumbnail file too large. Maximum size is 5MB'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Create unique filename
                import uuid
                file_extension = thumbnail_file.name.split('.')[-1].lower()
                unique_filename = f"blog_thumbnails/{teacher_profile.user_profile.user.id}/{uuid.uuid4()}.{file_extension}"
                
                # Upload to Supabase
                response = supabase.storage.from_('blog-images').upload(
                    unique_filename,
                    thumbnail_file.read(),
                    {
                        'content-type': thumbnail_file.content_type,
                        'cache-control': '3600',
                        'upsert': 'false'
                    }
                )
                
                # Get public URL
                public_url = supabase.storage.from_('blog-images').get_public_url(unique_filename)
                thumbnail_url = public_url
                
            except Exception as e:
                return Response({
                    'error': f'Failed to upload thumbnail: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Prepare data for serializer
        blog_data = request.data.copy()
        if thumbnail_url:
            blog_data['thumbnail'] = thumbnail_url
        
        # Create the blog using the serializer
        serializer = self.get_serializer(data=blog_data)
        if serializer.is_valid():
            serializer.save(author=teacher_profile)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
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
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # Support both JSON and file uploads
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BlogCreateUpdateSerializer
        return BlogDetailSerializer
    
    def get_queryset(self):
        """Get blogs for the authenticated teacher only"""
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=self.request.user)
            return Blog.objects.filter(author=teacher_profile).select_related(
                'category', 'author__user_profile__user'
            )
        except TeacherProfile.DoesNotExist:
            return Blog.objects.none()
    
    def update(self, request, *args, **kwargs):
        """Custom update method to handle thumbnail file upload"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Handle thumbnail file upload if provided
        thumbnail_url = None
        if 'thumbnail' in request.FILES:
            thumbnail_file = request.FILES['thumbnail']
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
            if thumbnail_file.content_type not in allowed_types:
                return Response({
                    'error': 'Invalid thumbnail file type. Only JPEG, PNG, WebP, and GIF images are allowed'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if thumbnail_file.size > max_size:
                return Response({
                    'error': 'Thumbnail file too large. Maximum size is 5MB'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Create unique filename
                import uuid
                file_extension = thumbnail_file.name.split('.')[-1].lower()
                unique_filename = f"blog_thumbnails/{instance.author.user_profile.user.id}/{uuid.uuid4()}.{file_extension}"
                
                # Upload to Supabase
                response = supabase.storage.from_('blog-images').upload(
                    unique_filename,
                    thumbnail_file.read(),
                    {
                        'content-type': thumbnail_file.content_type,
                        'cache-control': '3600',
                        'upsert': 'false'
                    }
                )
                
                # Get public URL
                public_url = supabase.storage.from_('blog-images').get_public_url(unique_filename)
                thumbnail_url = public_url
                
            except Exception as e:
                return Response({
                    'error': f'Failed to upload thumbnail: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Prepare data for serializer
        blog_data = request.data.copy()
        if thumbnail_url:
            blog_data['thumbnail'] = thumbnail_url
        
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
        return Response({
            'message': f'Blog "{blog_title}" has been deleted successfully.'
        }, status=status.HTTP_200_OK)


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
        ).select_related('category', 'author__user_profile__user')
        
        # Filter by category
        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)
        
        # Search in title and content
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(tags__icontains=search)
            )
        
        # Filter by tags
        tags_filter = self.request.query_params.get('tags')
        if tags_filter:
            tag_list = [tag.strip().lower() for tag in tags_filter.split(',')]
            for tag in tag_list:
                queryset = queryset.filter(tags__icontains=tag)
        
        return queryset.order_by('-published_at')


class PublicBlogDetailView(generics.RetrieveAPIView):
    """
    Public endpoint to view a specific published blog
    Also tracks views for analytics
    """
    serializer_class = BlogDetailSerializer
    permission_classes = []  # No authentication required
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Get only published blogs"""
        return Blog.objects.filter(
            status=Blog.StatusChoices.PUBLISHED
        ).select_related('category', 'author__user_profile__user')
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve blog and track view"""
        blog = self.get_object()
        
        # Track view (avoid duplicate views from same IP)
        self.track_blog_view(blog, request)
        
        serializer = self.get_serializer(blog)
        return Response(serializer.data)
    
    def track_blog_view(self, blog, request):
        """Track blog view for analytics"""
        try:
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Create or update view record
            blog_view, created = BlogView.objects.get_or_create(
                blog=blog,
                viewer_ip=ip,
                defaults={'user_agent': user_agent}
            )
            
            if created:
                # Increment view count on blog
                Blog.objects.filter(id=blog.id).update(
                    view_count=F('view_count') + 1
                )
        except Exception:
            # Don't fail the request if view tracking fails
            pass


class BlogCategoryListCreateView(generics.ListCreateAPIView):
    """
    List and create blog categories
    GET: List all categories (public)
    POST: Create category (teachers only)
    """
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    
    def get_permissions(self):
        """Different permissions for different methods"""
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return []  # GET is public
    
    def perform_create(self, serializer):
        """Ensure only teachers can create categories"""
        try:
            TeacherProfile.objects.get(user_profile__user=self.request.user)
            serializer.save()
        except TeacherProfile.DoesNotExist:
            raise permissions.PermissionDenied("Only teachers can create categories.")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_blog_stats(request):
    """
    Get blog statistics for the authenticated teacher
    """
    try:
        teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
    except TeacherProfile.DoesNotExist:
        return Response({'error': 'Teacher profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get teacher's blogs
    teacher_blogs = Blog.objects.filter(author=teacher_profile)
    
    # Calculate statistics
    stats = {
        'total_blogs': teacher_blogs.count(),
        'published_blogs': teacher_blogs.filter(status=Blog.StatusChoices.PUBLISHED).count(),
        'draft_blogs': teacher_blogs.filter(status=Blog.StatusChoices.DRAFT).count(),
        'archived_blogs': teacher_blogs.filter(status=Blog.StatusChoices.ARCHIVED).count(),
        'total_views': teacher_blogs.aggregate(total=Sum('view_count'))['total'] or 0,
        'most_viewed_blog': '',
        'recent_blogs_count': teacher_blogs.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
    }
    
    # Get most viewed blog
    most_viewed = teacher_blogs.order_by('-view_count').first()
    if most_viewed:
        stats['most_viewed_blog'] = most_viewed.title
    
    serializer = BlogStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def duplicate_blog(request, blog_id):
    """
    Create a duplicate of an existing blog
    """
    try:
        teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
        
        # Get the original blog
        original_blog = get_object_or_404(Blog, id=blog_id, author=teacher_profile)
        
        # Create duplicate
        with transaction.atomic():
            duplicate = Blog.objects.create(
                title=f"{original_blog.title} (Copy)",
                content=original_blog.content,
                thumbnail=original_blog.thumbnail,
                category=original_blog.category,
                tags=original_blog.tags.copy() if original_blog.tags else [],
                status=Blog.StatusChoices.DRAFT,  # Always start as draft
                author=teacher_profile,
                meta_description=original_blog.meta_description,
            )
        
        serializer = BlogDetailSerializer(duplicate)
        return Response({
            'message': 'Blog duplicated successfully',
            'blog': serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except TeacherProfile.DoesNotExist:
        return Response({'error': 'Teacher profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_blog_status(request):
    """
    Update status of multiple blogs at once
    """
    try:
        teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
    except TeacherProfile.DoesNotExist:
        return Response({'error': 'Teacher profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    blog_ids = request.data.get('blog_ids', [])
    new_status = request.data.get('status')
    
    if not blog_ids or not new_status:
        return Response({
            'error': 'blog_ids and status are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_status not in [choice[0] for choice in Blog.StatusChoices.choices]:
        return Response({
            'error': 'Invalid status'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update blogs
    updated_count = Blog.objects.filter(
        id__in=blog_ids,
        author=teacher_profile
    ).update(status=new_status)
    
    return Response({
        'message': f'{updated_count} blogs updated successfully',
        'updated_count': updated_count
    })


class BlogThumbnailUploadView(APIView):
    """
    Upload thumbnail image for blogs
    Teachers can upload image files that will be stored in Supabase
    """
    authentication_classes = [SupabaseTokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    
    def post(self, request):
        """Upload a thumbnail image and return the public URL"""
        try:
            # Check if user has teacher profile
            teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
        except TeacherProfile.DoesNotExist:
            return Response({
                'error': 'Only teachers can upload blog thumbnails'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if file is provided
        if 'thumbnail' not in request.FILES:
            return Response({
                'error': 'No thumbnail file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        thumbnail_file = request.FILES['thumbnail']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if thumbnail_file.content_type not in allowed_types:
            return Response({
                'error': 'Invalid file type. Only JPEG, PNG, WebP, and GIF images are allowed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if thumbnail_file.size > max_size:
            return Response({
                'error': 'File too large. Maximum size is 5MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create unique filename
            import uuid
            file_extension = thumbnail_file.name.split('.')[-1].lower()
            unique_filename = f"blog_thumbnails/{teacher_profile.user_profile.user.id}/{uuid.uuid4()}.{file_extension}"
            
            # Upload to Supabase
            response = supabase.storage.from_('blog-images').upload(
                unique_filename,
                thumbnail_file.read(),
                {
                    'content-type': thumbnail_file.content_type,
                    'cache-control': '3600',
                    'upsert': 'false'
                }
            )
            
            # Get public URL
            public_url = supabase.storage.from_('blog-images').get_public_url(unique_filename)
            
            return Response({
                'message': 'Thumbnail uploaded successfully',
                'thumbnail_url': public_url,
                'filename': unique_filename
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to upload thumbnail: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlogThumbnailUpdateView(APIView):
    """
    Update blog thumbnail with automatic deletion of previous thumbnail
    Dedicated endpoint for replacing blog thumbnails
    """
    authentication_classes = [SupabaseTokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    
    def patch(self, request, blog_id):
        """Update blog thumbnail and delete previous one from Supabase"""
        try:
            # Check if user has teacher profile
            teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
        except TeacherProfile.DoesNotExist:
            return Response({
                'error': 'Only teachers can update blog thumbnails'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the blog
        try:
            blog = Blog.objects.get(id=blog_id, author=teacher_profile)
        except Blog.DoesNotExist:
            return Response({
                'error': 'Blog not found or you do not have permission to update it'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if file is provided
        if 'thumbnail' not in request.FILES:
            return Response({
                'error': 'No thumbnail file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        thumbnail_file = request.FILES['thumbnail']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if thumbnail_file.content_type not in allowed_types:
            return Response({
                'error': 'Invalid file type. Only JPEG, PNG, WebP, and GIF images are allowed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if thumbnail_file.size > max_size:
            return Response({
                'error': 'File too large. Maximum size is 5MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Delete previous thumbnail if exists
            old_thumbnail_deleted = False
            if blog.thumbnail:
                old_thumbnail_path = self._extract_filename_from_url(blog.thumbnail)
                if old_thumbnail_path:
                    try:
                        supabase.storage.from_('blog-images').remove([old_thumbnail_path])
                        old_thumbnail_deleted = True
                    except Exception as delete_error:
                        # Log the error but continue with upload
                        print(f"Warning: Could not delete old thumbnail: {delete_error}")
            
            # Create unique filename for new thumbnail
            import uuid
            file_extension = thumbnail_file.name.split('.')[-1].lower()
            unique_filename = f"blog_thumbnails/{teacher_profile.user_profile.user.id}/{uuid.uuid4()}.{file_extension}"
            
            # Upload new thumbnail to Supabase
            response = supabase.storage.from_('blog-images').upload(
                unique_filename,
                thumbnail_file.read(),
                {
                    'content-type': thumbnail_file.content_type,
                    'cache-control': '3600',
                    'upsert': 'false'
                }
            )
            
            # Get public URL
            new_thumbnail_url = supabase.storage.from_('blog-images').get_public_url(unique_filename)
            
            # Update blog with new thumbnail URL
            old_thumbnail_url = blog.thumbnail
            blog.thumbnail = new_thumbnail_url
            blog.save(update_fields=['thumbnail'])
            
            return Response({
                'message': 'Thumbnail updated successfully',
                'blog_id': blog.id,
                'old_thumbnail_url': old_thumbnail_url,
                'new_thumbnail_url': new_thumbnail_url,
                'old_thumbnail_deleted': old_thumbnail_deleted,
                'filename': unique_filename
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to update thumbnail: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _extract_filename_from_url(self, url):
        """Extract filename from Supabase URL for deletion"""
        try:
            if not url or 'blog-images' not in url:
                return None
            
            # Extract the path after blog-images/
            parts = url.split('blog-images/')
            if len(parts) > 1:
                # Remove any query parameters
                filename = parts[1].split('?')[0]
                return filename
            return None
        except Exception:
            return None
