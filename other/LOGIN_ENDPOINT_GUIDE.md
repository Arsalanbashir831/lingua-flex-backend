# Login Endpoint Guide

## Overview
The login endpoint has been enhanced to include the user's role (student, teacher, or admin) in the response. This allows frontend applications to handle role-based navigation and features immediately after login.

## Endpoint Details

**URL:** `POST /api/auth/login/`

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "userpassword"
}
```

**Enhanced Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
        "email": "user@example.com",
        "id": "user-uuid-here",
        "role": "STUDENT"
    }
}
```

## User Roles

The `role` field can have the following values:
- `STUDENT` - Regular student user
- `TEACHER` - Teacher/instructor user  
- `ADMIN` - Administrator user

## Frontend Usage Examples

### JavaScript/React Example
```javascript
const login = async (email, password) => {
    try {
        const response = await fetch('http://localhost:8000/api/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store tokens
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            
            // Handle role-based navigation
            const userRole = data.user.role;
            switch(userRole) {
                case 'STUDENT':
                    window.location.href = '/student-dashboard';
                    break;
                case 'TEACHER':
                    window.location.href = '/teacher-dashboard';
                    break;
                case 'ADMIN':
                    window.location.href = '/admin-dashboard';
                    break;
                default:
                    window.location.href = '/dashboard';
            }
        }
    } catch (error) {
        console.error('Login failed:', error);
    }
};
```

### Python/Requests Example
```python
import requests

def login_user(email, password):
    url = "http://localhost:8000/api/auth/login/"
    data = {"email": email, "password": password}
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        
        # Extract user info
        user_role = result['user']['role']
        user_email = result['user']['email']
        access_token = result['access_token']
        
        print(f"Login successful for {user_email} with role: {user_role}")
        return result
    else:
        print(f"Login failed: {response.text}")
        return None
```

## Postman Testing

### Request Setup
1. **Method:** POST
2. **URL:** `http://localhost:8000/api/auth/login/`
3. **Headers:**
   - `Content-Type: application/json`
4. **Body (raw JSON):**
   ```json
   {
       "email": "your-test-email@example.com",
       "password": "your-test-password"
   }
   ```

### Expected Response
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "email": "your-test-email@example.com",
        "id": "uuid-string",
        "role": "STUDENT"
    }
}
```

## Error Responses

### Invalid Credentials
**Status:** 401 Unauthorized
```json
{
    "error": "Invalid login credentials."
}
```

### Missing Fields
**Status:** 400 Bad Request
```json
{
    "error": "Email and password are required."
}
```

### Server Error
**Status:** 400 Bad Request
```json
{
    "error": "Failed to login. [error details]"
}
```

## Implementation Notes

1. **Role Source:** The role is fetched from the Django User model stored in the local database
2. **Default Role:** If a user doesn't exist in the Django database, the role defaults to "STUDENT"
3. **Token Integration:** The access token contains user information that can be decoded on the frontend
4. **Security:** The role is included in the response but should also be verified server-side for sensitive operations

## Testing Your Implementation

Use the provided test script `test_login_with_role.py`:

```bash
python test_login_with_role.py
```

Make sure to:
1. Update the test credentials with actual user data
2. Ensure your Django server is running on port 8000
3. Verify the response includes the user role

## Integration with Other Endpoints

With the role information available immediately after login, you can:

1. **Navigate to Role-Specific Dashboards:** Direct users to appropriate interfaces
2. **Show/Hide UI Elements:** Based on user permissions
3. **Make Role-Specific API Calls:** Use the role to determine which endpoints to call
4. **Cache User Role:** Store role info for offline functionality

This enhancement provides a seamless user experience with immediate role-based customization after authentication.
