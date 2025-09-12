from rest_framework import viewsets, status, permissions
from django.db import models
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from .models import TeacherAvailability, SessionBooking, SessionFeedback
from .serializers import TeacherAvailabilitySerializer, SessionBookingSerializer, SessionFeedbackSerializer
from .zoom_service import ZoomService
import logging

logger = logging.getLogger(__name__)

class TeacherAvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.action == 'list':
            teacher_id = self.request.query_params.get('teacher_id')
            if teacher_id:
                return TeacherAvailability.objects.filter(teacher_id=teacher_id)
        return TeacherAvailability.objects.filter(teacher=self.request.user)

    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        teacher_id = request.query_params.get('teacher_id')
        date_str = request.query_params.get('date')
        
        if not teacher_id or not date_str:
            return Response(
                {"error": "Both teacher_id and date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get recurring availability for the day of week
        day_of_week = date.weekday()
        availabilities = TeacherAvailability.objects.filter(
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            is_recurring=True
        )

        # Get any specific availability for the date
        specific_availabilities = TeacherAvailability.objects.filter(
            teacher_id=teacher_id,
            date=date,
            is_recurring=False
        )

        # Combine and format all available time slots
        available_slots = []
        for availability in list(availabilities) + list(specific_availabilities):
            available_slots.append({
                'start_time': availability.start_time.strftime('%H:%M'),
                'end_time': availability.end_time.strftime('%H:%M')
            })

        return Response(available_slots)

class SessionBookingViewSet(viewsets.ModelViewSet):
    serializer_class = SessionBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Show both student and teacher bookings with payment data
        return SessionBooking.objects.filter(
            models.Q(student=user) | models.Q(teacher=user)
        ).select_related('student', 'teacher', 'gig', 'payment').order_by('-start_time')

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            # Delete Zoom meeting if it exists
            if booking.zoom_meeting_id:
                zoom_service = ZoomService()
                zoom_service.delete_meeting(booking.zoom_meeting_id)
                logger.info(f"Deleted Zoom meeting {booking.zoom_meeting_id} for cancelled booking {booking.id}")
            
            booking.cancel(reason)
            return Response({
                'message': 'Booking cancelled successfully',
                'booking': SessionBookingSerializer(booking).data
            })
        except Exception as e:
            logger.error(f"Error cancelling booking {booking.id}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule a booking and update the Zoom meeting"""
        booking = self.get_object()
        
        # Check if user can reschedule this booking
        if request.user not in [booking.teacher, booking.student]:
            return Response(
                {'error': 'Only the teacher or student can reschedule this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status == 'CANCELLED':
            return Response(
                {'error': 'Cannot reschedule a cancelled booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get new times from request
        new_start_time = request.data.get('new_start_time')
        new_end_time = request.data.get('new_end_time')
        reason = request.data.get('reason', '')
        
        if not new_start_time or not new_end_time:
            return Response(
                {'error': 'Both new_start_time and new_end_time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Parse the new times
            from django.utils.dateparse import parse_datetime
            new_start = parse_datetime(new_start_time)
            new_end = parse_datetime(new_end_time)
            
            if not new_start or not new_end:
                return Response(
                    {'error': 'Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if new_start >= new_end:
                return Response(
                    {'error': 'Start time must be before end time'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update booking times
            old_start = booking.start_time
            old_end = booking.end_time
            
            booking.start_time = new_start
            booking.end_time = new_end
            booking.save()
            
            # Update Zoom meeting if it exists
            if booking.zoom_meeting_id:
                zoom_service = ZoomService()
                success = zoom_service.update_meeting(booking.zoom_meeting_id, booking)
                
                if success:
                    logger.info(f"Updated Zoom meeting {booking.zoom_meeting_id} for booking {booking.id}")
                else:
                    logger.warning(f"Failed to update Zoom meeting {booking.zoom_meeting_id}, but booking was rescheduled")
            
            return Response({
                'message': 'Booking rescheduled successfully',
                'changes': {
                    'old_start_time': old_start,
                    'old_end_time': old_end,
                    'new_start_time': new_start,
                    'new_end_time': new_end,
                    'reason': reason
                },
                'booking': SessionBookingSerializer(booking).data
            })
            
        except Exception as e:
            logger.error(f"Error rescheduling booking {booking.id}: {str(e)}")
            return Response(
                {'error': f"Failed to reschedule booking: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        
        if booking.status != 'PENDING':
            return Response(
                {'error': 'Only pending sessions can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.user != booking.teacher:
            return Response(
                {'error': 'Only teachers can confirm sessions'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Integrate with Zoom API to create meeting
        zoom_service = ZoomService()
        try:
            zoom_result = zoom_service.create_meeting(booking)
            
            if zoom_result.get('success'):
                booking.zoom_meeting_id = zoom_result['meeting_id']
                booking.zoom_join_url = zoom_result['join_url']
                booking.zoom_start_url = zoom_result['start_url']
                booking.zoom_password = zoom_result.get('password', '')
                booking.status = 'CONFIRMED'
                booking.save()
                
                logger.info(f"Zoom meeting created for booking {booking.id}: {zoom_result['meeting_id']}")
                
                return Response({
                    'message': 'Booking confirmed successfully',
                    'booking': SessionBookingSerializer(booking).data
                })
            else:
                return Response(
                    {'error': f"Error creating Zoom meeting: {zoom_result.get('error', 'Unknown error')}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error confirming booking {booking.id}: {str(e)}")
            return Response(
                {'error': f"Error creating Zoom meeting: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a booking as completed - can be done by both student and teacher"""
        booking = self.get_object()
        
        # Check if booking can be marked as completed
        if booking.status not in ['CONFIRMED']:
            return Response(
                {'error': 'Only confirmed sessions can be marked as completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if payment has been made
        if booking.payment_status != 'PAID':
            return Response(
                {'error': 'Session can only be marked as completed after payment is made'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is either student or teacher of this booking
        if request.user not in [booking.student, booking.teacher]:
            return Response(
                {'error': 'Only the student or teacher can mark the session as completed'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Optional: Check if session time has passed (business rule)
        current_time = timezone.now()
        if booking.end_time > current_time:
            return Response(
                {
                    'error': 'Cannot mark session as completed before its scheduled end time',
                    'details': {
                        'session_end_time': booking.end_time.isoformat(),
                        'current_time': current_time.isoformat(),
                        'time_remaining': str(booking.end_time - current_time)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update booking status
            booking.status = 'COMPLETED'
            booking.save()
            
            logger.info(f"Booking {booking.id} marked as completed by user {request.user.id}")
            
            return Response({
                'success': True,
                'message': 'Session marked as completed successfully',
                'booking': SessionBookingSerializer(booking).data,
                'completed_by': 'student' if request.user == booking.student else 'teacher',
                'completed_at': booking.updated_at
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error completing booking {booking.id}: {str(e)}")
            return Response(
                {'error': f"Error marking session as completed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def create_meeting(self, request, pk=None):
        """Create or recreate Zoom meeting for a booking"""
        booking = self.get_object()
        
        # Check if user is either the teacher or student of this booking
        if request.user not in [booking.teacher, booking.student]:
            return Response(
                {'error': 'Only the teacher or student can create meeting links for this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if booking is in a valid state for meeting creation
        if booking.status == 'CANCELLED':
            return Response(
                {'error': 'Cannot create meeting for cancelled booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        zoom_service = ZoomService()
        try:
            # If meeting already exists, delete it first (to recreate)
            if booking.zoom_meeting_id:
                logger.info(f"Deleting existing Zoom meeting {booking.zoom_meeting_id} for booking {booking.id}")
                zoom_service.delete_meeting(booking.zoom_meeting_id)
            
            # Create new meeting
            zoom_result = zoom_service.create_meeting(booking)
            
            if zoom_result.get('success'):
                booking.zoom_meeting_id = zoom_result['meeting_id']
                booking.zoom_join_url = zoom_result['join_url']
                booking.zoom_start_url = zoom_result['start_url']
                booking.zoom_password = zoom_result.get('password', '')
                
                # Update status to confirmed if it was pending
                if booking.status == 'PENDING':
                    booking.status = 'CONFIRMED'
                
                booking.save()
                
                logger.info(f"Zoom meeting created for booking {booking.id}: {zoom_result['meeting_id']}")
                
                return Response({
                    'message': 'Zoom meeting created successfully',
                    'meeting_details': {
                        'meeting_id': booking.zoom_meeting_id,
                        'join_url': booking.zoom_join_url,
                        'start_url': booking.zoom_start_url,
                        'password': booking.zoom_password,
                        'host_email': zoom_result.get('host_email', booking.teacher.email)
                    },
                    'booking': SessionBookingSerializer(booking).data
                })
            else:
                return Response(
                    {'error': f"Failed to create Zoom meeting: {zoom_result.get('error', 'Unknown error')}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error creating meeting for booking {booking.id}: {str(e)}")
            return Response(
                {'error': f"Error creating Zoom meeting: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def meeting_info(self, request, pk=None):
        """Get Zoom meeting information for a booking"""
        booking = self.get_object()
        
        # Check if user is either the teacher or student of this booking
        if request.user not in [booking.teacher, booking.student]:
            return Response(
                {'error': 'Only the teacher or student can access meeting info for this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not booking.zoom_meeting_id:
            return Response(
                {'error': 'No Zoom meeting associated with this booking'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'meeting_details': {
                'meeting_id': booking.zoom_meeting_id,
                'join_url': booking.zoom_join_url,
                'start_url': booking.zoom_start_url,
                'password': booking.zoom_password,
                'host_email': booking.teacher.email,
                'booking_id': booking.id,
                'start_time': booking.start_time,
                'end_time': booking.end_time,
                'status': booking.status
            }
        })

class SessionFeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = SessionFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return SessionFeedback.objects.filter(
            models.Q(booking__student=user) | models.Q(booking__teacher=user)
        )
