# Improved Role Detection System

## Overview

The Django chats endpoint now features **improved role detection** that can identify user roles from multiple sources:

1. **Primary**: Supabase user metadata `role` field
2. **Fallback**: Django database (TeacherProfile model)
3. **Last resort**: Positional assignment with clear warnings

## How It Works

### Role Detection Flow

```
1. Fetch user metadata from Supabase
2. Check metadata.role field
3. If role is UNKNOWN:
   - Query Django database
   - Check if user has TeacherProfile
   - Assign TEACHER or STUDENT accordingly
4. Use roles for accurate name-ID mapping
5. If roles still unclear, use positional fallback
```

### Response Structure

```json
{
  "chats": [
    {
      "id": "chat_id",
      "student_id": "uuid_here",
      "teacher_id": "uuid_here", 
      "student_name": "Student Name",
      "teacher_name": "Teacher Name",
      "created_at": "timestamp",
      "roles_identified": true,
      "role_assignment_method": "role_based",
      "user_info": {
        "uuid1": {
          "name": "User Name",
          "role": "TEACHER",
          "role_source": "metadata"
        },
        "uuid2": {
          "name": "User Name", 
          "role": "STUDENT",
          "role_source": "django"
        }
      },
      "participants": ["uuid1", "uuid2"]
    }
  ]
}
```

## Assignment Methods

| Method | Description | Reliability |
|--------|-------------|-------------|
| `role_based` | Roles determined from metadata/Django | ✅ High |
| `fallback_positional` | participant1=student, participant2=teacher | ⚠️ Low |

## Role Sources

| Source | Description | Priority |
|--------|-------------|----------|
| `metadata` | From Supabase user_metadata.role | 1st |
| `django` | From Django TeacherProfile model | 2nd |

## Using the System

### 1. Test the Endpoint

```bash
python test_improved_role_detection.py
```

### 2. Sync Roles from Django to Supabase

```bash
# Dry run to see what would be updated
python manage.py sync_roles_to_supabase --dry-run

# Actually sync the roles
python manage.py sync_roles_to_supabase

# Sync a specific user
python manage.py sync_roles_to_supabase --email user@example.com
```

### 3. Verify Results

Check the test output for:
- ✅ Correct name-ID mapping
- ✅ `roles_identified: true`
- ✅ `role_assignment_method: "role_based"`

## Troubleshooting

### Names Not Mapping Correctly

1. **Check role sources in response**:
   ```json
   "user_info": {
     "uuid": {
       "role_source": "django",  // Good - role detected
       "warning": "..."          // Bad - role unclear
     }
   }
   ```

2. **Sync metadata**:
   ```bash
   python manage.py sync_roles_to_supabase
   ```

3. **Verify Django models**:
   - Ensure TeacherProfile objects exist for teachers
   - Check User.email matches Supabase user.email

### Role Detection Failing

1. **Check Supabase connection**:
   - Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
   - Test auth.admin.get_user_by_id() works

2. **Check Django models**:
   - Verify TeacherProfile model exists
   - Check foreign key to User model

3. **Check email matching**:
   - Ensure User.email in Django matches Supabase user.email
   - Consider adding supabase_id field for direct mapping

## Best Practices

### 1. Keep Metadata in Sync

- Run `sync_roles_to_supabase` after user role changes
- Consider adding to user registration/profile update flows
- Set up periodic sync (daily/weekly)

### 2. Handle Edge Cases

- Always check `roles_identified` field in frontend
- Show appropriate UI for unclear roles
- Provide user feedback when roles are assumed

### 3. Monitor Performance

- Role detection adds database queries
- Consider caching for high-traffic scenarios
- Monitor Supabase API limits

## Frontend Integration

```javascript
// Check if roles were properly identified
if (chat.roles_identified) {
  // Use student_name and teacher_name confidently
  displayChat(chat.student_name, chat.teacher_name);
} else {
  // Handle unclear roles gracefully
  displayChatWithWarning(chat);
}

// Show role assignment method for debugging
if (chat.role_assignment_method === 'fallback_positional') {
  console.warn('Chat roles assigned positionally - may be inaccurate');
}
```

## API Changes Summary

### New Fields Added

- `roles_identified`: Boolean indicating if roles were reliably determined
- `role_assignment_method`: How roles were assigned (role_based/fallback_positional)
- `user_info[].role_source`: Where the role came from (metadata/django)
- `user_info[].warning`: Present when role assignment is uncertain

### Behavior Changes

- Names now consistently map to correct IDs when roles are known
- Django database is checked when Supabase metadata is incomplete
- Clearer fallback logic with positional assignment when all else fails
- More detailed debugging information in responses

## Future Improvements

1. **Direct User Mapping**: Add `supabase_id` field to Django User model
2. **Role Caching**: Cache role lookups to reduce database queries  
3. **Real-time Sync**: Update Supabase metadata immediately on role changes
4. **Role History**: Track role changes over time
5. **Bulk Operations**: Optimize for multiple chat queries
