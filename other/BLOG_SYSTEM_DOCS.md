# Blog Management System Documentation

## Overview

The Blog Management System allows teachers to create, manage, and publish educational blog posts. Students and visitors can view published blogs without authentication. The system includes categorization, tagging, analytics, and SEO features.

## Features

### Core Features
- ✅ **Blog CRUD Operations** - Create, Read, Update, Delete blogs
- ✅ **Auto-generated Slugs** - SEO-friendly URLs
- ✅ **Categories & Tags** - Organize and filter content
- ✅ **Status Management** - Draft, Published, Archived
- ✅ **View Tracking** - Analytics for blog views
- ✅ **Read Time Calculation** - Automatic estimation
- ✅ **SEO Meta Description** - Search engine optimization
- ✅ **Teacher-only Access** - Only teachers can create/manage blogs
- ✅ **Public Reading** - Published blogs accessible to everyone

### Advanced Features
- ✅ **Bulk Operations** - Update multiple blogs at once
- ✅ **Blog Duplication** - Copy existing blogs
- ✅ **Statistics Dashboard** - View counts, status breakdown
- ✅ **Search & Filtering** - Find blogs by title, content, tags
- ✅ **Pagination** - Handle large numbers of blogs
- ✅ **Admin Interface** - Django admin integration

## Models

### Blog Model
```python
class Blog(models.Model):
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    content = models.TextField()
    thumbnail = models.CharField(max_length=500, blank=True, null=True)
    
    # Categorization
    category = models.ForeignKey(BlogCategory, ...)
    tags = models.JSONField(default=list, blank=True)
    
    # Status & Author
    status = models.CharField(max_length=20, choices=StatusChoices.choices)
    author = models.ForeignKey(TeacherProfile, ...)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # SEO & Analytics
    meta_description = models.CharField(max_length=160, blank=True)
    read_time = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
```

### BlogCategory Model
```python
class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### BlogView Model
```python
class BlogView(models.Model):
    blog = models.ForeignKey(Blog, ...)
    viewer_ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
```

## API Endpoints

### Teacher Blog Management (Requires Authentication)

#### List & Create Blogs
```
GET  /api/teacher/blogs/
POST /api/teacher/blogs/
```

**Query Parameters for GET:**
- `status` - Filter by status (draft, published, archived)
- `category` - Filter by category ID
- `search` - Search in title, content, tags
- `date_from` - Filter from date (YYYY-MM-DD)
- `date_to` - Filter to date (YYYY-MM-DD)
- `page` - Page number for pagination
- `page_size` - Number of items per page (max 50)

**POST Request Body (JSON):**
```json
{
    "title": "Your Blog Title",
    "content": "Detailed blog content here...",
    "thumbnail": "https://example.com/image.jpg",
    "category": 1,
    "tags": ["education", "language", "tips"],
    "status": "draft",
    "meta_description": "SEO description"
}
```

**POST Request Body (Form-data with File Upload):**
```
Content-Type: multipart/form-data

Fields:
- title: "Your Blog Title" (text)
- content: "Detailed blog content here..." (text)  
- thumbnail: image_file.jpg (file) - OPTIONAL
- category: 1 (text)
- tags: ["education", "language", "tips"] (text)
- status: "draft" (text)
- meta_description: "SEO description" (text)
```

**File Upload Requirements:**
- **Supported formats**: JPEG, PNG, WebP, GIF
- **Maximum size**: 5MB
- **Field name**: `thumbnail`
- **Storage**: Automatically uploaded to Supabase cloud storage
- **URL**: Automatically generated and included in response

#### Blog Detail Operations
```
GET    /api/teacher/blogs/{id}/     - Get specific blog
PUT    /api/teacher/blogs/{id}/     - Full update (supports file upload)
PATCH  /api/teacher/blogs/{id}/     - Partial update (supports file upload)
DELETE /api/teacher/blogs/{id}/     - Delete blog
```

**Update with File Upload:**
- Same form-data structure as creation
- Supports thumbnail file upload during updates
- Previous thumbnail is automatically replaced

#### Blog Statistics
```
GET /api/teacher/blogs/stats/
```

**Response:**
```json
{
    "total_blogs": 15,
    "published_blogs": 10,
    "draft_blogs": 4,
    "archived_blogs": 1,
    "total_views": 1250,
    "most_viewed_blog": "10 Tips for Learning Languages",
    "recent_blogs_count": 3
}
```

#### Advanced Operations
```
POST /api/teacher/blogs/{id}/duplicate/    - Duplicate blog
POST /api/teacher/blogs/bulk-update/       - Bulk status update
```

**Bulk Update Request:**
```json
{
    "blog_ids": [1, 2, 3],
    "status": "published"
}
```

#### Blog Thumbnail Upload
```
POST /api/teacher/blogs/upload-thumbnail/
```

**Content-Type:** `multipart/form-data`

**Form Data:**
- `thumbnail` - Image file (JPEG, PNG, WebP, GIF, max 5MB)

**Response:**
```json
{
    "message": "Thumbnail uploaded successfully",
    "thumbnail_url": "https://supabase-url/storage/v1/object/public/blog-images/...",
    "filename": "blog_thumbnails/user_id/uuid.jpg"
}
```

**Usage Workflow:**
1. Upload thumbnail image using this endpoint
2. Copy the returned `thumbnail_url`
3. Use the URL in blog creation/update requests

#### Blog Thumbnail Update (with Auto-Delete)
```
PATCH /api/teacher/blogs/{blog_id}/update-thumbnail/
```

**Content-Type:** `multipart/form-data`

**Form Data:**
- `thumbnail` - New image file (JPEG, PNG, WebP, GIF, max 5MB)

**Response:**
```json
{
    "message": "Thumbnail updated successfully",
    "blog_id": 1,
    "old_thumbnail_url": "https://supabase-url/.../old-thumbnail.jpg",
    "new_thumbnail_url": "https://supabase-url/.../new-thumbnail.jpg",
    "old_thumbnail_deleted": true,
    "filename": "blog_thumbnails/user_id/new-uuid.jpg"
}
```

**Features:**
- ✅ Automatically deletes previous thumbnail from Supabase storage
- ✅ Uploads new thumbnail with unique filename
- ✅ Updates blog record with new thumbnail URL
- ✅ Returns detailed response with old/new URLs
- ✅ Prevents storage bloat from unused files

**Usage:**
1. Get blog ID from existing blog
2. Send PATCH request with new thumbnail file
3. Previous thumbnail automatically deleted
4. Blog updated with new thumbnail URL

### Public Blog Access (No Authentication)

#### List Published Blogs
```
GET /api/blogs/
```

**Query Parameters:**
- `search` - Search in title, content, tags
- `category` - Filter by category ID
- `tags` - Filter by tags (comma-separated)
- `page` - Page number
- `page_size` - Items per page

#### View Specific Blog
```
GET /api/blogs/{slug}/
```

This endpoint also tracks views for analytics.

### Categories

#### List & Create Categories
```
GET  /api/categories/     - List all categories (public)
POST /api/categories/     - Create category (teachers only)
```

## Usage Examples

### Creating a Blog

```javascript
// JavaScript/Frontend example
const createBlog = async (blogData, authToken) => {
    const response = await fetch('/api/teacher/blogs/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(blogData)
    });
    
    if (response.ok) {
        const blog = await response.json();
        console.log('Blog created:', blog.title);
        return blog;
    } else {
        const error = await response.json();
        console.error('Error:', error);
    }
};

// Usage
const blogData = {
    title: "10 Tips for Effective Language Learning",
    content: "Here are proven strategies...",
    category: 1,
    tags: ["education", "language", "tips"],
    status: "published"
};

createBlog(blogData, userToken);
```

### Fetching Public Blogs

```javascript
// Fetch published blogs (no auth required)
const fetchPublicBlogs = async (filters = {}) => {
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/blogs/?${params}`);
    
    if (response.ok) {
        const data = await response.json();
        return data.results; // Array of blogs
    }
    return [];
};

// Usage
const blogs = await fetchPublicBlogs({
    search: 'language learning',
    category: 1,
    page: 1
});
```

### Python Client Example

```python
import requests

class BlogClient:
    def __init__(self, base_url, auth_token=None):
        self.base_url = base_url
        self.headers = {}
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
    
    def create_blog(self, blog_data):
        response = requests.post(
            f'{self.base_url}/api/teacher/blogs/',
            json=blog_data,
            headers=self.headers
        )
        return response.json()
    
    def get_public_blogs(self, **filters):
        response = requests.get(
            f'{self.base_url}/api/blogs/',
            params=filters
        )
        return response.json()
    
    def get_blog_stats(self):
        response = requests.get(
            f'{self.base_url}/api/teacher/blogs/stats/',
            headers=self.headers
        )
        return response.json()

# Usage
client = BlogClient('http://localhost:8000', 'your-token-here')

# Create blog
blog = client.create_blog({
    'title': 'My First Blog',
    'content': 'Blog content here...',
    'tags': ['education'],
    'status': 'published'
})

# Get stats
stats = client.get_blog_stats()
print(f"Total blogs: {stats['total_blogs']}")
```

## Status Workflow

```
Draft → Published → Archived
  ↓        ↓         ↑
  └── Published ────┘
```

- **Draft**: Blog is being worked on, not visible to public
- **Published**: Blog is live and visible to everyone
- **Archived**: Blog is hidden but preserved for reference

## Features in Detail

### Auto-generated Slugs
- Slugs are automatically created from blog titles
- Duplicates are handled with numbered suffixes
- Custom slugs can be set if needed

### View Tracking
- Each unique IP view is counted once per blog
- View counts are updated in real-time
- Analytics help teachers understand content performance

### SEO Features
- Meta descriptions for search engines
- Slug-based URLs for better SEO
- Structured data for better indexing

### Security
- Only authenticated teachers can create/manage blogs
- Teachers can only access their own blogs
- Public endpoints are read-only

## Admin Interface

The Django admin provides a full management interface:

- **Blog Management**: Create, edit, delete blogs
- **Category Management**: Organize blog categories
- **View Analytics**: Monitor blog performance
- **Bulk Operations**: Manage multiple blogs at once

Access at: `/admin/blogs/`

## Installation & Setup

1. **App is already created and configured**
2. **Migrations have been applied**
3. **URLs are configured**
4. **Admin is registered**

## Testing

Use the provided test scripts:

### Blog CRUD & Analytics Testing
```bash
python test_blogs_api.py
```

### Blog Creation with Thumbnail Upload Testing
```bash
python test_blog_creation_with_thumbnail.py
```

### Separate Thumbnail Upload Testing (Legacy)
```bash
python test_blog_thumbnail_upload.py
```

Update the teacher credentials in the scripts before running tests.

### Postman Testing for Blog Creation with Thumbnail

**Recommended Method (Single Request):**

1. **Create Blog with Thumbnail:**
   - Method: POST
   - URL: `http://127.0.0.1:8000/api/blogs/teacher/blogs/`
   - Headers: `Authorization: Token YOUR_TOKEN`
   - Body: form-data
     - title: "My Blog Title" (text)
     - content: "Blog content..." (text)
     - thumbnail: select_image_file.jpg (file)
     - category: 1 (text)
     - tags: ["tag1", "tag2"] (text)
     - status: "published" (text)

2. **Response:**
   ```json
   {
     "id": 1,
     "title": "My Blog Title",
     "thumbnail": "https://supabase-url/storage/...",
     "status": "published",
     ...
   }
   ```

### Legacy Method (Two-Step Process)

1. **Upload Thumbnail:**
   - Method: POST
   - URL: `http://127.0.0.1:8000/api/blogs/teacher/blogs/upload-thumbnail/`
   - Headers: `Authorization: Token YOUR_TOKEN`
   - Body: form-data with key `thumbnail` (file type)
   - Select image file (JPEG, PNG, WebP, GIF, max 5MB)

2. **Copy Response URL:**
   ```json
   {
     "thumbnail_url": "https://supabase-url/...",
     "filename": "blog_thumbnails/..."
   }
   ```

3. **Create Blog with Uploaded Thumbnail:**
   - Method: POST
   - URL: `http://127.0.0.1:8000/api/blogs/teacher/blogs/`
   - Body: JSON with `thumbnail` field using the uploaded URL

## Future Enhancements

Potential features for future development:

- 📝 **Rich Text Editor**: WYSIWYG content editing
- ✅ **Image Upload**: ✅ COMPLETED - Direct image upload for thumbnails
- 💬 **Comments System**: Reader engagement
- 👍 **Like/Rating System**: Content feedback
- 🔗 **Social Sharing**: Share buttons
- 📧 **Email Notifications**: Notify followers of new posts
- 🏷️ **Tag Suggestions**: Auto-suggest popular tags
- 📊 **Advanced Analytics**: Detailed view statistics
- 🔍 **Full-Text Search**: Enhanced search capabilities
- 📱 **Mobile Optimization**: Better mobile experience

## Support

For issues or questions:
1. Check the test scripts for examples (`test_blogs_api.py`, `test_blog_thumbnail_upload.py`)
2. Review the API documentation above
3. Check Django admin for data management
4. Ensure proper authentication for teacher endpoints
5. Verify Supabase storage bucket "blog-images" exists for file uploads

The blog system is now fully functional with file upload capabilities and ready for production use!
