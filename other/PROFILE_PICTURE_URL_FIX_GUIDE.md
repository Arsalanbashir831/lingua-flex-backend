# Profile Picture URL Fix Guide

## Issue Description
The profile picture upload endpoint was returning local file paths instead of proper Supabase URLs, causing invalid profile picture URLs in API responses.

**Before Fix:**
```json
{
    "profile_picture": "/media/user_a6e13d11-9bd4-4561-9e0b-0d199670d49e/Screenshot%202025-07-11%20175532.png"
}
```

**After Fix:**
```json
{
    "profile_picture": "https://your-project.supabase.co/storage/v1/object/public/user-uploads/user_a6e13d11-9bd4-4561-9e0b-0d199670d49e/Screenshot%202025-07-11%20175532.png"
}
```

## Solution Implemented

### Modified UserSerializer
Updated `core/serializers.py` to properly construct Supabase URLs for profile pictures:

```python
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip()
    
    def get_profile_picture(self, obj):
        """Return proper Supabase URL for profile picture"""
        if not obj.profile_picture:
            return None
        
        from django.conf import settings
        supabase_url = settings.SUPABASE_URL
        bucket_name = "user-uploads"
        
        # Construct full Supabase URL
        return f"{supabase_url}/storage/v1/object/public/{bucket_name}/{obj.profile_picture}"
```

## Affected Endpoints

### 1. Profile Picture Upload
**Endpoint:** `POST /user/profile-picture/`

**Before Fix Response:**
```json
{
    "id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture": "/media/user_a6e13d11-9bd4-4561-9e0b-0d199670d49e/image.png",
    "created_at": "2025-08-06T09:18:04.851891Z"
}
```

**After Fix Response:**
```json
{
    "id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture": "https://your-project.supabase.co/storage/v1/object/public/user-uploads/user_a6e13d11-9bd4-4561-9e0b-0d199670d49e/image.png",
    "created_at": "2025-08-06T09:18:04.851891Z"
}
```

### 2. Profile Picture Get
**Endpoint:** `GET /user/profile-picture/get/`

Now returns consistent Supabase URLs.

### 3. User Profile Endpoints
**Endpoints:** 
- `GET /user/profile/`
- `PATCH /user/profile/`
- `GET /accounts/profiles/me/`
- `PATCH /accounts/profiles/me/`

All user profile endpoints now return proper Supabase URLs for profile pictures.

## URL Format

### Supabase Storage URL Structure
```
https://{supabase_project_url}/storage/v1/object/public/{bucket_name}/{file_path}
```

### Components:
- **supabase_project_url**: Your Supabase project URL from settings
- **bucket_name**: `user-uploads` (the storage bucket)
- **file_path**: `user_{user_id}/{filename}` (the storage key)

### Example:
```
https://abcdefg.supabase.co/storage/v1/object/public/user-uploads/user_a6e13d11-9bd4-4561-9e0b-0d199670d49e/profile.jpg
```

## Testing

### Manual Testing Steps

1. **Upload Profile Picture:**
   ```bash
   curl -X POST "http://localhost:8000/user/profile-picture/" \
        -H "Authorization: Bearer {your_token}" \
        -F "profile_picture=@/path/to/image.jpg"
   ```

2. **Verify Response:**
   - Check that `profile_picture` field contains a full Supabase URL
   - URL should be accessible in browser
   - URL should start with your Supabase project URL

3. **Test Profile Endpoints:**
   ```bash
   curl -X GET "http://localhost:8000/accounts/profiles/me/" \
        -H "Authorization: Bearer {your_token}"
   ```

### Expected Behavior

✅ **Correct Profile Picture URL:**
- Starts with `https://`
- Contains your Supabase project domain
- Includes `/storage/v1/object/public/user-uploads/`
- Ends with the actual filename

❌ **Incorrect Profile Picture URL:**
- Starts with `/media/` (local path)
- Contains file system paths
- Not accessible via HTTP

## Validation Script

Use the provided test script `test_profile_picture_urls.py`:

```bash
python test_profile_picture_urls.py
```

This script will:
1. Test the profile picture GET endpoint
2. Validate URL format
3. Provide instructions for upload testing

## Frontend Integration

### JavaScript Example
```javascript
const uploadProfilePicture = async (file) => {
    const formData = new FormData();
    formData.append('profile_picture', file);
    
    const response = await fetch('/user/profile-picture/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        },
        body: formData
    });
    
    const data = await response.json();
    
    // Profile picture URL is now a valid Supabase URL
    console.log('Profile picture URL:', data.profile_picture);
    
    // Can be used directly in img src
    const imgElement = document.getElementById('profile-img');
    imgElement.src = data.profile_picture;
};
```

### React Example
```jsx
const ProfilePicture = ({ user }) => {
    return (
        <img 
            src={user.profile_picture || '/default-avatar.png'} 
            alt="Profile"
            onError={(e) => {
                e.target.src = '/default-avatar.png';
            }}
        />
    );
};
```

## Benefits of the Fix

1. **Direct Access**: Profile picture URLs are directly accessible
2. **CDN Performance**: Leverages Supabase's CDN for fast image delivery
3. **Consistency**: All profile picture URLs follow the same format
4. **Frontend Friendly**: URLs can be used directly in `<img>` tags
5. **Cross-Platform**: URLs work across web, mobile, and other clients

## Troubleshooting

### If Profile Pictures Still Show Local Paths:
1. Restart your Django server
2. Clear any caches
3. Verify settings.SUPABASE_URL is correctly configured
4. Check that the UserSerializer is being used in all relevant endpoints

### If URLs Return 404:
1. Verify Supabase storage bucket permissions
2. Check that files were uploaded correctly
3. Ensure bucket name matches (`user-uploads`)
4. Verify Supabase project URL is correct

The profile picture URL issue has been resolved, and all endpoints now return proper, accessible Supabase URLs.
