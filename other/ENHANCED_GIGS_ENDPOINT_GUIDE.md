# Enhanced Gigs Endpoint Guide

## Overview
The gigs endpoint has been enhanced to include comprehensive teacher details in all responses. This provides clients with complete teacher information without requiring additional API calls.

## Endpoint Details

**URL:** `POST/GET {{base_url}}/accounts/gigs/`
**Public URL:** `GET {{base_url}}/accounts/gigs/public/`

## Enhanced Response Structure

### Before Enhancement:
```json
{
    "id": 11,
    "teacher": 10,
    "category": "astrological",
    "service_type": "Language Consultation",
    "service_title": "1-on-1 English Conversation",
    "short_description": "Improve your spoken English in a friendly session.",
    "full_description": "We will focus on fluency, pronunciation, and confidence.",
    "price_per_session": "25.00",
    "session_duration": 60,
    "tags": ["english", "conversation"],
    "what_you_provide_in_session": "Personalized feedback and practice",
    "created_at": "2025-08-07T05:29:54.551847Z",
    "updated_at": "2025-08-07T05:29:54.551858Z"
}
```

### After Enhancement:
```json
{
    "id": 11,
    "teacher": 10,
    "teacher_details": {
        "id": 10,
        "user_id": "user-uuid-string",
        "email": "teacher@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "profile_picture": "https://your-project.supabase.co/storage/v1/object/public/user-uploads/user_123/profile.jpg",
        "phone_number": "1234567890",
        "qualification": "Masters in English Literature",
        "experience_years": 5,
        "about": "Passionate language teacher with 5 years of experience",
        "bio": "I love helping students improve their language skills",
        "city": "New York",
        "country": "United States",
        "native_language": "English"
    },
    "category": "astrological",
    "service_type": "Language Consultation",
    "service_title": "1-on-1 English Conversation",
    "short_description": "Improve your spoken English in a friendly session.",
    "full_description": "We will focus on fluency, pronunciation, and confidence.",
    "price_per_session": "25.00",
    "session_duration": 60,
    "tags": ["english", "conversation"],
    "what_you_provide_in_session": "Personalized feedback and practice",
    "created_at": "2025-08-07T05:29:54.551847Z",
    "updated_at": "2025-08-07T05:29:54.551858Z"
}
```

## Teacher Details Fields

### User Information
- **`id`**: Teacher profile ID
- **`user_id`**: User account ID
- **`email`**: Teacher's email address
- **`first_name`**: Teacher's first name
- **`last_name`**: Teacher's last name
- **`full_name`**: Combined first and last name
- **`profile_picture`**: Full Supabase URL to profile image (null if not set)
- **`phone_number`**: Teacher's contact number

### Professional Information
- **`qualification`**: Teacher's educational background/qualifications
- **`experience_years`**: Years of teaching experience
- **`about`**: Professional description about the teacher

### Personal Information
- **`bio`**: Personal bio from user profile
- **`city`**: Teacher's city
- **`country`**: Teacher's country
- **`native_language`**: Teacher's native language

## API Usage Examples

### Create Gig with Teacher Details Response
```javascript
const createGig = async (gigData) => {
    const response = await fetch('/accounts/gigs/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(gigData)
    });
    
    const result = await response.json();
    
    // Access teacher details
    const teacher = result.teacher_details;
    console.log(`Gig created by ${teacher.full_name}`);
    console.log(`Teacher experience: ${teacher.experience_years} years`);
    console.log(`Teacher location: ${teacher.city}, ${teacher.country}`);
    
    return result;
};
```

### List All Gigs with Teacher Details
```javascript
const fetchGigs = async () => {
    const response = await fetch('/accounts/gigs/', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    
    const gigs = await response.json();
    
    // Display gigs with teacher information
    gigs.forEach(gig => {
        console.log(`${gig.service_title} by ${gig.teacher_details.full_name}`);
        console.log(`Price: $${gig.price_per_session} for ${gig.session_duration} minutes`);
        console.log(`Teacher: ${gig.teacher_details.qualification}`);
    });
    
    return gigs;
};
```

### Public Gigs (No Authentication Required)
```javascript
const fetchPublicGigs = async () => {
    const response = await fetch('/accounts/gigs/public/');
    const gigs = await response.json();
    
    // Public access to all gigs with teacher details
    return gigs;
};
```

## Frontend Integration Examples

### React Component for Gig Display
```jsx
import React from 'react';

const GigCard = ({ gig }) => {
    const { teacher_details: teacher } = gig;
    
    return (
        <div className="gig-card">
            <div className="teacher-info">
                {teacher.profile_picture ? (
                    <img src={teacher.profile_picture} alt={teacher.full_name} />
                ) : (
                    <div className="avatar">
                        {teacher.first_name?.[0]}{teacher.last_name?.[0]}
                    </div>
                )}
                <div className="teacher-details">
                    <h3>{teacher.full_name}</h3>
                    <p>{teacher.qualification}</p>
                    <p>{teacher.experience_years} years experience</p>
                    <p>{teacher.city}, {teacher.country}</p>
                </div>
            </div>
            
            <div className="gig-info">
                <h2>{gig.service_title}</h2>
                <p>{gig.short_description}</p>
                <div className="gig-meta">
                    <span>${gig.price_per_session}</span>
                    <span>{gig.session_duration} minutes</span>
                    <span className="category">{gig.category}</span>
                </div>
                <div className="tags">
                    {gig.tags.map(tag => (
                        <span key={tag} className="tag">{tag}</span>
                    ))}
                </div>
            </div>
        </div>
    );
};

const GigsList = () => {
    const [gigs, setGigs] = useState([]);
    
    useEffect(() => {
        fetchPublicGigs().then(setGigs);
    }, []);
    
    return (
        <div className="gigs-container">
            {gigs.map(gig => (
                <GigCard key={gig.id} gig={gig} />
            ))}
        </div>
    );
};
```

### Vue.js Component Example
```vue
<template>
  <div class="gig-list">
    <div v-for="gig in gigs" :key="gig.id" class="gig-item">
      <div class="teacher-section">
        <img 
          :src="gig.teacher_details.profile_picture || '/default-avatar.png'" 
          :alt="gig.teacher_details.full_name"
          class="teacher-avatar"
        />
        <div class="teacher-info">
          <h4>{{ gig.teacher_details.full_name }}</h4>
          <p>{{ gig.teacher_details.qualification }}</p>
          <span>{{ gig.teacher_details.experience_years }} years exp.</span>
        </div>
      </div>
      
      <div class="gig-content">
        <h3>{{ gig.service_title }}</h3>
        <p>{{ gig.short_description }}</p>
        <div class="pricing">
          ${{ gig.price_per_session }} / {{ gig.session_duration }}min
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      gigs: []
    };
  },
  async mounted() {
    try {
      const response = await fetch('/accounts/gigs/public/');
      this.gigs = await response.json();
    } catch (error) {
      console.error('Failed to fetch gigs:', error);
    }
  }
};
</script>
```

## Affected Endpoints

### 1. Create Gig
- **Method**: POST
- **URL**: `/accounts/gigs/`
- **Auth**: Required (Teacher only)
- **Returns**: Created gig with full teacher details

### 2. List Teacher's Gigs
- **Method**: GET
- **URL**: `/accounts/gigs/`
- **Auth**: Required (Teacher only)
- **Returns**: Array of teacher's gigs with teacher details

### 3. Update Gig
- **Method**: PUT/PATCH
- **URL**: `/accounts/gigs/{id}/`
- **Auth**: Required (Teacher only)
- **Returns**: Updated gig with teacher details

### 4. Get Specific Gig
- **Method**: GET
- **URL**: `/accounts/gigs/{id}/`
- **Auth**: Required (Teacher only)
- **Returns**: Single gig with teacher details

### 5. Public Gigs
- **Method**: GET
- **URL**: `/accounts/gigs/public/`
- **Auth**: Not required
- **Returns**: All gigs with teacher details (public access)

## Benefits of Enhancement

### For Frontend Development:
- **Reduced API Calls**: No need for separate teacher detail requests
- **Rich UI Components**: Complete teacher info for gig displays
- **Better UX**: Immediate access to teacher credentials and experience
- **Profile Integration**: Direct access to teacher profile pictures and contact info

### For Mobile Apps:
- **Offline Capability**: Cache complete teacher data with gigs
- **Performance**: Fewer network requests
- **User Experience**: Rich teacher profiles in gig listings

### For Search and Filtering:
- **Teacher-Based Search**: Filter by teacher location, experience, etc.
- **Advanced Filtering**: Sort by teacher ratings, experience, location
- **Recommendation Systems**: Use teacher data for personalized recommendations

## Testing

### Manual Testing with Postman

1. **Create a Gig** (Teacher required):
   ```
   POST /accounts/gigs/
   Headers: Authorization: Bearer {teacher_token}
   Body: {gig data as shown above}
   ```

2. **Verify Teacher Details**:
   - Check that response includes `teacher_details` object
   - Verify all teacher fields are present
   - Confirm profile picture URL is valid Supabase URL

3. **Test Public Access**:
   ```
   GET /accounts/gigs/public/
   No authorization required
   ```

### Automated Testing
Use the provided test script `test_gigs_with_teacher_details.py`:

```bash
python test_gigs_with_teacher_details.py
```

## Migration Notes

- **Backward Compatibility**: Existing API consumers will receive additional `teacher_details` field
- **Performance**: Slight increase in response size due to teacher data inclusion
- **Caching**: Consider caching teacher profile data for better performance
- **Documentation**: Update API documentation to reflect new response structure

The enhanced gigs endpoint now provides complete teacher information, enabling richer frontend experiences and reducing the need for multiple API calls to gather teacher details!
