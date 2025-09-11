from rest_framework import serializers
from .models import Campaign, CampaignRecipient
from accounts.models import TeacherProfile


class CampaignRecipientSerializer(serializers.ModelSerializer):
    """Serializer for campaign recipients"""
    
    class Meta:
        model = CampaignRecipient
        fields = [
            'id', 'student_email', 'student_name', 'status',
            'sent_at', 'delivered_at', 'error_message'
        ]
        read_only_fields = ['id', 'sent_at', 'delivered_at']


class CampaignListSerializer(serializers.ModelSerializer):
    """Serializer for listing campaigns"""
    
    teacher_name = serializers.CharField(source='teacher.user_profile.user.get_full_name', read_only=True)
    recipients_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'title', 'subject', 'status', 'total_recipients',
            'teacher_name', 'recipients_count', 'created_at', 'sent_at'
        ]
        read_only_fields = ['id', 'created_at', 'sent_at', 'teacher_name']
    
    def get_recipients_count(self, obj):
        """Get the count of recipients for this campaign"""
        return obj.recipients.count()


class CampaignDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed campaign view"""
    
    teacher_name = serializers.CharField(source='teacher.user_profile.user.get_full_name', read_only=True)
    teacher_email = serializers.EmailField(source='teacher.user_profile.user.email', read_only=True)
    recipients = CampaignRecipientSerializer(many=True, read_only=True)
    recipients_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'title', 'subject', 'content', 'status', 'total_recipients',
            'from_name', 'from_email', 'teacher_name', 'teacher_email',
            'recipients_count', 'recipients', 'notes', 'created_at', 
            'updated_at', 'sent_at'
        ]
        read_only_fields = [
            'id', 'teacher_name', 'teacher_email', 'recipients', 
            'recipients_count', 'created_at', 'updated_at', 'sent_at'
        ]
    
    def get_recipients_count(self, obj):
        """Get the count of recipients for this campaign"""
        return obj.recipients.count()


class CampaignCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating campaigns"""
    
    class Meta:
        model = Campaign
        fields = [
            'title', 'subject', 'content', 'from_name', 'from_email', 'notes'
        ]
    
    def validate_title(self, value):
        """Validate campaign title"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Campaign title must be at least 3 characters long.")
        return value.strip()
    
    def validate_subject(self, value):
        """Validate email subject"""
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Email subject must be at least 5 characters long.")
        return value.strip()
    
    def validate_content(self, value):
        """Validate email content"""
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Email content must be at least 20 characters long.")
        return value.strip()
    
    def create(self, validated_data):
        """Create a new campaign"""
        # Get teacher from request user
        teacher = TeacherProfile.objects.get(user_profile__user=self.context['request'].user)
        validated_data['teacher'] = teacher
        return super().create(validated_data)


class CampaignSendSerializer(serializers.Serializer):
    """Serializer for sending campaigns"""
    
    confirm_send = serializers.BooleanField(
        required=True,
        help_text="Must be True to confirm sending the campaign"
    )
    
    def validate_confirm_send(self, value):
        """Validate confirmation"""
        if not value:
            raise serializers.ValidationError("You must confirm sending by setting confirm_send to True.")
        return value


class CampaignSendToSpecificStudentsSerializer(serializers.Serializer):
    """Serializer for sending campaigns to specific students"""
    
    confirm_send = serializers.BooleanField(
        required=True,
        help_text="Must be True to confirm sending the campaign"
    )
    
    student_emails = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1,
        max_length=500,  # Reasonable limit to prevent abuse
        help_text="List of student email addresses to send the campaign to"
    )
    
    def validate_confirm_send(self, value):
        """Validate confirmation"""
        if not value:
            raise serializers.ValidationError("You must confirm sending by setting confirm_send to True.")
        return value
    
    def validate_student_emails(self, value):
        """Validate student emails"""
        if not value:
            raise serializers.ValidationError("At least one student email is required.")
        
        # Remove duplicates while preserving order
        unique_emails = []
        seen = set()
        for email in value:
            email_lower = email.lower()
            if email_lower not in seen:
                seen.add(email_lower)
                unique_emails.append(email)
        
        if len(unique_emails) > 500:
            raise serializers.ValidationError("Maximum 500 student emails allowed per campaign.")
        
        return unique_emails


class CampaignStatsSerializer(serializers.Serializer):
    """Serializer for campaign statistics"""
    
    total_campaigns = serializers.IntegerField()
    draft_campaigns = serializers.IntegerField()
    sent_campaigns = serializers.IntegerField()
    failed_campaigns = serializers.IntegerField()
    total_emails_sent = serializers.IntegerField()
    last_campaign_date = serializers.DateTimeField()
    most_recent_campaign = serializers.CharField()
