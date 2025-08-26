# LinguaFlex Blog System - Postman Testing Guide

## 📦 Postman Collection Import

### 1. Import the Collection
1. Open **Postman**
2. Click **Import** button (top left)
3. Select **File** tab
4. Choose `LinguaFlex_Blog_System_API.postman_collection.json`
5. Click **Import**

### 2. Environment Setup (Optional but Recommended)
Create a new environment with these variables:
- `base_url`: `http://127.0.0.1:8000`
- `teacher_token`: (will be auto-set after login)
- `category_id`: (will be auto-set after category creation)
- `blog_id`: (will be auto-set after blog creation)

## 🚀 Testing Workflow

### Phase 1: Authentication & Setup

#### 1. **Teacher Login**
- **Purpose**: Get authentication token
- **Folder**: `Authentication → Teacher Login`
- **Action**: Update email/password in request body if needed
- **Result**: Sets `teacher_token` environment variable automatically

#### 2. **Create Category**
- **Purpose**: Create a blog category for testing
- **Folder**: `Blog Categories → Create Category`
- **Result**: Sets `category_id` environment variable

### Phase 2: Blog Management Testing

#### 3. **List Teacher Blogs**
- **Purpose**: View existing blogs (should be empty initially)
- **Folder**: `Blog Management (Teacher) → List Teacher Blogs`

#### 4. **Create Blog (JSON - No File)**
- **Purpose**: Test traditional blog creation with JSON
- **Features**: 
  - ✅ Creates blog with external thumbnail URL
  - ✅ Sets blog_id and blog_slug variables
- **Folder**: `Blog Management (Teacher) → Create Blog (JSON - No File)`

#### 5. **Create Blog with Thumbnail Upload** ⭐
- **Purpose**: Test single-endpoint file upload
- **Features**:
  - ✅ Upload image file during blog creation
  - ✅ Automatic thumbnail URL generation
  - ✅ Form-data request with mixed content
- **Folder**: `Blog Management (Teacher) → Create Blog with Thumbnail Upload`
- **Important**: Select an image file in the `thumbnail` field

#### 6. **Get Blog Details**
- **Purpose**: Retrieve specific blog information
- **Folder**: `Blog Management (Teacher) → Get Blog Details`

#### 7. **Update Blog with New Thumbnail**
- **Purpose**: Test thumbnail replacement during updates
- **Features**:
  - ✅ Upload new image to replace existing thumbnail
  - ✅ Update other blog fields simultaneously
- **Folder**: `Blog Management (Teacher) → Update Blog with New Thumbnail`

### Phase 3: Advanced Features

#### 8. **Search & Filter Tests**
Run these requests to test filtering capabilities:
- `Search Teacher Blogs` - Text search functionality
- `Filter Blogs by Category` - Category-based filtering
- `Filter Blogs by Date Range` - Date range filtering

#### 9. **Analytics & Stats**
- `Get Blog Statistics` - View comprehensive blog analytics
- `Duplicate Blog` - Create copy of existing blog
- `Bulk Update Blog Status` - Update multiple blogs at once

### Phase 4: Public Access Testing

#### 10. **Public Blog Access**
Test public endpoints (no authentication required):
- `List Public Blogs` - View published blogs
- `Search Public Blogs` - Public search functionality
- `Filter Public Blogs by Category` - Public filtering
- `Filter Public Blogs by Tags` - Tag-based filtering
- `View Blog by Slug` - Individual blog viewing (tracks analytics)

### Phase 5: Error Testing

#### 11. **Validation Tests**
- `Test Unauthorized Access` - Should return 401
- `Test Invalid Blog ID` - Should return 404
- `Test Invalid File Upload` - Should return 400 with validation error
- `Test Missing Required Fields` - Should return 400

### Phase 6: Legacy Upload Testing

#### 12. **Two-Step Upload Process**
Test the legacy separate upload method:
1. `Upload Thumbnail (Separate Endpoint)` - Upload file first
2. `Create Blog with Uploaded URL` - Create blog with returned URL

### Phase 7: Cleanup

#### 13. **Delete Test Data**
- `Delete Test Blog` - Remove created test blogs
- `Delete Duplicated Blog` - Clean up duplicated content

## 📋 File Upload Testing Guide

### For Single-Endpoint Upload (Recommended):

1. **Request**: `Create Blog with Thumbnail Upload`
2. **Body Type**: `form-data`
3. **Required Files**: 
   - Select an image file for `thumbnail` field
   - Supported: JPEG, PNG, WebP, GIF (max 5MB)

### Sample Test Images:
Create test images or download sample images:
- **Small image**: 400x300 pixels (~50KB)
- **Medium image**: 800x600 pixels (~200KB)
- **Large image**: 1920x1080 pixels (~500KB)

### File Upload Validation Tests:

#### ✅ **Valid File Tests**:
- Upload JPEG image ✅
- Upload PNG image ✅
- Upload WebP image ✅
- Upload GIF image ✅

#### ❌ **Invalid File Tests**:
- Upload .txt file → Should get 400 error
- Upload .pdf file → Should get 400 error
- Upload oversized image (>5MB) → Should get 400 error

## 🔍 What to Look For

### Successful Responses:

#### Blog Creation (201 Created):
```json
{
  "id": 1,
  "title": "Your Blog Title",
  "slug": "your-blog-title",
  "thumbnail": "https://supabase-url/storage/...",
  "category": {
    "id": 1,
    "name": "Education"
  },
  "status": "published",
  "created_at": "2025-08-19T...",
  "author": {
    "name": "Teacher Name"
  }
}
```

#### File Upload Success:
- `thumbnail` field contains Supabase URL
- URL format: `https://...supabase.../storage/v1/object/public/blog-images/blog_thumbnails/...`

### Error Responses:

#### File Validation (400 Bad Request):
```json
{
  "error": "Invalid thumbnail file type. Only JPEG, PNG, WebP, and GIF images are allowed"
}
```

#### Authentication Error (401 Unauthorized):
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## 🎯 Testing Checklist

### ✅ Core Functionality:
- [ ] Teacher login successful
- [ ] Category creation works
- [ ] Blog creation (JSON) works
- [ ] Blog creation with file upload works
- [ ] Blog update with new file works
- [ ] Blog retrieval works
- [ ] Blog deletion works

### ✅ File Upload Features:
- [ ] JPEG upload successful
- [ ] PNG upload successful
- [ ] Invalid file type rejected
- [ ] Large file rejected
- [ ] Thumbnail URL generated correctly
- [ ] Supabase storage working

### ✅ Search & Filter:
- [ ] Text search works
- [ ] Category filtering works
- [ ] Date range filtering works
- [ ] Tag filtering works

### ✅ Public Access:
- [ ] Public blog listing works
- [ ] Public blog viewing works
- [ ] View tracking works
- [ ] No authentication required

### ✅ Analytics:
- [ ] Blog statistics displayed
- [ ] View counts tracked
- [ ] Duplication works
- [ ] Bulk updates work

### ✅ Error Handling:
- [ ] Authentication errors handled
- [ ] Validation errors clear
- [ ] File upload errors descriptive
- [ ] Missing field errors shown

## 🛠️ Troubleshooting

### Common Issues:

#### 1. **Token Not Set**
- **Problem**: 401 errors on authenticated requests
- **Solution**: Run "Teacher Login" first, check environment variables

#### 2. **File Upload Fails**
- **Problem**: File upload returns error
- **Solutions**: 
  - Check file size (max 5MB)
  - Verify file type (image only)
  - Ensure Supabase credentials are configured

#### 3. **Category Not Found**
- **Problem**: 400 error when creating blogs
- **Solution**: Run "Create Category" first

#### 4. **Server Connection Error**
- **Problem**: Cannot connect to API
- **Solutions**:
  - Ensure Django server is running: `python manage.py runserver`
  - Check base_url is correct: `http://127.0.0.1:8000`

### Debug Tips:

1. **Check Environment Variables**: Ensure auto-set variables are populated
2. **View Response Details**: Check status codes and error messages
3. **Test Incrementally**: Run requests in order for dependencies
4. **File Selection**: Ensure you select actual image files for upload tests

## 🎉 Success Criteria

After running all tests, you should have:

- ✅ **Created blogs** with both JSON and file upload methods
- ✅ **Uploaded thumbnails** directly during blog creation
- ✅ **Updated blogs** with new thumbnail files
- ✅ **Tested all search/filter options**
- ✅ **Verified public access** works without authentication
- ✅ **Confirmed analytics** tracking and statistics
- ✅ **Validated error handling** for edge cases

The blog system is **production-ready** when all tests pass successfully! 🚀
