import resend
from django.conf import settings

# Configure Resend for email notifications
resend.api_key = settings.RESEND_API_KEY
BASE_URL = settings.BASE_URL

def send_teacher_notification_email(
    student_details: dict, teacher_details: dict, chat_id: str
) -> bool:
    """Send email notification to teacher when a student starts a chat"""
    try:
        # Get student's profile picture URL if available
        profile_picture_html = ""
        if student_details.get("profile_picture"):
            profile_picture_html = f"""
            <div style="text-align: center; margin: 20px 0;">
                <img src="{student_details.get("profile_picture")}" 
                     alt="Student Profile" 
                     style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #3498db;">
            </div>
            """

        # Create HTML email content with only student name and profile picture
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">New Chat Request from Student</h2>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                {profile_picture_html}
                <h3 style="color: #3498db; margin: 10px 0;">
                    {student_details.get("first_name", "")} {student_details.get("last_name", "")}
                </h3>
            </div>
            
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #27ae60;">
                    <strong>📱 A student has initiated a chat conversation with you!</strong>
                </p>
                <p style="margin: 10px 0 0 0; color: #555;">
                    Please click the button below to respond to the student's message.
                </p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{BASE_URL}/teacher/chat?chatId={chat_id}" 
                   style="background-color: #3498db; color: white; padding: 12px 30px; 
                           text-decoration: none; border-radius: 5px; display: inline-block;">
                    Open Chat Conversation
                </a>
            </div>
            
            <div style="text-align: center; margin: 20px 0;">
                <a href="{BASE_URL}/teacher/dashboard" 
                   style="background-color: #2c3e50; color: white; padding: 10px 25px; 
                           text-decoration: none; border-radius: 5px; display: inline-block;">
                    Go to LinguaFlex Dashboard
                </a>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #888; font-size: 12px; text-align: center;">
                This is an automated notification from LinguaFlex. Please do not reply to this email.
            </p>
        </div>
        """

        params = {
            "from": "LinguaFlex <onboarding@lordevs.com>",
            "to": [teacher_details.get("email")],
            "subject": f"New Chat Request from {student_details.get('first_name', 'Student')} {student_details.get('last_name', '')}",
            "html": html_content,
        }

        email_result = resend.Emails.send(params)
        print(f"Email sent successfully to teacher: {email_result}")
        return True

    except Exception as e:
        print(f"Failed to send email notification: {str(e)}")
        return False
