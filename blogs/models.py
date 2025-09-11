from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from accounts.models import TeacherProfile


class BlogCategory(models.Model):
    """Model for blog categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Blog Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Blog(models.Model):
    """Model for teacher blogs"""
    
    class StatusChoices(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
    
    # Basic fields
    title = models.CharField(max_length=200, help_text='Blog title')
    slug = models.SlugField(max_length=250, unique=True, blank=True, help_text='URL-friendly version of title')
    content = models.TextField(help_text='Main blog content')
    thumbnail = models.CharField(max_length=500, blank=True, null=True, help_text='URL or path to thumbnail image')
    
    # Categorization
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='blogs')
    tags = models.JSONField(default=list, blank=True, help_text='List of tags for the blog')
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT)
    author = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='blogs')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, help_text='When the blog was published')
    
    # SEO and engagement
    meta_description = models.CharField(max_length=160, blank=True, help_text='SEO meta description')
    read_time = models.PositiveIntegerField(default=0, help_text='Estimated read time in minutes')
    view_count = models.PositiveIntegerField(default=0, help_text='Number of views')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['slug']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure slug is unique
            original_slug = self.slug
            counter = 1
            while Blog.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Set published_at when status changes to published
        if self.status == self.StatusChoices.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        elif self.status != self.StatusChoices.PUBLISHED:
            self.published_at = None
        
        # Auto-calculate read time based on content
        if self.content:
            word_count = len(self.content.split())
            # Assuming average reading speed of 200 words per minute
            self.read_time = max(1, word_count // 200)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.author.user_profile.user.email}"
    
    @property
    def author_name(self):
        """Get the author's full name"""
        user = self.author.user_profile.user
        return f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email
    
    @property
    def is_published(self):
        """Check if blog is published"""
        return self.status == self.StatusChoices.PUBLISHED and self.published_at is not None
    
    @property
    def tag_list(self):
        """Get tags as a comma-separated string"""
        return ', '.join(self.tags) if self.tags else ''


class BlogView(models.Model):
    """Model to track blog views"""
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='views')
    viewer_ip = models.GenericIPAddressField(help_text='IP address of the viewer')
    user_agent = models.TextField(blank=True, help_text='Browser user agent')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['blog', 'viewer_ip']  # Prevent duplicate views from same IP
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"View of '{self.blog.title}' from {self.viewer_ip}"
