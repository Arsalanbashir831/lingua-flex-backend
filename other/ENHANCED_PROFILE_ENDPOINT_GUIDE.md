# Enhanced Profile Endpoint Guide

## Overview
The student profile endpoint (`/accounts/profiles/me/`) has been enhanced to include additional user information: **role**, **profile picture**, and **created_at** timestamp in all responses.

## Endpoint Details

**URL:** `GET/PATCH/PUT /accounts/profiles/me/`

### Enhanced Response Structure

#### Before Enhancement:
```json
{
    "message": "Profile updated successfully",
    "profile": {
        "first_name": "Ching",
        "last_name": "Chang",
        "phone_number": "12345678905",
        "gender": "Male5",
        "date_of_birth": "2000-01-05",
        "bio": "I am a passionate language learner...",
        "city": "New York",
        "country": "United States",
        "postal_code": "10001",
        "status": "Active",
        "native_language": "English",
        "learning_language": "Spanish"
    }
}
```

#### After Enhancement:
```json
{
    "message": "Profile updated successfully",
    "profile": {
        "id": "user-uuid-string",
        "email": "ching.chang@example.com",
        "first_name": "Ching",
        "last_name": "Chang",
        "phone_number": "12345678905",
        "gender": "Male5",
        "date_of_birth": "2000-01-05",
        "role": "STUDENT",
        "profile_picture": "https://your-supabase-url.com/storage/v1/object/public/user-uploads/user_123/profile.jpg",
        "created_at": "2024-01-15T10:30:00Z",
        "bio": "I am a passionate language learner...",
        "city": "New York",
        "country": "United States",
        "postal_code": "10001",
        "status": "Active",
        "native_language": "English",
        "learning_language": "Spanish"
    }
}
```

## New Fields Added

### 1. **id** (string)
- **Description:** Unique identifier for the user
- **Format:** UUID string
- **Example:** `"550e8400-e29b-41d4-a716-446655440000"`
- **Source:** User model primary key
- **Always Present:** Yes

### 2. **email** (string)
- **Description:** User's email address
- **Format:** Valid email format
- **Example:** `"user@example.com"`
- **Source:** User model email field
- **Always Present:** Yes

### 3. **role** (string)
- **Description:** User's role in the system
- **Possible Values:** 
  - `"STUDENT"` - Regular student user
  - `"TEACHER"` - Teacher/instructor user
  - `"ADMIN"` - Administrator user
- **Source:** Fetched from the User model
- **Always Present:** Yes

### 4. **profile_picture** (string|null)
- **Description:** Full URL to the user's profile picture
- **Format:** Complete Supabase storage URL
- **Example:** `"https://yourproject.supabase.co/storage/v1/object/public/user-uploads/user_123/profile.jpg"`
- **Null Value:** `null` if no profile picture is set
- **Source:** Constructed from User model's profile_picture field

### 5. **created_at** (string)
- **Description:** Timestamp when the user account was created
- **Format:** ISO 8601 datetime string
- **Example:** `"2024-01-15T10:30:00Z"`
- **Source:** User model's created_at field
- **Always Present:** Yes

## API Usage Examples

### GET Request (Retrieve Profile)
```javascript
const getProfile = async () => {
    const response = await fetch('/accounts/profiles/me/', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        }
    });
    
    const data = await response.json();
    
    // Access new fields
    console.log('User ID:', data.id);
    console.log('User Email:', data.email);
    console.log('User Role:', data.role);
    console.log('Profile Picture:', data.profile_picture);
    console.log('Account Created:', data.created_at);
    
    // Use role for conditional UI
    if (data.role === 'TEACHER') {
        showTeacherFeatures();
    } else if (data.role === 'STUDENT') {
        showStudentFeatures();
    }
};
```

### PATCH Request (Update Profile)
```javascript
const updateProfile = async (profileData) => {
    const response = await fetch('/accounts/profiles/me/', {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileData)
    });
    
    const result = await response.json();
    
    // Enhanced response includes new fields
    const updatedProfile = result.profile;
    console.log('User ID:', updatedProfile.id);
    console.log('User Email:', updatedProfile.email);
    console.log('Updated profile with role:', updatedProfile.role);
    console.log('Profile picture URL:', updatedProfile.profile_picture);
    console.log('Account age:', new Date() - new Date(updatedProfile.created_at));
};
```

## Frontend Integration Examples

### React Component Example
```jsx
import React, { useState, useEffect } from 'react';

const ProfileComponent = () => {
    const [profile, setProfile] = useState(null);
    
    useEffect(() => {
        fetchProfile();
    }, []);
    
    const fetchProfile = async () => {
        const response = await fetch('/accounts/profiles/me/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        setProfile(data);
    };
    
    if (!profile) return <div>Loading...</div>;
    
    return (
        <div className="profile-card">
            <div className="profile-header">
                {profile.profile_picture ? (
                    <img src={profile.profile_picture} alt="Profile" />
                ) : (
                    <div className="default-avatar">
                        {profile.first_name?.[0]}{profile.last_name?.[0]}
                    </div>
                )}
                <h2>{profile.first_name} {profile.last_name}</h2>
                <span className={`role-badge ${profile.role.toLowerCase()}`}>
                    {profile.role}
                </span>
            </div>
            
            <div className="profile-details">
                <p>User ID: {profile.id}</p>
                <p>Email: {profile.email}</p>
                <p>Member since: {new Date(profile.created_at).toLocaleDateString()}</p>
                <p>Location: {profile.city}, {profile.country}</p>
                <p>Bio: {profile.bio}</p>
                
                {/* Role-specific content */}
                {profile.role === 'TEACHER' && (
                    <div className="teacher-info">
                        <p>Qualification: {profile.qualification}</p>
                        <p>Experience: {profile.experience_years} years</p>
                    </div>
                )}
                
                {profile.role === 'STUDENT' && (
                    <div className="student-info">
                        <p>Learning: {profile.learning_language}</p>
                        <p>Native: {profile.native_language}</p>
                    </div>
                )}
            </div>
        </div>
    );
};
```

## Postman Testing

### Test GET Request
1. **Method:** GET
2. **URL:** `{{base_url}}/accounts/profiles/me/`
3. **Headers:**
   - `Authorization: Bearer {{access_token}}`
4. **Expected Response:** Profile data with id, email, role, profile_picture, and created_at

### Test PATCH Request
1. **Method:** PATCH
2. **URL:** `{{base_url}}/accounts/profiles/me/`
3. **Headers:**
   - `Authorization: Bearer {{access_token}}`
   - `Content-Type: application/json`
4. **Body:**
   ```json
   {
       "first_name": "Updated Name",
       "bio": "Updated bio"
   }
   ```
5. **Expected Response:** Updated profile with all fields including new ones

## Validation and Testing

### Test Script Usage
Use the provided test script `test_profile_endpoint_enhanced.py`:

```bash
python test_profile_endpoint_enhanced.py
```

### Manual Testing Checklist
- [ ] GET request returns id, email, role, profile_picture, and created_at
- [ ] PATCH request response includes new fields
- [ ] PUT request response includes new fields
- [ ] Profile picture URL is correctly formatted
- [ ] Role values are correct (STUDENT/TEACHER/ADMIN)
- [ ] User ID and email are correctly displayed
- [ ] created_at timestamp is in correct ISO format
- [ ] Null profile_picture is handled gracefully

## Teacher Profile Endpoint

The teacher profile endpoint (`/accounts/teachers/my_profile/`) has also been enhanced with the same new fields for consistency.

## Error Handling

The endpoint maintains the same error responses as before, with enhanced profile data in successful responses only.

## Migration Notes

- **Backward Compatibility:** Existing API consumers will continue to work but will receive additional fields
- **Frontend Updates:** Update frontend code to utilize the new role, profile_picture, and created_at fields
- **Caching:** Update any caching mechanisms to include the new fields
- **Documentation:** Update API documentation to reflect the enhanced response structure

This enhancement provides immediate access to essential user information, eliminating the need for additional API calls to fetch user role and profile details.
