import resend
from django.conf import settings
from django.utils import timezone
from typing import List, Dict, Tuple
from .models import Campaign, CampaignRecipient
from core.models import User


class ResendEmailService:
    """
    Service class to handle email sending via Resend API
    """
    
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        if not self.api_key:
            raise ValueError("RESEND_API_KEY not found in settings")
        
        # Initialize Resend client
        resend.api_key = self.api_key
    
    def get_all_students(self) -> List[Dict[str, str]]:
        """
        Get all students from the database
        Returns list of dictionaries with email and name
        """
        students = User.objects.filter(role=User.Role.STUDENT).select_related('profile')
        
        student_list = []
        for student in students:
            student_data = {
                'email': student.email,
                'name': student.get_full_name() or student.username
            }
            student_list.append(student_data)
        
        return student_list
    
    def create_campaign_recipients(self, campaign: Campaign, students: List[Dict[str, str]]) -> None:
        """
        Create CampaignRecipient records for all students
        """
        recipients = []
        for student in students:
            recipient = CampaignRecipient(
                campaign=campaign,
                student_email=student['email'],
                student_name=student['name']
            )
            recipients.append(recipient)
        
        # Bulk create recipients
        CampaignRecipient.objects.bulk_create(recipients, ignore_conflicts=True)
        
        # Update campaign total recipients count
        campaign.total_recipients = len(recipients)
        campaign.save(update_fields=['total_recipients'])
    
    def send_single_email(self, recipient_email: str, recipient_name: str, 
                         subject: str, content: str, from_name: str, 
                         from_email: str) -> Tuple[bool, str, str]:
        """
        Send a single email via Resend
        Returns: (success, email_id_or_error, error_message)
        """
        try:
            # Use the verified email address from FastAPI (which works)
            # Always use the verified domain to avoid authentication issues
            verified_from_email = "onboarding@lordevs.com"
            verified_from_name = from_name or "LinguaFlex"
            
            # Prepare email data (matching FastAPI implementation)
            email_data = {
                "from": f"{verified_from_name} <{verified_from_email}>",
                "to": [recipient_email],
                "subject": subject,
                "html": self._format_email_content(content, recipient_name)
            }
            
            # Send email via Resend (matching FastAPI implementation exactly)
            response = resend.Emails.send(email_data)
            
            # Check if response contains an ID (Resend returns a dict with 'id' key)
            if response and isinstance(response, dict) and 'id' in response:
                email_id = response['id']
                return True, email_id, ""
            else:
                error_msg = f"Invalid response from Resend: {response}"
                return False, "", error_msg
        
        except Exception as e:
            error_message = str(e)
            return False, "", error_message
    
    def get_specific_students(self, student_emails: List[str]) -> List[Dict[str, str]]:
        """
        Get specific students by their email addresses
        Returns list of dictionaries with email and name
        """
        students = User.objects.filter(
            role=User.Role.STUDENT,
            email__in=student_emails
        ).select_related('profile')
        
        student_list = []
        for student in students:
            student_data = {
                'email': student.email,
                'name': student.get_full_name() or student.username
            }
            student_list.append(student_data)
        
        return student_list
    
    def send_campaign_to_specific_students(self, campaign: Campaign, student_emails: List[str]) -> Dict[str, any]:
        """
        Send campaign to specific students by email addresses
        Returns dictionary with sending results
        """
        # Check if campaign can be sent (allow draft or failed campaigns for targeted sending)
        if campaign.status not in [Campaign.StatusChoices.DRAFT, Campaign.StatusChoices.FAILED]:
            return {
                'success': False,
                'error': f'Campaign cannot be sent. Current status: {campaign.status}. Only draft or failed campaigns can be sent to specific students.'
            }
        
        # Validate student emails
        if not student_emails:
            return {
                'success': False,
                'error': 'No student emails provided'
            }
        
        # Update campaign status to sending
        campaign.status = Campaign.StatusChoices.SENDING
        campaign.save(update_fields=['status'])
        
        try:
            # Get specific students
            students = self.get_specific_students(student_emails)
            
            if not students:
                campaign.status = Campaign.StatusChoices.FAILED
                campaign.save(update_fields=['status'])
                return {
                    'success': False,
                    'error': 'No valid students found with the provided email addresses'
                }
            
            # Check for missing students
            found_emails = [student['email'] for student in students]
            missing_emails = [email for email in student_emails if email not in found_emails]
            
            # Create campaign recipients for found students
            self.create_campaign_recipients(campaign, students)
            
            # Send emails to all recipients
            sent_count = 0
            failed_count = 0
            
            for recipient in campaign.recipients.all():
                success, email_id, error_msg = self.send_single_email(
                    recipient_email=recipient.student_email,
                    recipient_name=recipient.student_name,
                    subject=campaign.subject,
                    content=campaign.content,
                    from_name=campaign.from_name,
                    from_email=campaign.from_email
                )
                
                if success:
                    # Update recipient status
                    recipient.status = CampaignRecipient.DeliveryStatus.SENT
                    recipient.resend_email_id = email_id
                    recipient.sent_at = timezone.now()
                    sent_count += 1
                else:
                    # Update recipient with error
                    recipient.status = CampaignRecipient.DeliveryStatus.FAILED
                    recipient.error_message = error_msg
                    failed_count += 1
                
                recipient.save()
            
            # Update campaign status based on results
            if sent_count > 0:
                campaign.status = Campaign.StatusChoices.SENT
                campaign.sent_at = timezone.now()
            else:
                campaign.status = Campaign.StatusChoices.FAILED
            
            campaign.save(update_fields=['status', 'sent_at'])
            
            return {
                'success': True,
                'sent_count': sent_count,
                'failed_count': failed_count,
                'total_recipients': len(students),
                'missing_students': missing_emails,
                'campaign_id': campaign.id
            }
        
        except Exception as e:
            # Mark campaign as failed
            campaign.status = Campaign.StatusChoices.FAILED
            campaign.save(update_fields=['status'])
            
            return {
                'success': False,
                'error': f'Failed to send campaign: {str(e)}'
            }

    def send_campaign(self, campaign: Campaign) -> Dict[str, any]:
        """
        Send campaign to all students
        Returns dictionary with sending results
        """
        if not campaign.can_be_sent:
            return {
                'success': False,
                'error': f'Campaign cannot be sent. Current status: {campaign.status}'
            }
        
        # Update campaign status to sending
        campaign.status = Campaign.StatusChoices.SENDING
        campaign.save(update_fields=['status'])
        
        try:
            # Get all students
            students = self.get_all_students()
            
            if not students:
                campaign.status = Campaign.StatusChoices.FAILED
                campaign.save(update_fields=['status'])
                return {
                    'success': False,
                    'error': 'No students found in the system'
                }
            
            # Create campaign recipients
            self.create_campaign_recipients(campaign, students)
            
            # Send emails to all recipients
            sent_count = 0
            failed_count = 0
            
            for recipient in campaign.recipients.all():
                success, email_id, error_msg = self.send_single_email(
                    recipient_email=recipient.student_email,
                    recipient_name=recipient.student_name,
                    subject=campaign.subject,
                    content=campaign.content,
                    from_name=campaign.from_name,
                    from_email=campaign.from_email
                )
                
                if success:
                    # Update recipient status
                    recipient.status = CampaignRecipient.DeliveryStatus.SENT
                    recipient.resend_email_id = email_id
                    recipient.sent_at = timezone.now()
                    sent_count += 1
                else:
                    # Update recipient with error
                    recipient.status = CampaignRecipient.DeliveryStatus.FAILED
                    recipient.error_message = error_msg
                    failed_count += 1
                
                recipient.save()
            
            # Update campaign status based on results
            if sent_count > 0:
                campaign.status = Campaign.StatusChoices.SENT
                campaign.sent_at = timezone.now()
            else:
                campaign.status = Campaign.StatusChoices.FAILED
            
            campaign.save(update_fields=['status', 'sent_at'])
            
            return {
                'success': True,
                'sent_count': sent_count,
                'failed_count': failed_count,
                'total_recipients': len(students),
                'campaign_id': campaign.id
            }
        
        except Exception as e:
            # Mark campaign as failed
            campaign.status = Campaign.StatusChoices.FAILED
            campaign.save(update_fields=['status'])
            
            return {
                'success': False,
                'error': f'Failed to send campaign: {str(e)}'
            }
    
    def _format_email_content(self, content: str, recipient_name: str) -> str:
        """
        Format email content with basic HTML structure and personalization
        """
        # Replace placeholders
        formatted_content = content.replace('{{student_name}}', recipient_name)
        formatted_content = formatted_content.replace('{{name}}', recipient_name)
        
        # Convert line breaks to HTML
        formatted_content = formatted_content.replace('\n', '<br>')
        
        # Wrap in basic HTML structure
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Message from Your Teacher</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    border-bottom: 2px solid #007bff;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .content {{
                    margin-bottom: 20px;
                }}
                .footer {{
                    border-top: 1px solid #ddd;
                    padding-top: 10px;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Message from Your Teacher</h2>
            </div>
            <div class="content">
                <p>Hello {recipient_name},</p>
                {formatted_content}
            </div>
            <div class="footer">
                <p>This email was sent through LinguaFlex platform.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def get_campaign_stats(self, teacher_profile) -> Dict[str, any]:
        """
        Get campaign statistics for a teacher
        """
        campaigns = Campaign.objects.filter(teacher=teacher_profile)
        
        stats = {
            'total_campaigns': campaigns.count(),
            'draft_campaigns': campaigns.filter(status=Campaign.StatusChoices.DRAFT).count(),
            'sent_campaigns': campaigns.filter(status=Campaign.StatusChoices.SENT).count(),
            'failed_campaigns': campaigns.filter(status=Campaign.StatusChoices.FAILED).count(),
            'total_emails_sent': sum(c.total_recipients for c in campaigns.filter(status=Campaign.StatusChoices.SENT)),
            'last_campaign_date': None,
            'most_recent_campaign': None
        }
        
        # Get most recent campaign
        recent_campaign = campaigns.first()
        if recent_campaign:
            stats['last_campaign_date'] = recent_campaign.created_at
            stats['most_recent_campaign'] = recent_campaign.title
        
        return stats
