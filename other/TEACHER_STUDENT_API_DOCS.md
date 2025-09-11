# Teacher Student Management API Documentation

## Overview
This API provides endpoints for teachers to access and manage student information. Teachers can view all students, get detailed information about specific students, and access comprehensive statistics about the student population.

## Base URL
```
http://localhost:8000/api/accounts/
```

## Authentication
All endpoints require teacher authentication using Bearer token:
```
Authorization: Bearer YOUR_TEACHER_TOKEN
```

**Note**: Only users with teacher profiles can access these endpoints. Students and non-authenticated users will receive a 403 Forbidden response.

---

## 📚 Endpoints

### 1. Get All Students
**Endpoint**: `GET /teacher/students/`  
**Description**: Retrieve a paginated list of all students with filtering, searching, and sorting capabilities.

#### Query Parameters:
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `page` | integer | Page number for pagination | `?page=2` |
| `page_size` | integer | Number of results per page (max 100) | `?page_size=20` |
| `country` | string | Filter by student's country | `?country=Pakistan` |
| `city` | string | Filter by student's city | `?city=Karachi` |
| `native_language` | string | Filter by native language | `?native_language=Urdu` |
| `learning_language` | string | Filter by learning language | `?learning_language=English` |
| `status` | string | Filter by student status | `?status=active` |
| `gender` | string | Filter by gender | `?gender=male` |
| `age_min` | integer | Minimum age filter | `?age_min=18` |
| `age_max` | integer | Maximum age filter | `?age_max=30` |
| `date_from` | date | Filter by registration date from | `?date_from=2024-01-01` |
| `date_to` | date | Filter by registration date to | `?date_to=2024-12-31` |
| `search` | string | Search across multiple fields | `?search=john` |
| `sort_by` | string | Sort field | `?sort_by=-created_at` |

#### Sorting Options:
- `created_at` / `-created_at` - Registration date (ascending/descending)
- `user__first_name` / `-user__first_name` - First name
- `user__last_name` / `-user__last_name` - Last name
- `user__email` / `-user__email` - Email
- `country` / `-country` - Country
- `city` / `-city` - City
- `native_language` / `-native_language` - Native language
- `learning_language` / `-learning_language` - Learning language

#### Example Request:
```bash
GET /api/accounts/teacher/students/?country=Pakistan&learning_language=English&page=1&page_size=10&sort_by=-created_at
```

#### Example Response:
```json
{
  "count": 156,
  "next": "http://localhost:8000/api/accounts/teacher/students/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": "uuid-123",
        "email": "student@example.com",
        "first_name": "Ahmed",
        "last_name": "Khan",
        "phone_number": "+92300123456",
        "gender": "male",
        "date_of_birth": "1995-05-15",
        "profile_picture": null
      },
      "role": "STUDENT",
      "bio": "Passionate language learner",
      "city": "Karachi",
      "country": "Pakistan",
      "postal_code": "75500",
      "status": "active",
      "native_language": "Urdu",
      "learning_language": "English",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-20T15:45:00Z"
    }
  ],
  "statistics": {
    "total_students": 156,
    "top_countries": [
      {"country": "Pakistan", "count": 45},
      {"country": "India", "count": 32}
    ],
    "top_native_languages": [
      {"native_language": "Urdu", "count": 40},
      {"native_language": "Hindi", "count": 30}
    ],
    "top_learning_languages": [
      {"learning_language": "English", "count": 80},
      {"learning_language": "French", "count": 25}
    ]
  }
}
```

---

### 2. Get Student Details by ID
**Endpoint**: `GET /teacher/students/{student_id}/`  
**Description**: Retrieve detailed information about a specific student.

#### Path Parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `student_id` | string | The user ID of the student |

#### Example Request:
```bash
GET /api/accounts/teacher/students/uuid-123-456/
```

#### Example Response:
```json
{
  "id": 1,
  "user": {
    "id": "uuid-123-456",
    "email": "student@example.com",
    "first_name": "Ahmed",
    "last_name": "Khan",
    "phone_number": "+92300123456",
    "gender": "male",
    "date_of_birth": "1995-05-15",
    "profile_picture": null
  },
  "role": "STUDENT",
  "bio": "Passionate language learner interested in improving English communication skills",
  "city": "Karachi",
  "country": "Pakistan",
  "postal_code": "75500",
  "status": "active",
  "native_language": "Urdu",
  "learning_language": "English",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:45:00Z",
  "calculated_age": 29,
  "account_info": {
    "is_active": true,
    "last_login": "2024-01-25T08:30:00Z",
    "account_created": "2024-01-15T10:30:00Z",
    "profile_completed": true
  }
}
```

---

### 3. Get Student Statistics
**Endpoint**: `GET /teacher/students-statistics/`  
**Description**: Get comprehensive statistics about all students in the platform.

#### Example Request:
```bash
GET /api/accounts/teacher/students-statistics/
```

#### Example Response:
```json
{
  "summary": {
    "total_students": 156,
    "active_students": 142,
    "inactive_students": 14,
    "recent_registrations_30_days": 23,
    "profile_completion_rate": 87.18
  },
  "demographics": {
    "countries": [
      {"country": "Pakistan", "count": 45},
      {"country": "India", "count": 32},
      {"country": "Bangladesh", "count": 28},
      {"country": "United States", "count": 15},
      {"country": "United Kingdom", "count": 12}
    ],
    "genders": [
      {"user__gender": "male", "count": 78},
      {"user__gender": "female", "count": 65},
      {"user__gender": "other", "count": 8},
      {"user__gender": null, "count": 5}
    ]
  },
  "languages": {
    "native_languages": [
      {"native_language": "Urdu", "count": 45},
      {"native_language": "Hindi", "count": 32},
      {"native_language": "Bengali", "count": 28},
      {"native_language": "English", "count": 20},
      {"native_language": "Arabic", "count": 15}
    ],
    "learning_languages": [
      {"learning_language": "English", "count": 89},
      {"learning_language": "French", "count": 25},
      {"learning_language": "Spanish", "count": 18},
      {"learning_language": "German", "count": 12},
      {"learning_language": "Chinese", "count": 8}
    ]
  },
  "profiles": {
    "complete_profiles": 136,
    "incomplete_profiles": 20,
    "completion_percentage": 87.18
  }
}
```

---

## 🔍 Search Functionality

The search parameter (`?search=query`) searches across multiple fields:
- First name
- Last name
- Email
- Username
- Bio
- City
- Country
- Native language
- Learning language

**Example**: `?search=ahmed` will find students with "ahmed" in any of these fields.

---

## 📊 Filtering Examples

### Multiple Filters
```bash
GET /teacher/students/?country=Pakistan&learning_language=English&gender=male&age_min=20&age_max=35
```

### Search with Filters
```bash
GET /teacher/students/?search=karachi&native_language=Urdu&sort_by=user__first_name
```

### Date Range with Pagination
```bash
GET /teacher/students/?date_from=2024-01-01&date_to=2024-06-30&page=1&page_size=25
```

---

## 🚫 Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden (Non-teacher user)
```json
{
  "error": "Only teachers can access student statistics"
}
```

### 404 Not Found (Student detail)
```json
{
  "detail": "Not found."
}
```

---

## 📱 Use Cases

### 1. **Student Discovery for Teachers**
Teachers can find students based on:
- Location (country/city)
- Language preferences (native/learning languages)
- Demographics (age, gender)
- Activity status

### 2. **Student Analytics**
- Monitor student registration trends
- Analyze language learning patterns
- Track profile completion rates
- Understand geographical distribution

### 3. **Targeted Teaching**
- Find students learning specific languages
- Connect with students from specific regions
- Identify active vs inactive students

### 4. **Platform Insights**
- Understand user demographics
- Monitor platform growth
- Analyze language demand

---

## 🔧 Implementation Notes

1. **Authentication**: Uses Supabase token authentication
2. **Permissions**: Only teachers can access these endpoints
3. **Pagination**: Default page size is 20, maximum is 100
4. **Performance**: Queries are optimized with select_related()
5. **Statistics**: Real-time calculation of statistics
6. **Age Calculation**: Based on date_of_birth field
7. **Profile Completion**: Checks for required fields completion

---

## 🧪 Testing

Use the provided test script:
```bash
python test_teacher_student_endpoints.py
```

Make sure to update the script with:
- Valid teacher authentication token
- Valid student ID for detail testing

---

## 🌟 Key Features

- ✅ **Comprehensive Filtering** - Multiple filter options
- ✅ **Smart Search** - Searches across multiple fields
- ✅ **Flexible Sorting** - Sort by various fields
- ✅ **Pagination** - Efficient data loading
- ✅ **Real-time Statistics** - Live data analytics
- ✅ **Detailed Student Profiles** - Complete student information
- ✅ **Security** - Teacher-only access control
- ✅ **Performance Optimized** - Efficient database queries

This API provides teachers with powerful tools to discover, analyze, and understand their potential student base on the LinguaFlex platform!
