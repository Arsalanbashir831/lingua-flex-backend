# LinguaFlex - Simplified Registration API Documentation

## Overview
The registration system has been simplified to only require basic information during signup. Users can then update their role-specific profiles using dedicated endpoints.

## Authentication
All profile update endpoints require authentication using Bearer token in the Authorization header:
```
Authorization: Bearer <your_supabase_token>
```

## API Endpoints

### 1. User Registration (Simplified)

**POST** `/api/accounts/register/`

**Description:** Register a new user with minimal required information.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe",
    "role": "student"  // or "teacher"
}
```

**Response (Success - 201):**
```json
{
    "message": "Registration successful. Please verify your email.",
    "user_id": "uuid-string",
    "role": "student"
}
```

**Response (Error - 400):**
```json
{
    "error": "Error message"
}
```

---

### 2. Get User Profile

**GET** `/api/accounts/profile/me/`

**Description:** Get the current user's profile information.

**Headers:** `Authorization: Bearer <token>`

**Response (Success - 200):**
```json
{
    "id": 1,
    "user": {
        "id": "uuid-string",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "STUDENT"
    },
    "role": "student",
    "bio": "",
    "city": "",
    "country": "",
    "postal_code": "",
    "status": "",
    "native_language": "",
    "learning_language": "",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
}
```

---

### 3. Update Student Profile

**PUT/PATCH** `/api/accounts/profile/update-student/`

**Description:** Update student-specific profile information.

**Headers:** `Authorization: Bearer <token>`

**Request Body (all fields optional for PATCH):**
```json
{
    "bio": "I'm passionate about learning new languages",
    "city": "New York",
    "country": "USA",
    "postal_code": "10001",
    "status": "Learning Spanish and French",
    "native_language": "English",
    "learning_language": "Spanish"
}
```

**Response (Success - 200):**
```json
{
    "id": 1,
    "user": {
        "id": "uuid-string",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "STUDENT"
    },
    "role": "student",
    "bio": "I'm passionate about learning new languages",
    "city": "New York",
    "country": "USA",
    "postal_code": "10001",
    "status": "Learning Spanish and French",
    "native_language": "English",
    "learning_language": "Spanish",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
}
```

---

### 4. Get Teacher Profile

**GET** `/api/accounts/teacher/me/`

**Description:** Get the current teacher's profile information.

**Headers:** `Authorization: Bearer <token>`

**Note:** Only accessible by users with teacher role.

**Response (Success - 200):**
```json
{
    "id": 1,
    "user_profile": {
        "id": 1,
        "user": {
            "id": "uuid-string",
            "email": "teacher@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "role": "TEACHER"
        },
        "role": "teacher",
        "bio": "",
        "city": "",
        "country": "",
        "postal_code": "",
        "status": "",
        "native_language": "",
        "learning_language": "",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    },
    "qualification": "",
    "experience_years": 0,
    "certificates": [],
    "about": ""
}
```

---

### 5. Update Teacher Profile

**PUT/PATCH** `/api/accounts/teacher/update/`

**Description:** Update teacher-specific profile information including both user profile and teacher profile fields.

**Headers:** `Authorization: Bearer <token>`

**Note:** Only accessible by users with teacher role.

**Request Body (all fields optional for PATCH):**
```json
{
    // Teacher-specific fields
    "qualification": "Master's in English Literature, TESOL Certified",
    "experience_years": 5,
    "certificates": ["TESOL", "IELTS Examiner", "Business English Certificate"],
    "about": "Experienced English teacher specializing in business communication",
    
    // User profile fields (can be updated together)
    "bio": "Professional English teacher with 5 years of experience",
    "city": "London",
    "country": "UK",
    "postal_code": "SW1A 1AA",
    "status": "Available for new students",
    "native_language": "English",
    "learning_language": ""
}
```

**Response (Success - 200):**
```json
{
    "id": 1,
    "user_profile": {
        "id": 1,
        "user": {
            "id": "uuid-string",
            "email": "teacher@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "role": "TEACHER"
        },
        "role": "teacher",
        "bio": "Professional English teacher with 5 years of experience",
        "city": "London",
        "country": "UK",
        "postal_code": "SW1A 1AA",
        "status": "Available for new students",
        "native_language": "English",
        "learning_language": "",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    },
    "qualification": "Master's in English Literature, TESOL Certified",
    "experience_years": 5,
    "certificates": ["TESOL", "IELTS Examiner", "Business English Certificate"],
    "about": "Experienced English teacher specializing in business communication"
}
```

---

### 6. List All Teachers (Public)

**GET** `/api/accounts/teacher/list/`

**Description:** Get a list of all active teachers (public endpoint, no authentication required).

**Response (Success - 200):**
```json
[
    {
        "id": 1,
        "user_profile": {
            "id": 1,
            "user": {
                "id": "uuid-string",
                "email": "teacher@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "role": "TEACHER"
            },
            "role": "teacher",
            "bio": "Professional English teacher",
            "city": "London",
            "country": "UK"
        },
        "qualification": "Master's in English Literature",
        "experience_years": 5,
        "about": "Experienced English teacher"
    }
]
```

---

## Error Responses

### 400 Bad Request
```json
{
    "error": "Validation error message"
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "error": "Only teachers can access this endpoint"
}
```

### 404 Not Found
```json
{
    "error": "Profile not found"
}
```

---

## Usage Flow

### For Students:
1. **Register:** `POST /api/accounts/register/` with basic info
2. **Get Profile:** `GET /api/accounts/profile/me/` to see current profile
3. **Update Profile:** `PUT/PATCH /api/accounts/profile/update-student/` to add detailed information

### For Teachers:
1. **Register:** `POST /api/accounts/register/` with basic info and role="teacher"
2. **Get Profile:** `GET /api/accounts/teacher/me/` to see current teacher profile
3. **Update Profile:** `PUT/PATCH /api/accounts/teacher/update/` to add qualifications, experience, etc.

### For Browsing Teachers:
1. **List Teachers:** `GET /api/accounts/teacher/list/` to see all available teachers

---

## Implementation Notes

1. **Registration** creates minimal user and profile records
2. **Profile updates** are separate endpoints based on user role
3. **Teacher updates** can modify both user profile and teacher-specific fields in one request
4. **All fields** in update requests are optional when using PATCH method
5. **Full replacement** when using PUT method (all fields should be provided)
6. **Authentication** is handled through Supabase tokens
7. **Role validation** ensures users can only access appropriate endpoints
