# 🚀 Postman Testing Guide for Campaigns API

## 📋 **Setup Instructions**

### **1. Environment Configuration**
Create a new Postman environment with these variables:

```
Variable Name    | Initial Value           | Current Value
-----------------|------------------------|------------------
base_url         | http://localhost:8000  | http://localhost:8000
teacher_token    | your_teacher_token_here| your_actual_token
campaign_id      | 1                      | {{dynamic_value}}
```

### **2. Authorization Setup**
For all requests, use **Bearer Token** authenti### **5. Test Send to Specific Students with Invalid Data** 🎯 **NEW**
```
POST {{base_url}}/api/campaigns/teacher/campaigns/{{campaign_id}}/send-to-students/
```

**Request Body:**
```json
{
  "confirm_send": true,
  "student_emails": []
}
```

**Expected Response (400 Bad Request):**
```json
{
  "student_emails": ["At least one student email is required."]
}
```

### **6. Test Send to Specific Students with Invalid Emails** 🎯 **NEW**
```
POST {{base_url}}/api/campaigns/teacher/campaigns/{{campaign_id}}/send-to-students/
```

**Request Body:**
```json
{
  "confirm_send": true,
  "student_emails": ["invalid-email", "another@invalid"]
}
```

**Expected Response (400 Bad Request):**
```json
{
  "student_emails": ["Enter a valid email address."]
}
```

### **7. Test Send to Non-existent Students** 🎯 **NEW**
```
POST {{base_url}}/api/campaigns/teacher/campaigns/{{campaign_id}}/send-to-students/
```

**Request Body:**
```json
{
  "confirm_send": true,
  "student_emails": ["nonexistent1@example.com", "fake2@test.com"]
}
```

**Expected Response (500 Internal Server Error):**
```json
{
  "error": "No valid students found with the provided email addresses"
}
```ation:
- **Type**: Bearer Token
- **Token**: `{{teacher_token}}`

---

## 📧 **Campaign API Endpoints**

### **1. Create Campaign**
```
POST {{base_url}}/api/campaigns/teacher/campaigns/
```

**Headers:**
```
Authorization: Bearer {{teacher_token}}
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "title": "Summer Language Learning Special 2025",
  "subject": "🌟 Unlock Your Language Potential This Summer!",
  "content": "Hello {{student_name}},\n\nI hope this message finds you well! As we approach the summer season, I wanted to reach out with an exciting opportunity to accelerate your language learning journey.\n\n🎯 **What I'm Offering:**\n- Personalized one-on-one language sessions\n- Flexible scheduling to fit your summer plans\n- Interactive conversation practice\n- Cultural immersion experiences\n- Customized learning materials\n\n📚 **Special Summer Package:**\n- 10 sessions for the price of 8\n- Free initial assessment and learning plan\n- Access to exclusive learning resources\n- Progress tracking and regular feedback\n\nWhether you're preparing for travel, academic requirements, or personal enrichment, I'm here to help you achieve your language goals efficiently and enjoyably.\n\n🗓️ **Limited Time Offer:**\nBook your sessions before the end of August and receive a 20% discount on my regular rates!\n\nFeel free to reply to this email or book a consultation through the LinguaFlex platform. I'd love to discuss how we can tailor the perfect learning experience for you.\n\nLooking forward to our language learning adventure together!\n\nBest regards,\nYour Language Teacher",
  "from_name": "Sarah Johnson",
  "from_email": "sarah.teacher@linguaflex.com",
  "notes": "Summer 2025 promotional campaign targeting all students for language learning services"
}
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "title": "Summer Language Learning Special 2025",
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

**Test Script (Postman Tests Tab):**
```javascript
// Save campaign ID for other requests
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("campaign_id", response.id);
    pm.test("Campaign created successfully", function () {
        pm.expect(response.status).to.eql("draft");
        pm.expect(response.id).to.be.a('number');
    });
}

pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});
```

---

### **2. List All Campaigns**
```
GET {{base_url}}/api/campaigns/teacher/campaigns/
```

**Headers:**
```
Authorization: Bearer {{teacher_token}}
```

**Query Parameters (Optional):**
- `status`: `draft`, `sending`, `sent`, `failed`
- `search`: Search term for title/subject
- `page`: Page number
- `page_size`: Items per page (max 50)

**Example with Query Params:**
```
GET {{base_url}}/api/campaigns/teacher/campaigns/?status=draft&search=summer&page=1&page_size=10
```

**Expected Response (200 OK):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Summer Language Learning Special 2025",
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

**Test Script:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has pagination structure", function () {
    const response = pm.response.json();
    pm.expect(response).to.have.property('count');
    pm.expect(response).to.have.property('results');
    pm.expect(response.results).to.be.an('array');
});
```

---

### **3. Get Campaign Details**
```
GET {{base_url}}/api/campaigns/teacher/campaigns/{{campaign_id}}/
```

**Headers:**
```
Authorization: Bearer {{teacher_token}}
```

**Expected Response (200 OK):**
```json
{
  "id": 1,
  "title": "Summer Language Learning Special 2025",
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

**Test Script:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Campaign details are complete", function () {
    const response = pm.response.json();
    pm.expect(response).to.have.property('id');
    pm.expect(response).to.have.property('title');
    pm.expect(response).to.have.property('content');
    pm.expect(response).to.have.property('recipients');
});
```

---

### **4. Update Campaign**
```
PATCH {{base_url}}/api/campaigns/teacher/campaigns/{{campaign_id}}/
```

**Headers:**
```
Authorization: Bearer {{teacher_token}}
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "title": "Updated Summer Language Learning Special 2025",
  "subject": "🌟 Enhanced Language Learning Experience This Summer!",
  "notes": "Updated campaign with improved messaging and better call-to-action"
}
```

**Expected Response (200 OK):**
```json
{
  "title": "Updated Summer Language Learning Special 2025",
  "subject": "🌟 Enhanced Language Learning Experience This Summer!",
  "content": "Hello {{student_name}}...",
  "from_name": "Sarah Johnson",
  "from_email": "sarah.teacher@linguaflex.com",
  "notes": "Updated campaign with improved messaging"
}
```

**Test Script:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Campaign updated successfully", function () {
    const response = pm.response.json();
    pm.expect(response.title).to.include("Updated");
});
```

---

### **5. Preview Campaign Email**
```
GET {{base_url}}/api/campaigns/teacher/campaigns/{{campaign_id}}/preview/
```

**Headers:**
```
Authorization: Bearer {{teacher_token}}
```

**Expected Response (200 OK):**
```json
{
  "campaign_id": 1,
  "title": "Summer Language Learning Special 2025",
  "subject": "🌟 Unlock Your Language Potential This Summer!",
  "from_name": "Sarah Johnson",
  "from_email": "sarah.teacher@linguaflex.com",
  "sample_student_name": "John Doe",
  "formatted_content": "<!DOCTYPE html><html><head>...</head><body>...</body></html>",
  "raw_content": "Hello {{student_name}}..."
}
```

**Test Script:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Preview contains formatted content", function () {
    const response = pm.response.json();
    pm.expect(response).to.have.property('formatted_content');
    pm.expect(response).to.have.property('raw_content');
    pm.expect(response.formatted_content).to.include('<!DOCTYPE html>');
});
```

---

### **6. Get Campaign Statistics**
```
GET {{base_url}}/api/campaigns/teacher/campaigns/stats/
```

**Headers:**
```
Authorization: Bearer {{teacher_token}}
```

**Expected Response (200 OK):**
```json
{
  "total_campaigns": 5,
  "draft_campaigns": 3,
  "sent_campaigns": 2,
  "failed_campaigns": 0,
  "total_emails_sent": 245,
  "last_campaign_date": "2025-08-27T10:30:00Z",
  "most_recent_campaign": "Summer Language Learning Special 2025"
}
```

**Test Script:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Statistics contain all required fields", function () {
    const response = pm.response.json();
    pm.expect(response).to.have.property('total_campaigns');
    pm.expect(response).to.have.property('draft_campaigns');
    pm.expect(response).to.have.property('sent_campaigns');
    pm.expect(response).to.have.property('total_emails_sent');
});
```

---

### **7. Send Campaign (⚠️ CAUTION!)**
```
POST {{base_url}}/api/campaigns/teacher/campaigns/{{campaign_id}}/send/
```

**⚠️ WARNING: This will send actual emails to all students in the system!**

**Headers:**
```
Authorization: Bearer {{teacher_token}}
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "confirm_send": true
}
```

**Expected Response (200 OK):**
```json
{
  "message": "Campaign sent successfully",
  "campaign_id": 1,
  "campaign_title": "Summer Language Learning Special 2025",
  "sent_count": 148,
  "failed_count": 2,
  "total_recipients": 150
}
```

**Test Script:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Campaign sent successfully", function () {
    const response = pm.response.json();
    pm.expect(response).to.have.property('sent_count');
    pm.expect(response).to.have.property('total_recipients');
    pm.expect(response.message).to.include("sent successfully");
});
```

---

### **8. Send Campaign to Specific Students** 🎯 **NEW**
```
POST {{base_url}}/api/campaigns/teacher/campaigns/{{campaign_id}}/send-to-students/
```

**⚠️ WARNING: This will send actual emails to the specified students!**

**Headers:**
```
Authorization: Bearer {{teacher_token}}
Content-Type: application/json
```

**Request Body (JSON):**
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

**Expected Response (200 OK):**
```json
{
  "message": "Campaign sent successfully to selected students",
  "campaign_id": 1,
  "campaign_title": "Summer Language Learning Special 2025",
  "sent_count": 2,
  "failed_count": 0,
  "total_recipients": 2,
  "requested_emails": 3,
  "missing_students": ["nonexistent@example.com"],
  "warning": "1 student email(s) were not found in the system"
}
```

**Test Script:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Campaign sent to specific students", function () {
    const response = pm.response.json();
    pm.expect(response).to.have.property('sent_count');
    pm.expect(response).to.have.property('requested_emails');
    pm.expect(response).to.have.property('missing_students');
    pm.expect(response.message).to.include("sent successfully");
});

pm.test("Track missing students", function () {
    const response = pm.response.json();
    if (response.missing_students && response.missing_students.length > 0) {
        console.log(`Missing students: ${response.missing_students.join(', ')}`);
        pm.expect(response).to.have.property('warning');
    }
});
```

---

### **9. Get Available Students** 👥 **NEW**
```
GET {{base_url}}/api/campaigns/teacher/students/
```

**Headers:**
```
Authorization: Bearer {{teacher_token}}
```

**Expected Response (200 OK):**
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

**Test Script:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Students list structure", function () {
    const response = pm.response.json();
    pm.expect(response).to.have.property('count');
    pm.expect(response).to.have.property('students');
    pm.expect(response.students).to.be.an('array');
});

pm.test("Student data completeness", function () {
    const response = pm.response.json();
    if (response.students.length > 0) {
        const student = response.students[0];
        pm.expect(student).to.have.property('id');
        pm.expect(student).to.have.property('email');
        pm.expect(student).to.have.property('name');
        
        // Save first few student emails for other tests
        const emails = response.students.slice(0, 3).map(s => s.email);
        pm.environment.set("test_student_emails", JSON.stringify(emails));
    }
});
```

---

### **10. Delete Campaign**
```
DELETE {{base_url}}/api/campaigns/teacher/campaigns/{{campaign_id}}/
```

**Headers:**
```
Authorization: Bearer {{teacher_token}}
```

**Expected Response (200 OK):**
```json
{
  "message": "Campaign \"Summer Language Learning Special 2025\" has been deleted successfully."
}
```

**Test Script:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Campaign deleted successfully", function () {
    const response = pm.response.json();
    pm.expect(response.message).to.include("deleted successfully");
});
```

---

## 🔧 **Error Testing Scenarios**

### **1. Test Invalid Campaign ID**
```
GET {{base_url}}/api/campaigns/teacher/campaigns/99999/
```

**Expected Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```

### **2. Test Invalid Authentication**
```
GET {{base_url}}/api/campaigns/teacher/campaigns/
```
**Headers:** (Remove Authorization header)

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### **3. Test Invalid Campaign Data**
```
POST {{base_url}}/api/campaigns/teacher/campaigns/
```

**Request Body:**
```json
{
  "title": "",
  "subject": "Hi",
  "content": "Short"
}
```

**Expected Response (400 Bad Request):**
```json
{
  "title": ["Campaign title must be at least 3 characters long."],
  "subject": ["Email subject must be at least 5 characters long."],
  "content": ["Email content must be at least 20 characters long."]
}
```

### **4. Test Send Campaign with Invalid Confirmation**
```
POST {{base_url}}/api/campaigns/teacher/campaigns/{{campaign_id}}/send/
```

**Request Body:**
```json
{
  "confirm_send": false
}
```

**Expected Response (400 Bad Request):**
```json
{
  "confirm_send": ["You must confirm sending by setting confirm_send to True."]
}
```

---

## 📊 **Collection Organization**

### **Folder Structure:**
```
📁 Campaigns API
├── 📁 Campaign Management
│   ├── 📄 Create Campaign
│   ├── 📄 List Campaigns
│   ├── 📄 Get Campaign Details
│   ├── 📄 Update Campaign
│   └── 📄 Delete Campaign
├── 📁 Campaign Actions
│   ├── 📄 Preview Campaign
│   ├── 📄 Send Campaign ⚠️
│   └── 📄 Get Campaign Stats
└── 📁 Error Testing
    ├── 📄 Invalid Campaign ID
    ├── 📄 No Authentication
    ├── 📄 Invalid Data
    └── 📄 Invalid Send Confirmation
```

---

## 🧪 **Test Execution Flow**

### **Recommended Testing Order:**
1. **Create Campaign** (saves `campaign_id` to environment)
2. **List Campaigns** (verify campaign appears)
3. **Get Campaign Details** (verify full data)
4. **Preview Campaign** (check email formatting)
5. **Update Campaign** (modify some fields)
6. **Get Campaign Stats** (verify statistics)
7. **Send Campaign** (⚠️ ONLY IF YOU WANT TO SEND REAL EMAILS)
8. **Error Testing** (test various error scenarios)
9. **Delete Campaign** (cleanup - only for draft campaigns)

### **Pre-Request Script (Collection Level):**
```javascript
// Set timestamp for unique titles
pm.globals.set("timestamp", Date.now());

// Check if teacher token is set
if (!pm.environment.get("teacher_token") || pm.environment.get("teacher_token") === "your_teacher_token_here") {
    console.log("⚠️ Warning: Please set your teacher_token in the environment variables");
}
```

### **Test Script (Collection Level):**
```javascript
// Log response time
console.log(`Response time: ${pm.response.responseTime}ms`);

// Log any errors
if (pm.response.code >= 400) {
    console.log(`❌ Error ${pm.response.code}: ${pm.response.text()}`);
}
```

---

## 🔐 **Authentication Setup Guide**

### **Step 1: Get Teacher Token**
1. First, authenticate as a teacher using the login endpoint
2. Copy the bearer token from the response
3. Set it in your Postman environment as `teacher_token`

### **Step 2: Verify Teacher Role**
Make sure the authenticated user has a `TeacherProfile` in the system, otherwise all requests will return 403 Forbidden.

---

## 🎯 **Success Indicators**

✅ **Campaign Creation**: Status 201, campaign ID returned  
✅ **Campaign Listing**: Status 200, pagination structure  
✅ **Campaign Details**: Status 200, complete campaign data  
✅ **Campaign Preview**: Status 200, HTML formatted content  
✅ **Campaign Statistics**: Status 200, aggregated stats  
✅ **Campaign Updates**: Status 200, only draft campaigns  
✅ **Campaign Sending**: Status 200, email delivery results  
✅ **Error Handling**: Appropriate status codes and messages  

---

## 🚀 **Ready to Test!**

Your Postman collection is now ready to comprehensively test the Campaigns API. Remember to:

1. ✅ Set up environment variables
2. ✅ Configure authentication
3. ✅ Test in the recommended order
4. ⚠️ Be careful with the send campaign endpoint
5. ✅ Review all test scripts for validation

**Happy Testing!** 🧪✨
