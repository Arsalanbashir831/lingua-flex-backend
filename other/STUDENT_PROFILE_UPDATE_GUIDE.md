# 🎯 Comprehensive Student Profile Update - Testing Guide

## 📋 Updated Endpoint

**URL:** `PATCH {{base_url}}/accounts/profiles/me/`

## 🔧 What Changed

✅ **Now Updates All Fields:**
- ✅ User model fields (first_name, last_name, phone_number, gender, date_of_birth)
- ✅ UserProfile fields (bio, city, country, postal_code, status, native_language, learning_language)

## 📝 Sample Request

**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
    "first_name": "Ching",
    "last_name": "Chang", 
    "phone_number": "12345678905",
    "gender": "Male5",
    "date_of_birth": "2000-01-05",
    "bio": "I am a passionate language learner interested in improving my communication skills.",
    "city": "New York",
    "country": "United States", 
    "postal_code": "10001",
    "status": "Active",
    "native_language": "English",
    "learning_language": "Spanish"
}
```

## ✅ Expected Response

**Status:** `200 OK`

**Body:**
```json
{
    "message": "Profile updated successfully",
    "profile": {
        "first_name": "Ching",
        "last_name": "Chang",
        "phone_number": "12345678905", 
        "gender": "Male5",
        "date_of_birth": "2000-01-05",
        "bio": "I am a passionate language learner interested in improving my communication skills.",
        "city": "New York",
        "country": "United States",
        "postal_code": "10001", 
        "status": "Active",
        "native_language": "English",
        "learning_language": "Spanish"
    }
}
```

## 🎯 Key Features

1. **Partial Updates:** You can update any combination of fields
2. **Atomic Transactions:** All updates happen in one database transaction
3. **Comprehensive Response:** Returns all profile data after update
4. **Validation:** Proper validation for all field types
5. **Works for Students:** Specifically designed for student profile updates

## 📝 Partial Update Examples

**Update only personal info:**
```json
{
    "first_name": "Jane",
    "last_name": "Smith",
    "phone_number": "555-9876"
}
```

**Update only location:**
```json
{
    "city": "Los Angeles", 
    "country": "USA",
    "postal_code": "90210"
}
```

**Update only language preferences:**
```json
{
    "native_language": "Spanish",
    "learning_language": "French",
    "bio": "Excited to learn new languages!"
}
```

## 🔧 HTTP Methods Supported

### **GET** - Retrieve Current Profile
**URL:** `GET {{base_url}}/accounts/profiles/me/`
**Response:** All current profile data

### **PATCH** - Partial Update
**URL:** `PATCH {{base_url}}/accounts/profiles/me/`
**Body:** Only the fields you want to update

### **PUT** - Full Update
**URL:** `PUT {{base_url}}/accounts/profiles/me/`
**Body:** All fields (recommended to use PATCH instead)

## 🔧 Testing Steps

1. **Login as Student** to get access token
2. **GET** the endpoint first to see current data
3. **PATCH** with your updates 
4. **Verify** all fields are updated correctly

## 🆚 Comparison with Teacher Endpoint

| Feature | Student Endpoint | Teacher Endpoint |
|---------|------------------|------------------|
| URL | `/accounts/profiles/me/` | `/accounts/teachers/my-profile/` |
| User Fields | ✅ All supported | ✅ All supported |
| Profile Fields | ✅ UserProfile only | ✅ UserProfile + TeacherProfile |
| Methods | GET, PATCH, PUT | GET, PATCH |
| Auth Required | Student token | Teacher token |

## 🐛 Error Handling

**400 Bad Request** - Validation errors:
```json
{
    "field_name": ["Error message for this field"]
}
```

**404 Not Found** - No user profile:
```json
{
    "detail": "Not found."
}
```

**401 Unauthorized** - Invalid token:
```json
{
    "detail": "Authentication credentials were not provided."
}
```

## 🎯 Complete Testing Flow

### Step 1: Get Current Profile
```http
GET {{base_url}}/accounts/profiles/me/
Authorization: Bearer YOUR_STUDENT_TOKEN
```

### Step 2: Update All Fields
```http
PATCH {{base_url}}/accounts/profiles/me/
Authorization: Bearer YOUR_STUDENT_TOKEN
Content-Type: application/json

{
    "first_name": "Ching",
    "last_name": "Chang",
    "phone_number": "12345678905",
    "gender": "Male5", 
    "date_of_birth": "2000-01-05",
    "bio": "I am a passionate language learner interested in improving my communication skills.",
    "city": "New York",
    "country": "United States",
    "postal_code": "10001",
    "status": "Active",
    "native_language": "English",
    "learning_language": "Spanish"
}
```

### Step 3: Verify Update
```http
GET {{base_url}}/accounts/profiles/me/
Authorization: Bearer YOUR_STUDENT_TOKEN
```

## 🚀 Ready to Test!

Your student profile endpoint now supports comprehensive updates just like the teacher endpoint. Test it in Postman with the sample data above! 🎉
