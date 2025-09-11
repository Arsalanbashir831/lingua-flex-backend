# bookings/zoom_service.py
"""
Zoom API integration service for creating and managing Zoom meetings
Uses latest Zoom Server-to-Server OAuth authentication
"""
import requests
import base64
import time
from datetime import datetime, timedelta
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ZoomService:
    def __init__(self):
        self.account_id = getattr(settings, 'ZOOM_ACCOUNT_ID', '')
        self.client_id = getattr(settings, 'ZOOM_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'ZOOM_CLIENT_SECRET', '')
        self.base_url = 'https://api.zoom.us/v2'
        self.token_url = 'https://zoom.us/oauth/token'
        self._access_token = None
        self._token_expires_at = 0
        
    def _get_user_display_name(self, user):
        """Get a display name for the user, handling various name configurations"""
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            if user.first_name and user.last_name:
                return f"{user.first_name} {user.last_name}"
            elif user.first_name:
                return user.first_name
            elif user.last_name:
                return user.last_name
        
        # Fallback to email username part
        if hasattr(user, 'email') and user.email:
            return user.email.split('@')[0]
        
        # Last resort fallback
        return str(user)
        
    def get_access_token(self):
        """Get OAuth access token using Server-to-Server OAuth"""
        
        # Check if we have a valid token
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        
        if not all([self.account_id, self.client_id, self.client_secret]):
            raise Exception("Zoom OAuth credentials not configured properly")
        
        # Create authorization header
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'account_credentials',
            'account_id': self.account_id
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data['access_token']
                # Set expiry time with 5 minute buffer
                expires_in = token_data.get('expires_in', 3600)
                self._token_expires_at = time.time() + expires_in - 300
                
                logger.info("Zoom access token obtained successfully")
                return self._access_token
            else:
                error_msg = f"Failed to get Zoom access token: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error getting Zoom token: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def create_meeting(self, booking):
        """Create a Zoom meeting for a booking"""
        try:
            # Get access token
            access_token = self.get_access_token()
            
            # Use a default host email instead of teacher's email
            host_email = "ammarmukhtar@lordevs.com"  # Your actual Zoom email
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            meeting_data = {
                'topic': f"Language Session with {booking.teacher.first_name} {booking.teacher.last_name}",
                'type': 2,  # Scheduled meeting
                'start_time': booking.start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'duration': int((booking.end_time - booking.start_time).total_seconds() / 60),
                'timezone': 'UTC',
                'settings': {
                    'host_video': True,
                    'participant_video': True,
                    'join_before_host': True,
                    'mute_upon_entry': True,
                    'waiting_room': False,
                    'audio': 'both',
                    'auto_recording': 'none'
                }
            }
            
            # Create meeting using HTTP request
            url = f'{self.base_url}/users/{host_email}/meetings'
            response = requests.post(url, json=meeting_data, headers=headers, timeout=30)
            
            if response.status_code == 201:
                meeting_info = response.json()
                logger.info(f"Zoom meeting created successfully: {meeting_info['id']}")
                return {
                    'success': True,
                    'meeting_id': meeting_info['id'],
                    'join_url': meeting_info['join_url'],
                    'start_url': meeting_info['start_url'],
                    'password': meeting_info.get('password', '')
                }
            else:
                error_msg = f'{response.status_code} - {response.text}'
                logger.error(f"Failed to create Zoom meeting: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating Zoom meeting: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def update_meeting(self, meeting_id, booking):
        """Update an existing Zoom meeting using Server-to-Server OAuth"""
        try:
            access_token = self.get_access_token()
        except Exception as e:
            logger.error(f"Failed to get access token for update: {str(e)}")
            return False
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        duration = int((booking.end_time - booking.start_time).total_seconds() / 60)
        start_time = booking.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Get display names safely
        teacher_name = self._get_user_display_name(booking.teacher)
        student_name = self._get_user_display_name(booking.student)
        
        meeting_data = {
            'topic': f'Language Session: {teacher_name} & {student_name}',
            'start_time': start_time,
            'duration': duration,
            'timezone': 'UTC',
            'agenda': f'Updated: Language learning session between {teacher_name} and {student_name}'
        }
        
        url = f'{self.base_url}/meetings/{meeting_id}'
        
        try:
            response = requests.patch(url, json=meeting_data, headers=headers, timeout=30)
            
            if response.status_code == 204:
                logger.info(f"Zoom meeting updated successfully: {meeting_id}")
                return True
            else:
                logger.error(f"Failed to update Zoom meeting {meeting_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating Zoom meeting {meeting_id}: {str(e)}")
            return False
    
    def delete_meeting(self, meeting_id):
        """Delete a Zoom meeting using Server-to-Server OAuth"""
        try:
            access_token = self.get_access_token()
        except Exception as e:
            logger.error(f"Failed to get access token for delete: {str(e)}")
            return False
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        url = f'{self.base_url}/meetings/{meeting_id}'
        
        try:
            response = requests.delete(url, headers=headers, timeout=30)
            
            if response.status_code == 204:
                logger.info(f"Zoom meeting deleted successfully: {meeting_id}")
                return True
            else:
                logger.error(f"Failed to delete Zoom meeting {meeting_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting Zoom meeting {meeting_id}: {str(e)}")
            return False
    
    def get_meeting_info(self, meeting_id):
        """Get information about a Zoom meeting using Server-to-Server OAuth"""
        try:
            access_token = self.get_access_token()
        except Exception as e:
            logger.error(f"Failed to get access token for meeting info: {str(e)}")
            return None
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        url = f'{self.base_url}/meetings/{meeting_id}'
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Zoom meeting info retrieved successfully: {meeting_id}")
                return response.json()
            else:
                logger.error(f"Failed to get Zoom meeting info {meeting_id}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Zoom meeting info {meeting_id}: {str(e)}")
            return None
    
    def list_meetings(self, user_email, page_size=30):
        """List meetings for a specific user"""
        try:
            access_token = self.get_access_token()
        except Exception as e:
            logger.error(f"Failed to get access token for listing meetings: {str(e)}")
            return None
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        url = f'{self.base_url}/users/{user_email}/meetings'
        params = {
            'type': 'scheduled',
            'page_size': page_size
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Meetings listed successfully for user: {user_email}")
                return response.json()
            else:
                logger.error(f"Failed to list meetings for {user_email}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error listing meetings for {user_email}: {str(e)}")
            return None
