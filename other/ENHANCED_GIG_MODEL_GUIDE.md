# Enhanced Gig Model - Migration and Usage Guide

## Changes Made

### 1. Added Status Field
- **Field**: `status`
- **Type**: CharField with choices
- **Options**: 
  - `active` - Gig is active and bookable
  - `inactive` - Gig is temporarily disabled
  - `draft` - Gig is in draft mode (not published)
- **Default**: `active`

### 2. Modified what_you_provide_in_session
- **Before**: TextField (single string)
- **After**: JSONField (array of strings)
- **Purpose**: Allow multiple services to be listed as an array

## Migration Steps

### 1. Migrations Created
You've already run:
```bash
python manage.py makemigrations
```

### 2. Apply Migrations (REQUIRED)
Now run this command to update your database:
```bash
python manage.py migrate
```

### 3. Handle Existing Data
If you have existing gigs, the migration will:
- Set default `status` to "active" for all existing gigs
- Convert existing `what_you_provide_in_session` text to empty array `[]`

**Note**: You may need to manually update existing gigs to populate the new array format.

## Enhanced Request/Response Format

### Updated Request Format

#### Before Enhancement:
```json
{
    "service_type": "Language Consultation",
    "service_title": "1-on-1 English Conversation",
    "short_description": "Improve your spoken English in a friendly session.",
    "full_description": "We will focus on fluency, pronunciation, and confidence.",
    "price_per_session": "25.00",
    "session_duration": 60,
    "tags": ["english", "conversation"],
    "what_you_provide_in_session": "Personalized feedback and practice"
}
```

#### After Enhancement:
```json
{
    "service_type": "Language Consultation",
    "service_title": "1-on-1 English Conversation",
    "short_description": "Improve your spoken English in a friendly session.",
    "full_description": "We will focus on fluency, pronunciation, and confidence.",
    "price_per_session": "25.00",
    "session_duration": 60,
    "tags": ["english", "conversation"],
    "what_you_provide_in_session": [
        "Personalized feedback",
        "Practice exercises",
        "Grammar correction",
        "Pronunciation guidance"
    ],
    "status": "active"
}
```

### Enhanced Response Format
```json
{
    "id": 11,
    "teacher": 10,
    "teacher_details": {
        "id": 10,
        "user_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e",
        "email": "teacher@example.com",
        "first_name": "Teacher1",
        "last_name": "Teacher2",
        "full_name": "Teacher1 Teacher2",
        "profile_picture": "https://your-project.supabase.co/storage/v1/object/public/user-uploads/user_123/profile.jpg",
        "phone_number": "1234567890",
        "qualification": "Masters in Education and Science",
        "experience_years": 10,
        "about": "Passionate about teaching languages",
        "bio": "I am a passionate language learner",
        "city": "New York",
        "country": "United States",
        "native_language": "English"
    },
    "category": "language",
    "service_type": "Language Consultation",
    "service_title": "1-on-1 English Conversation",
    "short_description": "Improve your spoken English in a friendly session.",
    "full_description": "We will focus on fluency, pronunciation, and confidence.",
    "price_per_session": "25.00",
    "session_duration": 60,
    "tags": ["english", "conversation"],
    "what_you_provide_in_session": [
        "Personalized feedback",
        "Practice exercises", 
        "Grammar correction",
        "Pronunciation guidance"
    ],
    "status": "active",
    "created_at": "2025-08-07T05:29:54.551847Z",
    "updated_at": "2025-08-07T06:20:28.850343Z"
}
```

## Status Field Usage

### Available Status Options:

1. **`active`** (default)
   - Gig is live and bookable by students
   - Appears in public gig listings
   - Students can create bookings

2. **`inactive`**
   - Gig is temporarily disabled
   - Not bookable by students
   - Hidden from public listings
   - Teacher can reactivate later

3. **`draft`**
   - Gig is being prepared but not published
   - Not visible to students
   - Teacher can edit before publishing

### Status Management Examples:

#### Create Active Gig:
```json
{
    "category": "language",
    "service_type": "Language Consultation",
    "service_title": "English Conversation",
    "status": "active",
    // ... other fields
}
```

#### Create Draft Gig:
```json
{
    "category": "language", 
    "service_type": "Language Consultation",
    "service_title": "English Conversation",
    "status": "draft",
    // ... other fields
}
```

#### Deactivate Gig:
```json
{
    "status": "inactive"
}
```

## Frontend Integration Examples

### React Component with Status
```jsx
const GigCard = ({ gig }) => {
    const getStatusBadge = (status) => {
        const statusConfig = {
            active: { color: 'green', text: 'Active' },
            inactive: { color: 'red', text: 'Inactive' },
            draft: { color: 'orange', text: 'Draft' }
        };
        
        const config = statusConfig[status] || statusConfig.draft;
        
        return (
            <span className={`status-badge status-${status}`} style={{ color: config.color }}>
                {config.text}
            </span>
        );
    };
    
    return (
        <div className="gig-card">
            <div className="gig-header">
                <h3>{gig.service_title}</h3>
                {getStatusBadge(gig.status)}
            </div>
            
            <div className="services-provided">
                <h4>What you get:</h4>
                <ul>
                    {gig.what_you_provide_in_session.map((service, index) => (
                        <li key={index}>{service}</li>
                    ))}
                </ul>
            </div>
            
            <div className="teacher-info">
                <span>{gig.teacher_details.full_name}</span>
                <span>${gig.price_per_session} / {gig.session_duration}min</span>
            </div>
        </div>
    );
};
```

### Status Filtering
```javascript
// Filter only active gigs for public display
const getActiveGigs = async () => {
    const response = await fetch('/accounts/gigs/public/');
    const allGigs = await response.json();
    
    // Filter only active gigs
    const activeGigs = allGigs.filter(gig => gig.status === 'active');
    return activeGigs;
};

// Teacher dashboard - show all statuses
const getTeacherGigs = async () => {
    const response = await fetch('/accounts/gigs/', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const gigs = await response.json();
    
    // Group by status
    const gigsByStatus = {
        active: gigs.filter(g => g.status === 'active'),
        inactive: gigs.filter(g => g.status === 'inactive'),
        draft: gigs.filter(g => g.status === 'draft')
    };
    
    return gigsByStatus;
};
```

## API Usage Examples

### Create Gig with New Format
```javascript
const createGig = async (gigData) => {
    const gigPayload = {
        category: "language",
        service_type: "Language Consultation", 
        service_title: "1-on-1 English Conversation",
        short_description: "Improve your spoken English",
        full_description: "We will focus on fluency and confidence",
        price_per_session: "25.00",
        session_duration: 60,
        tags: ["english", "conversation"],
        what_you_provide_in_session: [
            "Personalized feedback",
            "Grammar correction",
            "Pronunciation practice",
            "Confidence building exercises"
        ],
        status: "active"
    };
    
    const response = await fetch('/accounts/gigs/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(gigPayload)
    });
    
    return response.json();
};
```

### Update Gig Status
```javascript
const updateGigStatus = async (gigId, newStatus) => {
    const response = await fetch(`/accounts/gigs/${gigId}/`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
    });
    
    return response.json();
};

// Usage examples:
await updateGigStatus(11, 'inactive'); // Deactivate gig
await updateGigStatus(11, 'active');   // Reactivate gig
await updateGigStatus(11, 'draft');    // Convert to draft
```

## Testing the Enhanced Model

### Test Request for Update:
```bash
PATCH {{base_url}}/accounts/gigs/11/
Content-Type: application/json
Authorization: Bearer your_token

{
    "service_type": "Advanced Language Consultation",
    "service_title": "Professional English Conversation",
    "short_description": "Advanced English practice for professionals",
    "full_description": "Focus on business English, presentations, and professional communication",
    "price_per_session": "35.00",
    "session_duration": 90,
    "tags": ["english", "business", "professional"],
    "what_you_provide_in_session": [
        "Business vocabulary training",
        "Presentation skills practice", 
        "Email writing guidance",
        "Professional conversation practice",
        "Industry-specific terminology"
    ],
    "status": "active"
}
```

### Expected Response:
The response will include the new `status` field and `what_you_provide_in_session` as an array.

## Important Notes

1. **Migration Required**: You must run `python manage.py migrate` to apply the database changes
2. **Existing Data**: Existing gigs will have empty arrays for `what_you_provide_in_session`
3. **Default Status**: New gigs will have `status: "active"` by default
4. **Validation**: The API will validate that `what_you_provide_in_session` is an array
5. **Backward Compatibility**: Update your frontend code to handle the array format

## Next Steps

1. **Apply Migration**:
   ```bash
   python manage.py migrate
   ```

2. **Update Existing Gigs**: Manually update existing gigs to use the new array format

3. **Test Endpoints**: Verify that CRUD operations work with the new fields

4. **Update Frontend**: Modify frontend code to handle the new status field and array format

The enhanced Gig model now provides better status management and more flexible service descriptions!
