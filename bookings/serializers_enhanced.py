# bookings/serializers_enhanced.py
from rest_framework import serializers
from .models import TeacherAvailability, SessionBooking, SessionFeedback
from core.serializers import UserSerializer
from accounts.models import UserProfile, TeacherProfile

class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TeacherAvailability
        fields = ['id', 'teacher', 'teacher_name', 'day_of_week', 'start_time', 
                 'end_time', 'is_recurring', 'date']
        read_only_fields = ['teacher', 'teacher_name']

    def get_teacher_name(self, obj):
        return obj.teacher.get_full_name()

class BookingRequestSerializer(serializers.Serializer):
    """Serializer for creating booking requests"""
    teacher_id = serializers.UUIDField()
    start_time = serializers.DateTimeField()
    duration = serializers.IntegerField(default=60, min_value=30, max_value=180)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

class SessionBookingSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    student_email = serializers.SerializerMethodField()
    teacher_email = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_reschedule = serializers.SerializerMethodField()
    zoom_info = serializers.SerializerMethodField()
    
    class Meta:
        model = SessionBooking
        fields = [
            'id', 'student', 'teacher', 'student_name', 'teacher_name',
            'student_email', 'teacher_email', 'start_time', 'end_time',
            'duration_minutes', 'status', 'zoom_meeting_id', 'zoom_join_url',
            'notes', 'cancellation_reason', 'created_at', 'updated_at',
            'can_cancel', 'can_reschedule', 'zoom_info'
        ]
        read_only_fields = [
            'id', 'student', 'status', 'zoom_meeting_id', 'zoom_join_url',
            'created_at', 'updated_at', 'student_name', 'teacher_name',
            'student_email', 'teacher_email', 'duration_minutes',
            'can_cancel', 'can_reschedule', 'zoom_info'
        ]

    def get_student_name(self, obj):
        return obj.student.get_full_name()

    def get_teacher_name(self, obj):
        return obj.teacher.get_full_name()
    
    def get_student_email(self, obj):
        return obj.student.email
    
    def get_teacher_email(self, obj):
        return obj.teacher.email

    def get_duration_minutes(self, obj):
        return int((obj.end_time - obj.start_time).total_seconds() / 60)
    
    def get_can_cancel(self, obj):
        """Check if the current user can cancel this booking"""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        user = request.user
        return (
            user in [obj.student, obj.teacher] and 
            obj.status in ['PENDING', 'CONFIRMED']
        )
    
    def get_can_reschedule(self, obj):
        """Check if the current user can reschedule this booking"""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        
        user = request.user
        return (
            user in [obj.student, obj.teacher] and 
            obj.status in ['PENDING', 'CONFIRMED']
        )
    
    def get_zoom_info(self, obj):
        """Return Zoom meeting information if available"""
        if obj.zoom_meeting_id and obj.zoom_join_url:
            return {
                'meeting_id': obj.zoom_meeting_id,
                'join_url': obj.zoom_join_url,
                'has_meeting': True
            }
        return {
            'meeting_id': None,
            'join_url': None,
            'has_meeting': False
        }

class BookingConfirmationSerializer(serializers.Serializer):
    """Serializer for booking confirmation response"""
    message = serializers.CharField()
    booking = SessionBookingSerializer()
    zoom_info = serializers.DictField()

class AvailableSlotSerializer(serializers.Serializer):
    """Serializer for available time slots"""
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    datetime_start = serializers.CharField()
    datetime_end = serializers.CharField()

class TeacherScheduleSerializer(serializers.Serializer):
    """Serializer for teacher schedule response"""
    teacher_id = serializers.UUIDField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    bookings = serializers.ListField()

class SessionFeedbackSerializer(serializers.ModelSerializer):
    booking_info = serializers.SerializerMethodField()
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SessionFeedback
        fields = [
            'id', 'booking', 'booking_info', 'rating', 'comment', 
            'created_at', 'is_from_student', 'reviewer_name'
        ]
        read_only_fields = ['id', 'booking', 'created_at', 'is_from_student', 'booking_info', 'reviewer_name']

    def get_booking_info(self, obj):
        return {
            'session_date': obj.booking.start_time,
            'teacher_name': obj.booking.teacher.get_full_name(),
            'student_name': obj.booking.student.get_full_name()
        }
    
    def get_reviewer_name(self, obj):
        if obj.is_from_student:
            return obj.booking.student.get_full_name()
        else:
            return obj.booking.teacher.get_full_name()

class FeedbackCreateSerializer(serializers.ModelSerializer):
    booking_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = SessionFeedback
        fields = ['booking_id', 'rating', 'comment']

class TeacherProfileWithAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for teacher profiles with availability info"""
    user = UserSerializer(read_only=True)
    next_available_slot = serializers.SerializerMethodField()
    hourly_rate = serializers.SerializerMethodField()
    total_sessions = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = TeacherProfile
        fields = [
            'id', 'user', 'qualification', 'experience_years', 
            'certificates', 'about', 'next_available_slot', 
            'hourly_rate', 'total_sessions', 'average_rating'
        ]
    
    def get_next_available_slot(self, obj):
        """Get the next available time slot for this teacher"""
        # This would require more complex logic to find the next available slot
        # For now, return None - can be implemented based on requirements
        return None
    
    def get_hourly_rate(self, obj):
        """Get teacher's hourly rate from the Teacher model"""
        try:
            teacher = obj.user_profile.user.teacher_set.first()
            return float(teacher.hourly_rate) if teacher else None
        except:
            return None
    
    def get_total_sessions(self, obj):
        """Get total number of completed sessions"""
        return SessionBooking.objects.filter(
            teacher=obj.user_profile.user,
            status='COMPLETED'
        ).count()
    
    def get_average_rating(self, obj):
        """Get average rating from student feedback"""
        feedbacks = SessionFeedback.objects.filter(
            booking__teacher=obj.user_profile.user,
            is_from_student=True
        )
        if feedbacks.exists():
            total_rating = sum(feedback.rating for feedback in feedbacks)
            return round(total_rating / feedbacks.count(), 1)
        return None
