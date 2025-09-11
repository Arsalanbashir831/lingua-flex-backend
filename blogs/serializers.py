from rest_framework import serializers
from .models import Blog, BlogCategory, BlogView
from accounts.models import TeacherProfile


class BlogCategorySerializer(serializers.ModelSerializer):
    """Serializer for blog categories"""
    
    class Meta:
        model = BlogCategory
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class BlogListSerializer(serializers.ModelSerializer):
    """Serializer for listing blogs (minimal fields)"""
    author_name = serializers.ReadOnlyField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    tag_list = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'thumbnail', 'category', 'category_name', 
            'tags', 'tag_list', 'status', 'author_name', 'created_at', 
            'updated_at', 'published_at', 'meta_description', 'read_time', 
            'view_count', 'is_published'
        ]
        read_only_fields = [
            'id', 'slug', 'author_name', 'created_at', 'updated_at', 
            'published_at', 'read_time', 'view_count', 'is_published'
        ]


class BlogDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed blog view with full content"""
    author_name = serializers.ReadOnlyField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    tag_list = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'content', 'thumbnail', 'category', 
            'category_name', 'tags', 'tag_list', 'status', 'author', 
            'author_name', 'created_at', 'updated_at', 'published_at', 
            'meta_description', 'read_time', 'view_count', 'is_published'
        ]
        read_only_fields = [
            'id', 'slug', 'author', 'author_name', 'created_at', 
            'updated_at', 'published_at', 'read_time', 'view_count', 
            'is_published'
        ]


class BlogCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating blogs"""
    
    class Meta:
        model = Blog
        fields = [
            'title', 'content', 'thumbnail', 'category', 'tags', 
            'status', 'meta_description'
        ]
    
    def validate_title(self, value):
        """Validate blog title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long.")
        return value.strip()
    
    def validate_content(self, value):
        """Validate blog content"""
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        if len(value.strip()) < 50:
            raise serializers.ValidationError("Content must be at least 50 characters long.")
        return value.strip()
    
    def validate_tags(self, value):
        """Validate tags format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        
        # Clean and validate each tag
        cleaned_tags = []
        for tag in value:
            if isinstance(tag, str) and tag.strip():
                cleaned_tag = tag.strip().lower()
                if cleaned_tag not in cleaned_tags:  # Avoid duplicates
                    cleaned_tags.append(cleaned_tag)
        
        if len(cleaned_tags) > 10:
            raise serializers.ValidationError("Maximum 10 tags allowed.")
        
        return cleaned_tags
    
    def create(self, validated_data):
        """Create blog with authenticated teacher as author"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")
        
        # Get teacher profile
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
        except TeacherProfile.DoesNotExist:
            raise serializers.ValidationError("Only teachers can create blogs.")
        
        validated_data['author'] = teacher_profile
        return super().create(validated_data)


class BlogViewSerializer(serializers.ModelSerializer):
    """Serializer for blog views"""
    
    class Meta:
        model = BlogView
        fields = ['id', 'blog', 'viewer_ip', 'user_agent', 'viewed_at']
        read_only_fields = ['id', 'viewed_at']


class BlogStatsSerializer(serializers.Serializer):
    """Serializer for blog statistics"""
    total_blogs = serializers.IntegerField()
    published_blogs = serializers.IntegerField()
    draft_blogs = serializers.IntegerField()
    archived_blogs = serializers.IntegerField()
    total_views = serializers.IntegerField()
    most_viewed_blog = serializers.CharField()
    recent_blogs_count = serializers.IntegerField()
    
    def to_representation(self, instance):
        # This is used when we pass calculated stats
        return instance
