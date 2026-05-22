from rest_framework import serializers
from .models import Blog
from accounts.models import TeacherProfile


class BlogListSerializer(serializers.ModelSerializer):
    """Serializer for listing blogs (minimal fields)"""

    author_name = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()

    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "slug",
            "thumbnail",
            "tags",
            "tag_list",
            "status",
            "author_name",
            "created_at",
            "updated_at",
            "published_at",
            "meta_description",
            "read_time",
            "view_count",
            "is_published",
        ]
        read_only_fields = [
            "id",
            "slug",
            "author_name",
            "created_at",
            "updated_at",
            "published_at",
            "read_time",
            "view_count",
            "is_published",
        ]


class BlogDetailSerializer(BlogListSerializer):
    """Serializer for detailed blog view with full content"""

    class Meta(BlogListSerializer.Meta):
        fields = BlogListSerializer.Meta.fields + ["content", "author"]
        read_only_fields = BlogListSerializer.Meta.read_only_fields + ["author"]


class BlogCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating blogs"""

    author = serializers.PrimaryKeyRelatedField(
        queryset=TeacherProfile.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Blog
        fields = [
            "title",
            "content",
            "thumbnail",
            "tags",
            "status",
            "meta_description",
            "author",
        ]

    def validate_title(self, value):
        """Validate blog title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Title must be at least 5 characters long."
            )
        return value.strip()

    def validate_content(self, value):
        """Validate blog content"""
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        if len(value.strip()) < 50:
            raise serializers.ValidationError(
                "Content must be at least 50 characters long."
            )
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
        """Create blog with authenticated teacher or admin as author"""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        user = request.user
        is_admin = user.is_superuser or user.is_staff or user.role == "ADMIN"

        if is_admin:
            # Admin can set author explicitly, or default to None (Administrator)
            if "author" not in validated_data:
                validated_data["author"] = None
        else:
            try:
                teacher_profile = TeacherProfile.objects.get(
                    user_profile__user=user
                )
            except TeacherProfile.DoesNotExist:
                raise serializers.ValidationError("Only teachers or administrators can create blogs.")
            
            # Standard teachers can only create blogs for themselves
            validated_data["author"] = teacher_profile

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update blog, ensuring only admins can modify author"""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            user = request.user
            is_admin = user.is_superuser or user.is_staff or getattr(user, "role", None) == "ADMIN"
            if not is_admin:
                # Standard teachers cannot change the author
                validated_data.pop("author", None)
        return super().update(instance, validated_data)



