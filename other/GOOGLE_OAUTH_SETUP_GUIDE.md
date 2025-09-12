# 🚀 Google OAuth Authentication Setup Guide

## Overview
This guide covers the complete setup and implementation of Google OAuth authentication for LinguaFlex, allowing users to register and login with their Google accounts while selecting their role (Student/Teacher).

## ✅ **Implementation Status: COMPLETE**

### **What's Been Implemented:**
- ✅ **Database Schema**: OAuth fields added to User model
- ✅ **Backend Views**: Complete OAuth flow endpoints
- ✅ **Serializers**: Data validation and formatting
- ✅ **URL Configuration**: OAuth endpoints mapped
- ✅ **Database Migration**: Schema updated successfully
- ✅ **Test Scripts**: OAuth flow testing

## **Architecture Overview**

```
Frontend Selection    Backend Processing    Supabase OAuth    Google OAuth
      ↓                      ↓                   ↓               ↓
[Role: STUDENT]         [OAuth Initiate]    [Generate URL]   [User Consent]
[Google Button]    →    [/auth/google/]  →  [OAuth Flow]  →  [Profile Data]
      ↓                      ↓                   ↓               ↓
[Redirect to Google]    [OAuth Callback]    [User Created]   [Return to App]
      ↓                      ↓                   ↓               ↓
[User Returns]          [Profile Setup]     [JWT Tokens]     [Login Success]
```

## **API Endpoints**

### **1. Initiate OAuth Flow**
**Endpoint:** `POST /api/auth/google/initiate/`

**Request:**
```json
{
  "role": "STUDENT",
  "redirect_url": "http://localhost:3000/auth/callback"
}
```

**Response:**
```json
{
  "success": true,
  "oauth_url": "https://supabase-url/auth/v1/authorize?provider=google&redirect_to=...",
  "role": "STUDENT",
  "message": "Redirect user to oauth_url to complete Google authentication"
}
```

### **2. Handle OAuth Callback**
**Endpoint:** `POST /api/auth/google/callback/`

**Request:**
```json
{
  "access_token": "supabase_access_token_from_oauth",
  "refresh_token": "supabase_refresh_token",
  "role": "STUDENT"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User authenticated successfully via Google",
  "user": {
    "id": "uuid-from-supabase",
    "email": "user@gmail.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "STUDENT",
    "auth_provider": "GOOGLE",
    "email_verified": true,
    "is_oauth_user": true
  },
  "access_token": "supabase_access_token",
  "refresh_token": "supabase_refresh_token",
  "created": true,
  "requires_profile_completion": true
}
```

### **3. Complete Profile Setup**
**Endpoint:** `POST /api/auth/google/complete-profile/`

**Headers:**
```json
{
  "Authorization": "Bearer supabase_access_token"
}
```

**Student Request:**
```json
{
  "proficiency_level": "INTERMEDIATE",
  "learning_goals": "Improve conversational English",
  "target_languages": ["English", "Spanish"],
  "phone_number": "+1234567890"
}
```

**Teacher Request:**
```json
{
  "bio": "Experienced English teacher with 5 years...",
  "teaching_experience": 5,
  "teaching_languages": ["English", "French"],
  "hourly_rate": 30.00,
  "phone_number": "+1234567890"
}
```

### **4. Check OAuth Status**
**Endpoint:** `GET /api/auth/google/status/`

**Response:**
```json
{
  "success": true,
  "user": {...},
  "is_oauth_user": true,
  "auth_provider": "GOOGLE",
  "profile_complete": true,
  "profile_data": {...}
}
```

## **Setup Requirements**

### **1. Google Cloud Console Setup**
1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing one

2. **Enable Google+ API**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Application type: "Web application"
   - Add authorized redirect URIs:
     ```
     https://your-supabase-url.supabase.co/auth/v1/callback
     http://localhost:3000/auth/callback (for development)
     ```

4. **Get Client Credentials**
   - Copy Client ID and Client Secret
   - Add to your environment variables

### **2. Supabase Configuration**
1. **Enable Google OAuth Provider**
   - Go to Supabase Dashboard > Authentication > Providers
   - Enable Google provider
   - Add your Google Client ID and Client Secret

2. **Configure Redirect URLs**
   - Add your frontend callback URLs:
     ```
     http://localhost:3000/auth/callback
     https://your-frontend-domain.com/auth/callback
     ```

3. **Update Site URL**
   - Set your site URL in Supabase settings
   - **For Development:** `http://localhost:3000`
   - **For Production:** `https://your-domain.com`
   - This should match your frontend domain

4. **Configure Additional Redirect URLs**
   - Add all possible callback URLs:
   ```
   http://localhost:3000/auth/callback
   http://localhost:3000/extract_oauth_tokens.html
   https://your-domain.com/auth/callback
   ```

### **3. Environment Variables**
Add these to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback

# Existing Supabase variables (already configured)
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## **Frontend Integration**

### **React/Next.js Example**
```javascript
// OAuth Initiation
const initiateGoogleOAuth = async (role) => {
  try {
    const response = await fetch('/api/auth/google/initiate/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        role: role,
        redirect_url: `${window.location.origin}/auth/callback`
      })
    });
    
    const data = await response.json();
    if (data.success) {
      // Redirect user to Google OAuth
      window.location.href = data.oauth_url;
    }
  } catch (error) {
    console.error('OAuth initiation failed:', error);
  }
};

// OAuth Callback Handler
const handleOAuthCallback = async (accessToken, refreshToken, role) => {
  try {
    const response = await fetch('/api/auth/google/callback/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        access_token: accessToken,
        refresh_token: refreshToken,
        role: role
      })
    });
    
    const data = await response.json();
    if (data.success) {
      // Store tokens and user data
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Redirect based on profile completion status
      if (data.requires_profile_completion) {
        router.push('/profile/complete');
      } else {
        router.push('/dashboard');
      }
    }
  } catch (error) {
    console.error('OAuth callback failed:', error);
  }
};
```

### **Frontend Components**
```jsx
// Role Selection Component
const RoleSelectionPage = () => {
  const [selectedRole, setSelectedRole] = useState('');

  const handleGoogleSignup = () => {
    if (!selectedRole) {
      alert('Please select your role first');
      return;
    }
    initiateGoogleOAuth(selectedRole);
  };

  return (
    <div>
      <h2>Join LinguaFlex</h2>
      
      <div>
        <label>
          <input 
            type="radio" 
            value="STUDENT" 
            checked={selectedRole === 'STUDENT'}
            onChange={(e) => setSelectedRole(e.target.value)}
          />
          I want to learn languages
        </label>
        
        <label>
          <input 
            type="radio" 
            value="TEACHER" 
            checked={selectedRole === 'TEACHER'}
            onChange={(e) => setSelectedRole(e.target.value)}
          />
          I want to teach languages
        </label>
      </div>
      
      <button onClick={handleGoogleSignup}>
        Continue with Google
      </button>
    </div>
  );
};

// OAuth Callback Page
const OAuthCallbackPage = () => {
  useEffect(() => {
    // Extract tokens from URL or Supabase callback
    const handleCallback = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session) {
        const role = localStorage.getItem('selectedRole') || 'STUDENT';
        await handleOAuthCallback(
          session.access_token,
          session.refresh_token,
          role
        );
      }
    };
    
    handleCallback();
  }, []);

  return <div>Processing OAuth callback...</div>;
};
```

## **Testing**

### **1. Run Test Script**
```bash
python test_google_oauth.py
```

### **2. Manual Testing Flow**
1. **Start Django Server**
   ```bash
   python manage.py runserver
   ```

2. **Test OAuth Initiation**
   ```bash
   curl -X POST http://localhost:8000/api/auth/google/initiate/ \
   -H "Content-Type: application/json" \
   -d '{"role": "STUDENT", "redirect_url": "http://localhost:3000/auth/callback"}'
   ```

3. **Complete OAuth Flow**
   - Use returned OAuth URL in browser
   - Complete Google authentication
   - Extract access token from callback

4. **Test Callback**
   ```bash
   curl -X POST http://localhost:8000/api/auth/google/callback/ \
   -H "Content-Type: application/json" \
   -d '{"access_token": "REAL_TOKEN", "role": "STUDENT"}'
   ```

## **Database Schema**

### **Updated User Model**
```python
class User(AbstractBaseUser, PermissionsMixin):
    # ... existing fields ...
    
    # OAuth fields
    auth_provider = models.CharField(max_length=20, choices=AuthProvider.choices, default=AuthProvider.EMAIL)
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    is_oauth_user = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
```

### **Migration Applied**
```bash
python manage.py makemigrations core --name add_oauth_fields
python manage.py migrate
```

## **Security Considerations**

1. **Token Validation**: All OAuth tokens are validated through Supabase
2. **Role Verification**: Backend validates role selection against user permissions
3. **Email Verification**: OAuth users are automatically verified via Google
4. **Data Isolation**: OAuth and email users have same permission structure
5. **HTTPS Required**: Production must use HTTPS for OAuth redirects

## **Troubleshooting**

### **Common Issues:**

1. **OAuth URL Generation Fails**
   - Check Supabase configuration
   - Verify Google OAuth provider is enabled
   - Ensure environment variables are set

2. **Callback Token Invalid**
   - Verify access token is from Supabase, not Google directly
   - Check token expiration
   - Ensure Supabase OAuth flow completed successfully

3. **User Creation Fails**
   - Check Django User model constraints
   - Verify database migration was applied
   - Ensure role is valid (STUDENT/TEACHER)

4. **Profile Completion Issues**
   - Verify user is authenticated
   - Check required fields based on role
   - Ensure Student/Teacher profile exists

### **Debug Commands:**
```bash
# Check OAuth user in Django shell
python manage.py shell
>>> from core.models import User
>>> oauth_users = User.objects.filter(is_oauth_user=True)
>>> print(oauth_users)

# Check Supabase connection
>>> from supabase import create_client
>>> from django.conf import settings
>>> supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
>>> print("Supabase connected successfully")
```

---

## **✅ Next Steps**

1. **Configure Google Cloud Console** with your domain
2. **Enable Google OAuth in Supabase** dashboard
3. **Update environment variables** with OAuth credentials
4. **Implement frontend components** for role selection and OAuth flow
5. **Test complete flow** from frontend to backend
6. **Deploy and configure production** OAuth settings

## **🎉 Conclusion**

The Google OAuth authentication system is now fully implemented and ready for integration. Users can:

- ✅ **Select their role** (Student/Teacher) before OAuth
- ✅ **Authenticate with Google** seamlessly
- ✅ **Auto-create accounts** with proper role assignment
- ✅ **Complete profiles** with role-specific fields
- ✅ **Use same JWT system** as email/password users

The system maintains full compatibility with existing email/password authentication while providing a modern, secure OAuth alternative.
