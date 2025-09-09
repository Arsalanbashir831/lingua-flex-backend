from rest_framework import serializers
from .models import TeacherAvailability, SessionBooking, SessionFeedback

class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAvailability
        fields = '__all__'
        read_only_fields = ['teacher']

    def create(self, validated_data):
        validated_data['teacher'] = self.context['request'].user
        return super().create(validated_data)

class BulkTeacherAvailabilitySerializer(serializers.Serializer):
    """Serializer for bulk creation of teacher availability slots"""
    availabilities = TeacherAvailabilitySerializer(many=True)
    
    def validate_availabilities(self, value):
        """Validate that all availability data is correct"""
        if not value:
            raise serializers.ValidationError("At least one availability slot is required")
        
        # Check for duplicate day_of_week entries
        days_seen = set()
        for availability in value:
            day = availability.get('day_of_week')
            if day in days_seen:
                raise serializers.ValidationError(f"Duplicate availability for day {day}")
            days_seen.add(day)
        
        return value
    
    def create(self, validated_data):
        """Create multiple availability slots"""
        teacher = self.context['request'].user
        availabilities_data = validated_data['availabilities']
        
        created_availabilities = []
        for availability_data in availabilities_data:
            availability_data['teacher'] = teacher
            # Check if availability already exists for this teacher/day/time
            existing = TeacherAvailability.objects.filter(
                teacher=teacher,
                day_of_week=availability_data['day_of_week'],
                start_time=availability_data['start_time'],
                end_time=availability_data['end_time'],
                is_recurring=availability_data.get('is_recurring', True)
            ).first()
            
            if existing:
                # Update existing availability
                for key, value in availability_data.items():
                    if key != 'teacher':
                        setattr(existing, key, value)
                existing.save()
                created_availabilities.append(existing)
            else:
                # Create new availability
                availability = TeacherAvailability.objects.create(**availability_data)
                created_availabilities.append(availability)
        
        return created_availabilities
    class Meta:
        model = TeacherAvailability
        fields = '__all__'
        read_only_fields = ['teacher']

    def create(self, validated_data):
        validated_data['teacher'] = self.context['request'].user
        return super().create(validated_data)

class SessionBookingSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    duration_hours = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, read_only=True)

    class Meta:
        model = SessionBooking
        fields = '__all__'
        read_only_fields = ['student', 'status', 'zoom_meeting_id', 'zoom_join_url', 'duration_hours']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}"

    def validate(self, attrs):
        """Calculate duration_hours automatically from start_time and end_time"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError("Start time must be before end time")
            
            # Auto-calculate duration in hours
            duration_seconds = (end_time - start_time).total_seconds()
            duration_hours = round(duration_seconds / 3600, 2)  # Convert to hours with 2 decimal places
            attrs['duration_hours'] = duration_hours
            
            # Set scheduled_datetime if not provided
            if not attrs.get('scheduled_datetime'):
                attrs['scheduled_datetime'] = start_time
        
        return attrs

    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        validated_data['status'] = 'PENDING'
        return super().create(validated_data)

class SessionFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionFeedback
        fields = '__all__'
        read_only_fields = ['booking']

    def validate(self, attrs):
        user = self.context['request'].user
        booking = attrs.get('booking')
        
        # Check if the user is either the student or teacher of the booking
        if user not in [booking.student, booking.teacher]:
            raise serializers.ValidationError("You can only provide feedback for your own sessions")
        
        # Set is_from_student based on the user's role
        attrs['is_from_student'] = (user == booking.student)
        
        return attrs
