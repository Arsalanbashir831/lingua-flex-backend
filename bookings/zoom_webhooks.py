# bookings/zoom_webhooks.py
"""
Zoom Webhook handlers for automatic meeting status updates
"""
import json
import hmac
import hashlib
import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from .models import SessionBooking
from .zoom_service import ZoomService

logger = logging.getLogger(__name__)

def verify_zoom_webhook(request):
    """
    Verify that the webhook request is from Zoom
    """
    webhook_secret = getattr(settings, 'ZOOM_WEBHOOK_SECRET', '')
    if not webhook_secret:
        logger.warning("Zoom webhook secret not configured")
        return True  # Skip verification if not configured
    
    # Get the signature from headers
    signature = request.headers.get('X-Zm-Signature', '')
    if not signature:
        logger.error("Missing Zoom signature in webhook request")
        return False
    
    # Extract timestamp and hash
    try:
        timestamp, hash_value = signature.split('=')
        if timestamp != 't' or not hash_value:
            logger.error("Invalid signature format")
            return False
    except ValueError:
        logger.error("Invalid signature format")
        return False
    
    # Create expected signature
    payload = request.body.decode('utf-8')
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        f"v0:{timestamp}:{payload}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    if not hmac.compare_digest(f"v0={expected_signature}", signature):
        logger.error("Invalid webhook signature")
        return False
    
    return True

@csrf_exempt
@require_POST
def zoom_webhook_handler(request):
    """
    Handle Zoom webhook events
    """
    try:
        # Verify webhook authenticity
        if not verify_zoom_webhook(request):
            return HttpResponseBadRequest("Invalid webhook signature")
        
        # Parse webhook payload
        payload = json.loads(request.body.decode('utf-8'))
        event_type = payload.get('event')
        
        logger.info(f"Received Zoom webhook: {event_type}")
        
        # Handle different event types
        if event_type == 'meeting.ended':
            handle_meeting_ended(payload)
        elif event_type == 'meeting.started':
            handle_meeting_started(payload)
        elif event_type == 'meeting.participant_joined':
            handle_participant_joined(payload)
        elif event_type == 'meeting.participant_left':
            handle_participant_left(payload)
        else:
            logger.info(f"Unhandled webhook event: {event_type}")
        
        return HttpResponse("OK", status=200)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return HttpResponseBadRequest("Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return HttpResponseBadRequest("Internal error")

def handle_meeting_ended(payload):
    """
    Handle meeting.ended webhook event
    """
    try:
        meeting_data = payload.get('payload', {}).get('object', {})
        meeting_id = meeting_data.get('id')
        
        if not meeting_id:
            logger.error("No meeting ID in webhook payload")
            return
        
        # Find the booking with this meeting ID
        try:
            booking = SessionBooking.objects.get(zoom_meeting_id=str(meeting_id))
        except SessionBooking.DoesNotExist:
            logger.warning(f"No booking found for meeting ID: {meeting_id}")
            return
        except SessionBooking.MultipleObjectsReturned:
            logger.error(f"Multiple bookings found for meeting ID: {meeting_id}")
            return
        
        # Update booking status to COMPLETED
        if booking.status in ['CONFIRMED', 'PENDING']:
            booking.status = 'COMPLETED'
            booking.save()
            
            logger.info(f"Booking {booking.id} marked as COMPLETED after Zoom meeting ended")
            
            # Optional: Send completion notifications
            send_meeting_completion_notifications(booking)
        else:
            logger.info(f"Booking {booking.id} already in status: {booking.status}")
            
    except Exception as e:
        logger.error(f"Error handling meeting ended: {str(e)}")

def handle_meeting_started(payload):
    """
    Handle meeting.started webhook event
    """
    try:
        meeting_data = payload.get('payload', {}).get('object', {})
        meeting_id = meeting_data.get('id')
        
        if not meeting_id:
            logger.error("No meeting ID in webhook payload")
            return
        
        # Find the booking with this meeting ID
        try:
            booking = SessionBooking.objects.get(zoom_meeting_id=str(meeting_id))
        except SessionBooking.DoesNotExist:
            logger.warning(f"No booking found for meeting ID: {meeting_id}")
            return
        
        # Update booking status to CONFIRMED if it was PENDING
        if booking.status == 'PENDING':
            booking.status = 'CONFIRMED'
            booking.save()
            
            logger.info(f"Booking {booking.id} confirmed after Zoom meeting started")
            
    except Exception as e:
        logger.error(f"Error handling meeting started: {str(e)}")

def handle_participant_joined(payload):
    """
    Handle participant joined event (optional - for analytics)
    """
    try:
        meeting_data = payload.get('payload', {}).get('object', {})
        meeting_id = meeting_data.get('id')
        participant = meeting_data.get('participant', {})
        
        logger.info(f"Participant {participant.get('user_name', 'Unknown')} joined meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"Error handling participant joined: {str(e)}")

def handle_participant_left(payload):
    """
    Handle participant left event (optional - for analytics)
    """
    try:
        meeting_data = payload.get('payload', {}).get('object', {})
        meeting_id = meeting_data.get('id')
        participant = meeting_data.get('participant', {})
        
        logger.info(f"Participant {participant.get('user_name', 'Unknown')} left meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"Error handling participant left: {str(e)}")

def send_meeting_completion_notifications(booking):
    """
    Send notifications when a meeting is completed
    """
    try:
        # You can implement email notifications, push notifications, etc.
        logger.info(f"Sending completion notifications for booking {booking.id}")
        
        # Example: Send email to student and teacher
        # from django.core.mail import send_mail
        # send_mail(
        #     'Session Completed',
        #     f'Your session with {booking.teacher.get_full_name()} has been completed.',
        #     'noreply@linguaflex.com',
        #     [booking.student.email],
        #     fail_silently=False,
        # )
        
    except Exception as e:
        logger.error(f"Error sending completion notifications: {str(e)}")
