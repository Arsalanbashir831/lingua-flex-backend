# Voice Conversation API Documentation

This document provides comprehensive information about the Voice Conversation endpoints for storing and managing OpenAI speech-to-speech conversation details.

## Base URL
```
http://127.0.0.1:8000/accounts/voice-conversations/
```

## Authentication
All endpoints require authentication using Bearer token:
```
Authorization: Bearer <your_access_token>
```

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/voice-conversations/` | Create a new voice conversation |
| GET | `/voice-conversations/` | List all conversations for the user |
| GET | `/voice-conversations/{id}/` | Get specific conversation details |
| PATCH | `/voice-conversations/{id}/add_feedback/` | Add/update AI feedback |
| GET | `/voice-conversations/by-language/{language}/` | Filter by target language |
| GET | `/voice-conversations/by-type/{type}/` | Filter by conversation type |
| GET | `/voice-conversations/summary/` | Get user's conversation statistics |

## Model Structure

### VoiceConversation Fields
```python
{
    "id": "integer (auto-generated)",
    "user": "foreign key (auto-set to current user)",
    "topic": "string (required, max 200 characters)",
    "transcription": "text (required)",
    "native_language": "string (required, max 50 characters)",
    "target_language": "string (required, max 50 characters)",
    "conversation_type": "choice (required)",
    "duration_minutes": "integer (optional)",
    "ai_feedback": "JSON object (optional)",
    "created_at": "datetime (auto-generated)"
}
```

### Conversation Types
- `practice`: Language Practice
- `lesson`: Language Lesson
- `conversation`: Free Conversation
- `assessment`: Language Assessment
- `pronunciation`: Pronunciation Practice
- `vocabulary`: Vocabulary Building
- `grammar`: Grammar Practice

## API Endpoints Details

### 1. Create Voice Conversation
**POST** `/voice-conversations/`

Creates a new voice conversation record.

**Request Body:**
```json
{
    "topic": "Ordering Food at a Restaurant",
    "transcription": "User: Hi, I'd like to make a reservation...",
    "native_language": "English",
    "target_language": "Spanish",
    "conversation_type": "practice",
    "duration_minutes": 15,
    "ai_feedback": {
        "grammar_score": 85,
        "pronunciation_score": 78,
        "vocabulary_usage": "Good use of restaurant vocabulary"
    }
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "user": 1,
    "topic": "Ordering Food at a Restaurant",
    "transcription": "User: Hi, I'd like to make a reservation...",
    "native_language": "English",
    "target_language": "Spanish",
    "conversation_type": "practice",
    "conversation_type_display": "Language Practice",
    "duration_minutes": 15,
    "ai_feedback": {
        "grammar_score": 85,
        "pronunciation_score": 78,
        "vocabulary_usage": "Good use of restaurant vocabulary"
    },
    "created_at": "2024-01-20T10:30:00Z"
}
```

### 2. List All Conversations
**GET** `/voice-conversations/`

Returns all voice conversations for the authenticated user, ordered by creation date (newest first).

**Response (200 OK):**
```json
[
    {
        "id": 2,
        "user": 1,
        "topic": "Job Interview Preparation",
        "transcription": "User: Tell me about yourself...",
        "native_language": "English",
        "target_language": "French",
        "conversation_type": "lesson",
        "conversation_type_display": "Language Lesson",
        "duration_minutes": 20,
        "ai_feedback": null,
        "created_at": "2024-01-20T11:15:00Z"
    },
    {
        "id": 1,
        "user": 1,
        "topic": "Ordering Food at a Restaurant",
        "transcription": "User: Hi, I'd like to make a reservation...",
        "native_language": "English",
        "target_language": "Spanish",
        "conversation_type": "practice",
        "conversation_type_display": "Language Practice",
        "duration_minutes": 15,
        "ai_feedback": {
            "grammar_score": 85,
            "pronunciation_score": 78
        },
        "created_at": "2024-01-20T10:30:00Z"
    }
]
```

### 3. Get Specific Conversation
**GET** `/voice-conversations/{id}/`

Returns details of a specific conversation.

**Response (200 OK):**
```json
{
    "id": 1,
    "user": 1,
    "topic": "Ordering Food at a Restaurant",
    "transcription": "User: Hi, I'd like to make a reservation for two people tonight at 7 PM. AI: Certainly! I'd be happy to help you with that reservation...",
    "native_language": "English",
    "target_language": "Spanish",
    "conversation_type": "practice",
    "conversation_type_display": "Language Practice",
    "duration_minutes": 15,
    "ai_feedback": {
        "grammar_score": 85,
        "pronunciation_score": 78,
        "vocabulary_usage": "Good use of restaurant vocabulary",
        "areas_for_improvement": ["Practice rolling R sounds", "Work on subjunctive mood"]
    },
    "created_at": "2024-01-20T10:30:00Z"
}
```

### 4. Add/Update AI Feedback
**PATCH** `/voice-conversations/{id}/add_feedback/`

Adds or updates AI feedback for a specific conversation. The new feedback is merged with existing feedback.

**Request Body:**
```json
{
    "ai_feedback": {
        "conversation_flow": "Natural and engaging",
        "confidence_level": "Intermediate",
        "suggested_next_topics": ["Describing food preferences", "Making complaints"]
    }
}
```

**Response (200 OK):**
```json
{
    "message": "AI feedback updated successfully",
    "conversation": {
        "id": 1,
        "topic": "Ordering Food at a Restaurant",
        "ai_feedback": {
            "grammar_score": 85,
            "pronunciation_score": 78,
            "vocabulary_usage": "Good use of restaurant vocabulary",
            "areas_for_improvement": ["Practice rolling R sounds", "Work on subjunctive mood"],
            "conversation_flow": "Natural and engaging",
            "confidence_level": "Intermediate",
            "suggested_next_topics": ["Describing food preferences", "Making complaints"]
        },
        "created_at": "2024-01-20T10:30:00Z"
    }
}
```

### 5. Filter by Target Language
**GET** `/voice-conversations/by-language/{language}/`

Returns conversations filtered by target language.

**Example:** `/voice-conversations/by-language/Spanish/`

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "user": 1,
        "topic": "Ordering Food at a Restaurant",
        "target_language": "Spanish",
        "conversation_type": "practice",
        "conversation_type_display": "Language Practice",
        "duration_minutes": 15,
        "created_at": "2024-01-20T10:30:00Z"
    }
]
```

### 6. Filter by Conversation Type
**GET** `/voice-conversations/by-type/{type}/`

Returns conversations filtered by conversation type.

**Example:** `/voice-conversations/by-type/practice/`

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "user": 1,
        "topic": "Ordering Food at a Restaurant",
        "target_language": "Spanish",
        "conversation_type": "practice",
        "conversation_type_display": "Language Practice",
        "duration_minutes": 15,
        "created_at": "2024-01-20T10:30:00Z"
    }
]
```

### 7. Get Summary Statistics
**GET** `/voice-conversations/summary/`

Returns comprehensive statistics about the user's voice conversations.

**Response (200 OK):**
```json
{
    "total_conversations": 5,
    "total_duration_minutes": 75,
    "conversations_by_language": {
        "Spanish": 3,
        "French": 2
    },
    "conversations_by_type": {
        "practice": 3,
        "lesson": 1,
        "pronunciation": 1
    },
    "recent_conversations_last_7_days": 2,
    "average_duration_minutes": 15
}
```

## Error Responses

### Validation Errors (400 Bad Request)
```json
{
    "topic": ["This field may not be blank."],
    "transcription": ["This field is required."],
    "conversation_type": ["\"invalid_type\" is not a valid choice."]
}
```

### Not Found (404)
```json
{
    "detail": "Not found."
}
```

### Unauthorized (401)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

## Frontend Integration Examples

### JavaScript/Fetch API
```javascript
// Create a new voice conversation
const createVoiceConversation = async (conversationData) => {
    const response = await fetch('/accounts/voice-conversations/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(conversationData)
    });
    
    if (response.ok) {
        return await response.json();
    } else {
        throw new Error('Failed to create conversation');
    }
};

// Get user's conversation summary
const getConversationSummary = async () => {
    const response = await fetch('/accounts/voice-conversations/summary/', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    
    return await response.json();
};
```

### React Component Example
```jsx
import React, { useState, useEffect } from 'react';

const VoiceConversationDashboard = () => {
    const [conversations, setConversations] = useState([]);
    const [summary, setSummary] = useState(null);
    
    useEffect(() => {
        fetchConversations();
        fetchSummary();
    }, []);
    
    const fetchConversations = async () => {
        const response = await fetch('/accounts/voice-conversations/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        const data = await response.json();
        setConversations(data);
    };
    
    const fetchSummary = async () => {
        const response = await fetch('/accounts/voice-conversations/summary/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        const data = await response.json();
        setSummary(data);
    };
    
    return (
        <div>
            <h2>Voice Conversation Dashboard</h2>
            {summary && (
                <div>
                    <p>Total Conversations: {summary.total_conversations}</p>
                    <p>Total Duration: {summary.total_duration_minutes} minutes</p>
                </div>
            )}
            
            <div>
                {conversations.map(conv => (
                    <div key={conv.id}>
                        <h3>{conv.topic}</h3>
                        <p>Language: {conv.target_language}</p>
                        <p>Type: {conv.conversation_type_display}</p>
                        <p>Duration: {conv.duration_minutes} minutes</p>
                    </div>
                ))}
            </div>
        </div>
    );
};
```

## Best Practices

1. **Data Validation**: Always validate data on the frontend before sending to prevent validation errors.

2. **Error Handling**: Implement proper error handling for network issues and API errors.

3. **Pagination**: For large numbers of conversations, consider implementing pagination (can be added to the backend later).

4. **Real-time Updates**: Consider using WebSockets or polling for real-time conversation updates.

5. **AI Feedback Structure**: Keep AI feedback structure consistent across conversations for easier processing.

## Sample AI Feedback Structures

### Basic Feedback
```json
{
    "grammar_score": 85,
    "pronunciation_score": 78,
    "vocabulary_score": 92,
    "overall_score": 85
}
```

### Detailed Feedback
```json
{
    "scores": {
        "grammar": 85,
        "pronunciation": 78,
        "vocabulary": 92,
        "fluency": 80,
        "comprehension": 88
    },
    "strengths": ["Good vocabulary usage", "Natural conversation flow"],
    "areas_for_improvement": ["Practice rolling R sounds", "Work on past tense"],
    "suggested_exercises": ["Pronunciation drill for 'rr'", "Past tense practice sentences"],
    "next_session_focus": "Past tense usage in conversation"
}
```

## Testing

Use the provided `test_voice_conversations.py` script to test all endpoints:

1. Update the `access_token` variable with a valid token
2. Ensure Django server is running
3. Run the test script to validate all functionality

This comprehensive API provides everything needed to store and retrieve OpenAI speech-to-speech conversation details for your language learning platform.
