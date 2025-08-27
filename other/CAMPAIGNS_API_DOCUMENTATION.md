# 📧 Campaign Management API Documentation

## 🎯 **Overview**

The Campaign Management system allows teachers to create and send custom email campaigns to all students using the Resend email service. Teachers can create personalized marketing emails, announcements, and promotional content to engage with students.

---

## 🔐 **Authentication**

All campaign endpoints require teacher authentication:
- **Type**: Bearer Token (Supabase Authentication)
- **Header**: `Authorization: Bearer YOUR_TOKEN`
- **Permission**: Only users with `TeacherProfile` can access these endpoints

---

## 📋 **Campaign Endpoints**

### **1. List & Create Campaigns**
```
GET  /api/campaigns/teacher/campaigns/
POST /api/campaigns/teacher/campaigns/
```

#### **GET - List Campaigns**
Retrieve all campaigns created by the authenticated teacher.

**Query Parameters:**
- `status` (optional): Filter by status (`draft`, `sending`, `sent`, `failed`)
- `search` (optional): Search in title and subject
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of items per page (max 50)

**Response Example:**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/campaigns/teacher/campaigns/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Summer Language Learning Special",
      "subject": "🌟 Unlock Your Language Potential This Summer!",
      "status": "draft",
      "total_recipients": 0,
      "teacher_name": "Sarah Johnson",
      "recipients_count": 0,
      "created_at": "2025-08-27T10:30:00Z",
      "sent_at": null
    }
  ]
}
```

#### **POST - Create Campaign**
Create a new email campaign.

**Request Body:**
```json
{
  "title": "Summer Language Learning Special",
  "subject": "🌟 Unlock Your Language Potential This Summer!",
  "content": "Hello {{student_name}},\n\nI hope this message finds you well...",
  "from_name": "Sarah Johnson",
  "from_email": "sarah.teacher@linguaflex.com",
  "notes": "Summer 2025 promotional campaign"
}
```

**Field Validation:**
- `title`: Required, min 3 characters
- `subject`: Required, min 5 characters  
- `content`: Required, min 20 characters
- `from_name`: Optional (defaults to teacher's name)
- `from_email`: Optional (defaults to teacher's email)
- `notes`: Optional

**Success Response (201):**
```json
{
  "id": 1,
  "title": "Summer Language Learning Special",
  "subject": "🌟 Unlock Your Language Potential This Summer!",
  "content": "Hello {{student_name}}...",
  "status": "draft",
  "total_recipients": 0,
  "from_name": "Sarah Johnson",
  "from_email": "sarah.teacher@linguaflex.com",
  "teacher_name": "Sarah Johnson",
  "teacher_email": "sarah@example.com",
  "recipients_count": 0,
  "recipients": [],
  "notes": "Summer 2025 promotional campaign",
  "created_at": "2025-08-27T10:30:00Z",
  "updated_at": "2025-08-27T10:30:00Z",
  "sent_at": null
}
```

---

### **2. Campaign Details**
```
GET    /api/campaigns/teacher/campaigns/{id}/
PUT    /api/campaigns/teacher/campaigns/{id}/
PATCH  /api/campaigns/teacher/campaigns/{id}/
DELETE /api/campaigns/teacher/campaigns/{id}/
```

#### **GET - Get Campaign Details**
Retrieve detailed information about a specific campaign including recipients.

**Response Example:**
```json
{
  "id": 1,
  "title": "Summer Language Learning Special",
  "subject": "🌟 Unlock Your Language Potential This Summer!",
  "content": "Hello {{student_name}}...",
  "status": "sent",
  "total_recipients": 150,
  "from_name": "Sarah Johnson",
  "from_email": "sarah.teacher@linguaflex.com",
  "teacher_name": "Sarah Johnson",
  "teacher_email": "sarah@example.com",
  "recipients_count": 150,
  "recipients": [
    {
      "id": 1,
      "student_email": "john.doe@example.com",
      "student_name": "John Doe",
      "status": "sent",
      "sent_at": "2025-08-27T11:00:00Z",
      "delivered_at": null,
      "error_message": ""
    }
  ],
  "notes": "Summer 2025 promotional campaign",
  "created_at": "2025-08-27T10:30:00Z",
  "updated_at": "2025-08-27T10:35:00Z",
  "sent_at": "2025-08-27T11:00:00Z"
}
```

#### **PUT/PATCH - Update Campaign**
Update campaign details. Only `draft` status campaigns can be updated.

**Request Body (same as create):**
```json
{
  "title": "Updated Summer Language Learning Special",
  "subject": "🌟 Enhanced Language Learning Experience!",
  "content": "Hello {{student_name}}...",
  "notes": "Updated campaign content"
}
```

#### **DELETE - Delete Campaign**
Delete a campaign. Sent campaigns cannot be deleted (for record keeping).

**Success Response (200):**
```json
{
  "message": "Campaign \"Summer Language Learning Special\" has been deleted successfully."
}
```

---

### **3. Send Campaign**
```
POST /api/campaigns/teacher/campaigns/{id}/send/
```

Send the campaign to all students in the system via email.

**Request Body:**
```json
{
  "confirm_send": true
}
```

**Process:**
1. Validates campaign can be sent (status = `draft`)
2. Retrieves all students from the database
3. Creates recipient records for tracking
4. Sends individual emails via Resend API
5. Updates campaign and recipient statuses
6. Returns detailed sending results

**Success Response (200):**
```json
{
  "message": "Campaign sent successfully",
  "campaign_id": 1,
  "campaign_title": "Summer Language Learning Special",
  "sent_count": 148,
  "failed_count": 2,
  "total_recipients": 150
}
```

**Error Response (400):**
```json
{
  "error": "Campaign cannot be sent. Current status: sent"
}
```

---

### **4. Send Campaign to Specific Students** 🎯 **NEW**
```
POST /api/campaigns/teacher/campaigns/{id}/send-to-students/
```

Send the campaign to specific students selected by email address.

**Request Body:**
```json
{
  "confirm_send": true,
  "student_emails": [
    "john.doe@example.com",
    "jane.smith@example.com",
    "alex.wilson@example.com"
  ]
}
```

**Validation:**
- `confirm_send`: Must be `true`
- `student_emails`: Array of valid email addresses (1-500 emails)
- Duplicate emails are automatically removed
- Invalid email formats are rejected

**Process:**
1. Validates campaign can be sent (status = `draft`)
2. Validates and filters provided student emails
3. Retrieves only the specified students from database
4. Creates recipient records for found students
5. Sends individual emails via Resend API
6. Tracks missing/invalid student emails
7. Returns detailed results including missing students

**Success Response (200):**
```json
{
  "message": "Campaign sent successfully to selected students",
  "campaign_id": 1,
  "campaign_title": "Summer Language Learning Special",
  "sent_count": 2,
  "failed_count": 0,
  "total_recipients": 2,
  "requested_emails": 3,
  "missing_students": ["nonexistent@example.com"],
  "warning": "1 student email(s) were not found in the system"
}
```

**Error Response (400):**
```json
{
  "student_emails": ["At least one student email is required."],
  "confirm_send": ["You must confirm sending by setting confirm_send to True."]
}
```

**Error Response (500):**
```json
{
  "error": "No valid students found with the provided email addresses"
}
```

---

### **5. Get Available Students** 👥 **NEW**
```
GET /api/campaigns/teacher/students/
```

Get list of all students available for campaign targeting.

**Response Example:**
```json
{
  "count": 150,
  "students": [
    {
      "id": 1,
      "email": "john.doe@example.com",
      "name": "John Doe",
      "first_name": "John",
      "last_name": "Doe",
      "username": "johndoe",
      "date_joined": "2025-08-01T10:30:00Z"
    },
    {
      "id": 2,
      "email": "jane.smith@example.com",
      "name": "Jane Smith",
      "first_name": "Jane",
      "last_name": "Smith",
      "username": "janesmith",
      "date_joined": "2025-08-05T14:20:00Z"
    }
  ]
}
```

**Use Cases:**
- Build student selection UI in frontend
- Validate student emails before sending
- Display student counts and information
- Create targeted email lists

---

### **6. Campaign Preview**
```
GET /api/campaigns/teacher/campaigns/{id}/preview/
```

Preview how the campaign email will look when sent to students.

**Response Example:**
```json
{
  "campaign_id": 1,
  "title": "Summer Language Learning Special",
  "subject": "🌟 Unlock Your Language Potential This Summer!",
  "from_name": "Sarah Johnson",
  "from_email": "sarah.teacher@linguaflex.com",
  "sample_student_name": "John Doe",
  "formatted_content": "<!DOCTYPE html><html>...",
  "raw_content": "Hello {{student_name}}..."
}
```

---

### **7. Campaign Statistics**
```
POST /api/campaigns/teacher/campaigns/{id}/send/
```

Send the campaign to all students in the system via email.

**Request Body:**
```json
{
  "confirm_send": true
}
```

**Process:**
1. Validates campaign can be sent (status = `draft`)
2. Retrieves all students from the database
3. Creates recipient records for tracking
4. Sends individual emails via Resend API
5. Updates campaign and recipient statuses
6. Returns detailed sending results

**Success Response (200):**
```json
{
  "message": "Campaign sent successfully",
  "campaign_id": 1,
  "campaign_title": "Summer Language Learning Special",
  "sent_count": 148,
  "failed_count": 2,
  "total_recipients": 150
}
```

**Error Response (400):**
```json
{
  "error": "Campaign cannot be sent. Current status: sent"
}
```

---

### **4. Campaign Preview**
```
GET /api/campaigns/teacher/campaigns/{id}/preview/
```

Preview how the campaign email will look when sent to students.

**Response Example:**
```json
{
  "campaign_id": 1,
  "title": "Summer Language Learning Special",
  "subject": "🌟 Unlock Your Language Potential This Summer!",
  "from_name": "Sarah Johnson",
  "from_email": "sarah.teacher@linguaflex.com",
  "sample_student_name": "John Doe",
  "formatted_content": "<!DOCTYPE html><html>...",
  "raw_content": "Hello {{student_name}}..."
}
```

---

### **5. Campaign Statistics**
```
GET /api/campaigns/teacher/campaigns/stats/
```

Get campaign statistics for the authenticated teacher.

**Response Example:**
```json
{
  "total_campaigns": 12,
  "draft_campaigns": 3,
  "sent_campaigns": 8,
  "failed_campaigns": 1,
  "total_emails_sent": 1247,
  "last_campaign_date": "2025-08-27T10:30:00Z",
  "most_recent_campaign": "Summer Language Learning Special"
}
```

---

## 🎨 **Email Content Features**

### **Personalization**
Use placeholders in your email content:
- `{{student_name}}` - Replaced with student's full name
- `{{name}}` - Alternative placeholder for student's name

### **HTML Formatting**
- Line breaks (`\n`) are automatically converted to `<br>` tags
- Content is wrapped in professional HTML email template
- Automatic styling with header, content area, and footer

### **Email Template Structure**
```html
<!DOCTYPE html>
<html>
<head>
  <style>/* Professional email styling */</style>
</head>
<body>
  <div class="header">
    <h2>Message from Your Teacher</h2>
  </div>
  <div class="content">
    <p>Hello {student_name},</p>
    {your_content_here}
  </div>
  <div class="footer">
    <p>This email was sent through LinguaFlex platform.</p>
  </div>
</body>
</html>
```

---

## 📊 **Campaign Status Flow**

```
draft → sending → sent
  ↓       ↓
failed  failed
```

**Status Descriptions:**
- **`draft`**: Campaign created but not sent
- **`sending`**: Campaign is currently being sent
- **`sent`**: Campaign successfully sent to recipients  
- **`failed`**: Campaign sending failed

---

## 🎯 **Recipient Tracking**

Each campaign tracks individual recipients with the following statuses:
- **`pending`**: Email queued for sending
- **`sent`**: Email sent via Resend API
- **`delivered`**: Email delivered (future feature)
- **`failed`**: Email sending failed

---

## ⚠️ **Important Notes**

### **Email Sending Requirements**
1. **Resend API Key**: Must be configured in `RESEND_API_KEY` environment variable
2. **From Email**: Should be a verified domain in your Resend account
3. **Student Data**: System sends to all users with role = `STUDENT`

### **Campaign Limitations**
- Only teachers can create and send campaigns
- Only `draft` campaigns can be updated or sent
- `sent` campaigns cannot be deleted (for record keeping)
- Failed campaigns can be updated and re-sent

### **Rate Limiting**
- Resend API has rate limits - large student lists may take time
- Campaign status is updated to `sending` during the process
- Individual recipient failures don't stop the entire campaign

---

## 🧪 **Testing the API**

### **Using the Test Script**
1. Configure your teacher token in `test_campaigns_api.py`
2. Run: `python test_campaigns_api.py`
3. The script tests all endpoints except actual email sending

### **Manual Testing with Postman**
1. **Set Base URL**: `{{base_url}}/api/campaigns`
2. **Add Authorization**: Bearer Token with teacher token
3. **Content-Type**: `application/json`

**Sample Test Flow:**
1. POST `/teacher/campaigns/` - Create campaign
2. GET `/teacher/campaigns/` - List campaigns  
3. GET `/teacher/campaigns/{id}/` - Get details
4. GET `/teacher/campaigns/{id}/preview/` - Preview email
5. POST `/teacher/campaigns/{id}/send/` - Send (be careful!)

---

## 🔧 **Configuration**

### **Environment Variables**
```env
RESEND_API_KEY=your_resend_api_key_here
```

### **Django Settings**
```python
# Already configured in settings.py
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
```

### **Database Models**
- **Campaign**: Stores campaign details and metadata
- **CampaignRecipient**: Tracks individual email deliveries

---

## 🚀 **Production Considerations**

1. **Monitoring**: Track campaign success rates and delivery failures
2. **Backup**: Regular database backups for campaign history
3. **Scaling**: Consider background task queues for large recipient lists
4. **Compliance**: Ensure email content follows marketing regulations
5. **Analytics**: Future integration with email tracking and analytics

---

## 🎉 **Success! Your Campaign System is Ready**

The campaign management system provides teachers with a powerful tool to engage students through personalized email marketing. Teachers can create professional campaigns, preview content, and track delivery success - all integrated seamlessly with the LinguaFlex platform! 🚀
