# Enhanced Django Chats Endpoint Documentation

## Overview
The Django chats endpoint has been enhanced to return structured teacher and student information instead of generic participant1/participant2 fields, making it easier for frontend applications to display meaningful user information in chat lists.

## Endpoint Details

### GET /accounts/supabase/chats/

**Purpose**: Retrieve all chats for the authenticated user with enhanced student/teacher information

**Authentication**: Required (Bearer token)

**Method**: GET

**URL**: `{{base_url}}/accounts/supabase/chats/`

**Framework**: Django REST Framework

## Request Format

### Headers
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

### Parameters
None - Returns chats for the authenticated user automatically

## Response Format

### Success Response (200 OK)

#### Enhanced Chat List
```json
[
  {
    "id": "ddef980d-3d99-460c-97c1-ef68b6a1ef24",
    "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
    "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e",
    "student_name": "John Doe",
    "teacher_name": "Jane Smith",
    "created_at": "2025-08-06T10:19:14.395377+00:00",
    "roles_identified": true
  },
  {
    "id": "f8e2a91c-5d77-4892-b3c4-12345abcdef0",
    "student_id": "b7f24e22-1cd5-4672-af1c-1d299780e5af",
    "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e",
    "student_name": "Alice Johnson",
    "teacher_name": "Jane Smith",
    "created_at": "2025-08-05T15:30:22.123456+00:00",
    "roles_identified": true
  }
]
```

#### Fallback Format (when user details unavailable)
```json
[
  {
    "id": "ddef980d-3d99-460c-97c1-ef68b6a1ef24",
    "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
    "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e",
    "student_name": "Student",
    "teacher_name": "Teacher",
    "created_at": "2025-08-06T10:19:14.395377+00:00",
    "roles_identified": false,
    "error": "Failed to fetch user details"
  }
]
```

## Response Fields Explained

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique identifier for the chat |
| `student_id` | string (UUID) | ID of the student participant |
| `teacher_id` | string (UUID) | ID of the teacher participant |
| `student_name` | string | Display name of the student |
| `teacher_name` | string | Display name of the teacher |
| `created_at` | string (ISO timestamp) | When the chat was originally created |
| `roles_identified` | boolean | Whether user roles were successfully determined |
| `error` | string (optional) | Error message if user details couldn't be fetched |

## Key Improvements

### Before (Old Format)
```json
[
  {
    "id": "ddef980d-3d99-460c-97c1-ef68b6a1ef24",
    "participant1": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
    "participant2": "30139770-0d26-4e9e-8b36-8efb33ed7b2e",
    "created_at": "2025-08-06T10:19:14.395377+00:00"
  }
]
```

### After (Enhanced Format)
```json
[
  {
    "id": "ddef980d-3d99-460c-97c1-ef68b6a1ef24",
    "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
    "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e",
    "student_name": "John Doe",
    "teacher_name": "Jane Smith",
    "created_at": "2025-08-06T10:19:14.395377+00:00",
    "roles_identified": true
  }
]
```

### Benefits of Enhancement
1. **Clear Role Identification**: `student_id` and `teacher_id` instead of ambiguous `participant1`/`participant2`
2. **Human-Readable Names**: Actual user names for chat list displays
3. **Role Detection Status**: `roles_identified` flag indicates data reliability
4. **Error Handling**: Graceful fallbacks when user data is unavailable
5. **Frontend Friendly**: Structured data that's easier to consume in UI components

## Role Detection Logic

The endpoint determines student and teacher roles using the following logic:

1. **Fetch User Metadata**: Retrieves user information from Supabase auth
2. **Check Role Field**: Looks for `role` in user metadata (`TEACHER`, `STUDENT`, etc.)
3. **Assign Roles**: Maps users to student/teacher based on role metadata
4. **Fallback Handling**: Uses positional assignment if roles are unclear

### Example Role Detection
```python
# User with TEACHER role
user_metadata = {
  "role": "TEACHER",
  "first_name": "Jane",
  "last_name": "Smith"
}
# Result: Assigned as teacher

# User with STUDENT role  
user_metadata = {
  "role": "STUDENT", 
  "first_name": "John",
  "last_name": "Doe"
}
# Result: Assigned as student

# Users with unclear roles
# Result: Positional assignment (participant1 = student, participant2 = teacher)
```

## Name Resolution Logic

Names are resolved in the following priority order:

1. **Full Name**: `first_name` + `last_name` from user metadata
2. **Email Username**: Username part of email (before @) if metadata unavailable
3. **Role-Based Fallback**: "Student" or "Teacher" based on role
4. **Generic Fallback**: "User" if all else fails

### Example Name Resolution
```javascript
// User has complete metadata
{
  "user_metadata": {
    "first_name": "John",
    "last_name": "Doe",
    "role": "STUDENT"
  },
  "email": "john.doe@university.edu"
}
// Result: "John Doe"

// User has email only
{
  "email": "jane.teacher@school.edu",
  "user_metadata": { "role": "TEACHER" }
}
// Result: "jane.teacher"

// Minimal user data
{
  "user_metadata": { "role": "STUDENT" }
}
// Result: "Student"
```

## Frontend Integration Examples

### 1. React Chat List Component
```jsx
import React, { useState, useEffect } from 'react';

function ChatList({ userToken }) {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchChats();
  }, [userToken]);

  const fetchChats = async () => {
    try {
      const response = await fetch('/accounts/supabase/chats/', {
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const chatsData = await response.json();
        setChats(chatsData);
      } else {
        setError('Failed to load chats');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const openChat = (chatId) => {
    // Navigate to chat interface
    window.location.href = `/chat/${chatId}`;
  };

  if (loading) return <div className="loading">Loading chats...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="chat-list">
      <h2>Your Conversations ({chats.length})</h2>
      
      {chats.length === 0 ? (
        <div className="no-chats">No conversations yet</div>
      ) : (
        chats.map(chat => (
          <div 
            key={chat.id} 
            className="chat-item"
            onClick={() => openChat(chat.id)}
          >
            <div className="chat-participants">
              <div className="student">
                <label>Student:</label>
                <span>{chat.student_name}</span>
              </div>
              <div className="teacher">
                <label>Teacher:</label>
                <span>{chat.teacher_name}</span>
              </div>
            </div>
            
            <div className="chat-meta">
              <span className="created-date">
                {new Date(chat.created_at).toLocaleDateString()}
              </span>
              
              {!chat.roles_identified && (
                <span className="warning">⚠️ Role detection failed</span>
              )}
              
              {chat.error && (
                <span className="error-indicator" title={chat.error}>
                  ❌ Data unavailable
                </span>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default ChatList;
```

### 2. Vue.js Chat Dashboard
```vue
<template>
  <div class="chat-dashboard">
    <h1>Your Chats</h1>
    
    <div v-if="loading" class="loading">
      Loading your conversations...
    </div>
    
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    
    <div v-else-if="chats.length === 0" class="no-chats">
      You don't have any conversations yet.
      <button @click="startNewChat">Start a conversation</button>
    </div>
    
    <div v-else class="chats-container">
      <div class="chat-stats">
        <span>{{ chats.length }} conversations</span>
        <span>{{ successfulRoleDetection }} with identified roles</span>
      </div>
      
      <div 
        v-for="chat in chats" 
        :key="chat.id"
        class="chat-card"
        @click="openChat(chat.id)"
      >
        <div class="chat-header">
          <h3>{{ chat.student_name }} ↔ {{ chat.teacher_name }}</h3>
          <span class="date">{{ formatDate(chat.created_at) }}</span>
        </div>
        
        <div class="chat-details">
          <div class="participant student">
            <span class="role">Student:</span>
            <span class="name">{{ chat.student_name }}</span>
            <span class="id">{{ chat.student_id }}</span>
          </div>
          
          <div class="participant teacher">
            <span class="role">Teacher:</span>
            <span class="name">{{ chat.teacher_name }}</span>
            <span class="id">{{ chat.teacher_id }}</span>
          </div>
        </div>
        
        <div class="chat-status">
          <span 
            v-if="chat.roles_identified"
            class="status success"
          >
            ✅ Roles identified
          </span>
          <span 
            v-else
            class="status warning"
            :title="chat.error || 'Role detection failed'"
          >
            ⚠️ Role detection issue
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChatDashboard',
  props: ['userToken'],
  data() {
    return {
      chats: [],
      loading: true,
      error: null
    };
  },
  computed: {
    successfulRoleDetection() {
      return this.chats.filter(chat => chat.roles_identified).length;
    }
  },
  async mounted() {
    await this.loadChats();
  },
  methods: {
    async loadChats() {
      try {
        const response = await fetch('/accounts/supabase/chats/', {
          headers: {
            'Authorization': `Bearer ${this.userToken}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          this.chats = await response.json();
        } else {
          this.error = 'Failed to load conversations';
        }
      } catch (error) {
        this.error = 'Network error occurred';
      } finally {
        this.loading = false;
      }
    },
    
    openChat(chatId) {
      this.$router.push(`/chat/${chatId}`);
    },
    
    startNewChat() {
      this.$router.push('/teachers'); // Navigate to teacher selection
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    }
  }
};
</script>
```

### 3. JavaScript Chat Manager
```javascript
class ChatManager {
  constructor(baseUrl = '', userToken = '') {
    this.baseUrl = baseUrl;
    this.userToken = userToken;
  }

  async getUserChats() {
    try {
      const response = await fetch(`${this.baseUrl}/accounts/supabase/chats/`, {
        headers: {
          'Authorization': `Bearer ${this.userToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const chats = await response.json();
      
      // Process and validate chat data
      return chats.map(chat => this.processChat(chat));
    } catch (error) {
      console.error('Failed to load chats:', error);
      throw error;
    }
  }

  processChat(chat) {
    return {
      id: chat.id,
      student: {
        id: chat.student_id,
        name: chat.student_name,
        role: 'student'
      },
      teacher: {
        id: chat.teacher_id,
        name: chat.teacher_name,
        role: 'teacher'
      },
      createdAt: new Date(chat.created_at),
      metadata: {
        rolesIdentified: chat.roles_identified,
        hasError: !!chat.error,
        errorMessage: chat.error
      }
    };
  }

  formatChatTitle(chat) {
    return `${chat.student.name} ↔ ${chat.teacher.name}`;
  }

  groupChatsByDate(chats) {
    const groups = {};
    
    chats.forEach(chat => {
      const date = chat.createdAt.toDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(chat);
    });
    
    return groups;
  }

  filterChatsByRole(chats, currentUserId) {
    return chats.map(chat => ({
      ...chat,
      currentUserRole: chat.student.id === currentUserId ? 'student' : 'teacher',
      otherParticipant: chat.student.id === currentUserId ? chat.teacher : chat.student
    }));
  }
}

// Usage example
const chatManager = new ChatManager('http://127.0.0.1:8000', userToken);

async function displayChats() {
  try {
    const chats = await chatManager.getUserChats();
    const processedChats = chatManager.filterChatsByRole(chats, currentUserId);
    const groupedChats = chatManager.groupChatsByDate(processedChats);
    
    // Update UI with organized chat data
    updateChatUI(groupedChats);
  } catch (error) {
    showErrorMessage('Failed to load conversations');
  }
}
```

## Error Handling

### Authentication Errors (401 Unauthorized)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Invalid Token (401 Unauthorized)
```json
{
  "detail": "Invalid token."
}
```

### Frontend Error Handling
```javascript
async function loadChatsWithErrorHandling() {
  try {
    const response = await fetch('/accounts/supabase/chats/', {
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.status === 401) {
      // Handle authentication issues
      redirectToLogin();
      return;
    }

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const chats = await response.json();
    
    // Handle chats with errors
    const validChats = chats.filter(chat => !chat.error);
    const errorChats = chats.filter(chat => chat.error);
    
    if (errorChats.length > 0) {
      console.warn(`${errorChats.length} chats had data issues`);
    }
    
    return validChats;
  } catch (error) {
    console.error('Failed to load chats:', error);
    throw error;
  }
}
```

## Performance Considerations

### Optimization Strategies
1. **User Data Caching**: Cache user metadata to reduce Supabase API calls
2. **Batch Processing**: Process multiple user lookups in parallel
3. **Database Indexing**: Ensure participant fields are indexed
4. **Response Compression**: Enable gzip compression for API responses

### Caching Implementation Example
```python
from django.core.cache import cache
import hashlib

def get_cached_user_data(user_id):
    cache_key = f"user_data_{user_id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
    
    # Fetch from Supabase
    user_data = supabase.auth.admin.get_user_by_id(user_id)
    
    # Cache for 1 hour
    cache.set(cache_key, user_data, 3600)
    
    return user_data
```

## Testing the Endpoint

### Using cURL
```bash
# Test chats endpoint
curl -X GET "http://127.0.0.1:8000/accounts/supabase/chats/" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json"
```

### Using Postman
1. **Method**: GET
2. **URL**: `{{base_url}}/accounts/supabase/chats/`
3. **Headers**: 
   - `Authorization: Bearer {{access_token}}`
   - `Content-Type: application/json`

### Using Python Test Script
Run the provided test script:
```bash
python test_enhanced_django_chats.py
```

## Success Confirmation ✅

The enhanced Django chats endpoint now provides:
- ✅ Clear student/teacher role identification
- ✅ Human-readable names for chat list displays
- ✅ Role detection status and error handling
- ✅ Graceful fallbacks for missing user data
- ✅ Enhanced error reporting
- ✅ Frontend-friendly structured data
- ✅ Comprehensive documentation and examples
- ✅ Production-ready implementation with caching considerations
