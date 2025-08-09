# 🎯 Comprehensive Teacher Profile Update - Testing Guide

## 📋 Updated Endpoint

**URL:** `PATCH {{base_url}}/accounts/teachers/my-profile/`

## 🔧 What Changed

✅ **Now Updates All Fields:**
- ✅ User model fields (first_name, last_name, phone_number, gender, date_of_birth)
- ✅ UserProfile fields (bio, city, country, postal_code, status, native_language, learning_language)  
- ✅ TeacherProfile fields (qualification, experience_years, certificates, about)

## 📝 Sample Request

**Headers:**
```
Authorization: Bearer YOUR_TEACHER_ACCESS_TOKEN
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "first_name": "first3",
    "last_name": "last3", 
    "phone_number": "12345678903",
    "gender": "Male3",
    "date_of_birth": "2000-01-03",
    "bio": "I am a passionate language learner interested in improving my communication skills.",
    "city": "New York",
    "country": "United States", 
    "postal_code": "10001",
    "status": "Active",
    "native_language": "English",
    "learning_language": "Spanish",
    "qualification": "Masters in Education and Science",
    "experience_years": 10,
    "certificates": [
        {
            "name": "TEFL Certificate",
            "issuing_organization": "Cambridge"
        },
        {
            "name": "TEFL Certificate2", 
            "issuing_organization": "Cambridge2"
        }
    ],
    "about": "Passionate about teaching languages and others"
}
```

## ✅ Expected Response

**Status:** `200 OK`

**Body:**
```json
{
    "message": "Profile updated successfully",
    "profile": {
        "first_name": "first3",
        "last_name": "last3",
        "phone_number": "12345678903", 
        "gender": "Male3",
        "date_of_birth": "2000-01-03",
        "bio": "I am a passionate language learner interested in improving my communication skills.",
        "city": "New York",
        "country": "United States",
        "postal_code": "10001", 
        "status": "Active",
        "native_language": "English",
        "learning_language": "Spanish",
        "qualification": "Masters in Education and Science",
        "experience_years": 10,
        "certificates": [
            {
                "name": "TEFL Certificate",
                "issuing_organization": "Cambridge"
            },
            {
                "name": "TEFL Certificate2",
                "issuing_organization": "Cambridge2"
            }
        ],
        "about": "Passionate about teaching languages and others"
    }
}
```

## 🎯 Key Features

1. **Partial Updates:** You can update any combination of fields
2. **Atomic Transactions:** All updates happen in one database transaction
3. **Comprehensive Response:** Returns all profile data after update
4. **Validation:** Proper validation for all field types

## 📝 Partial Update Examples

**Update only personal info:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "555-1234"
}
```

**Update only location:**
```json
{
    "city": "San Francisco", 
    "country": "USA",
    "postal_code": "94102"
}
```

**Update only teaching info:**
```json
{
    "qualification": "PhD in Linguistics",
    "experience_years": 15,
    "about": "Expert language instructor"
}
```

## 🔧 Testing Steps

1. **Login as Teacher** to get access token
2. **GET** the endpoint first to see current data
3. **PATCH** with your updates 
4. **Verify** all fields are updated correctly

## 🐛 Error Handling

**400 Bad Request** - Validation errors:
```json
{
    "field_name": ["Error message for this field"]
}
```

**404 Not Found** - No teacher profile:
```json
{
    "error": "Teacher profile not found. Make sure you are registered as a teacher."
}
```

**401 Unauthorized** - Invalid token:
```json
{
    "detail": "Authentication credentials were not provided."
}
```
