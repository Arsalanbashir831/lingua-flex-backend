from django.shortcuts import get_object_or_404
from django.db import models
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from core.authentication import SupabaseTokenAuthentication
from accounts.models import TeacherProfile
from .models import Campaign, CampaignRecipient
from .serializers import (
    CampaignListSerializer, CampaignDetailSerializer, 
    CampaignCreateUpdateSerializer, CampaignSendSerializer,
    CampaignSendToSpecificStudentsSerializer, CampaignStatsSerializer
)
from .email_service import ResendEmailService


class CampaignPagination(PageNumberPagination):
    """Custom pagination for campaigns"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class TeacherCampaignListCreateView(generics.ListCreateAPIView):
    """
    List and create campaigns for authenticated teachers
    GET: List teacher's campaigns with filtering
    POST: Create new campaign
    """
    authentication_classes = [SupabaseTokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = CampaignPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CampaignCreateUpdateSerializer
        return CampaignListSerializer
    
    def get_queryset(self):
        """Get campaigns for the authenticated teacher"""
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=self.request.user)
        except TeacherProfile.DoesNotExist:
            return Campaign.objects.none()
        
        queryset = Campaign.objects.filter(teacher=teacher_profile).prefetch_related('recipients')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search in title and subject
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) | 
                models.Q(subject__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Custom create method for campaigns"""
        # Ensure user is a teacher
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
        except TeacherProfile.DoesNotExist:
            return Response({
                'error': 'Only teachers can create campaigns'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Create the campaign
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            campaign = serializer.save()
            
            # Return detailed campaign data
            detail_serializer = CampaignDetailSerializer(campaign)
            return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherCampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, and delete campaigns for authenticated teachers
    GET: Get campaign details with recipients
    PUT/PATCH: Update campaign (only if status is draft)
    DELETE: Delete campaign
    """
    authentication_classes = [SupabaseTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CampaignCreateUpdateSerializer
        return CampaignDetailSerializer
    
    def get_queryset(self):
        """Get campaigns for the authenticated teacher"""
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=self.request.user)
            return Campaign.objects.filter(teacher=teacher_profile)
        except TeacherProfile.DoesNotExist:
            return Campaign.objects.none()
    
    def update(self, request, *args, **kwargs):
        """Custom update method - only allow updates for draft campaigns"""
        campaign = self.get_object()
        
        if not campaign.can_be_sent:
            return Response({
                'error': f'Cannot update campaign with status: {campaign.status}. Only draft campaigns can be updated.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Custom delete with confirmation"""
        campaign = self.get_object()
        campaign_title = campaign.title
        
        # Prevent deletion of sent campaigns
        if campaign.is_sent:
            return Response({
                'error': 'Cannot delete sent campaigns. This is for record keeping.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        campaign.delete()
        return Response({
            'message': f'Campaign "{campaign_title}" has been deleted successfully.'
        }, status=status.HTTP_200_OK)


class CampaignSendToSpecificStudentsView(APIView):
    """
    Send campaign to specific students via email
    POST: Send the campaign to selected students
    """
    authentication_classes = [SupabaseTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, campaign_id):
        """Send campaign to specific students"""
        try:
            # Verify teacher
            teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
        except TeacherProfile.DoesNotExist:
            return Response({
                'error': 'Only teachers can send campaigns'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get campaign
        try:
            campaign = Campaign.objects.get(id=campaign_id, teacher=teacher_profile)
        except Campaign.DoesNotExist:
            return Response({
                'error': 'Campaign not found or you do not have permission to send it'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate request data
        serializer = CampaignSendToSpecificStudentsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if campaign can be sent (allow draft or failed campaigns for targeted sending)
        if campaign.status not in [Campaign.StatusChoices.DRAFT, Campaign.StatusChoices.FAILED]:
            return Response({
                'error': f'Campaign cannot be sent. Current status: {campaign.status}. Only draft or failed campaigns can be sent to specific students.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get student emails from validated data
        student_emails = serializer.validated_data['student_emails']
        
        # Send the campaign to specific students
        email_service = ResendEmailService()
        result = email_service.send_campaign_to_specific_students(campaign, student_emails)
        
        if result['success']:
            response_data = {
                'message': 'Campaign sent successfully to selected students',
                'campaign_id': campaign.id,
                'campaign_title': campaign.title,
                'sent_count': result['sent_count'],
                'failed_count': result['failed_count'],
                'total_recipients': result['total_recipients'],
                'requested_emails': len(student_emails),
                'missing_students': result.get('missing_students', [])
            }
            
            # Add warning if some students were not found
            if result.get('missing_students'):
                response_data['warning'] = f"{len(result['missing_students'])} student email(s) were not found in the system"
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CampaignSendView(APIView):
    """
    Send campaign to all students via email
    POST: Send the campaign
    """
    authentication_classes = [SupabaseTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, campaign_id):
        """Send campaign to all students"""
        try:
            # Verify teacher
            teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
        except TeacherProfile.DoesNotExist:
            return Response({
                'error': 'Only teachers can send campaigns'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get campaign
        try:
            campaign = Campaign.objects.get(id=campaign_id, teacher=teacher_profile)
        except Campaign.DoesNotExist:
            return Response({
                'error': 'Campaign not found or you do not have permission to send it'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate request data
        serializer = CampaignSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if campaign can be sent
        if not campaign.can_be_sent:
            return Response({
                'error': f'Campaign cannot be sent. Current status: {campaign.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send the campaign
        email_service = ResendEmailService()
        result = email_service.send_campaign(campaign)
        
        if result['success']:
            return Response({
                'message': 'Campaign sent successfully',
                'campaign_id': campaign.id,
                'campaign_title': campaign.title,
                'sent_count': result['sent_count'],
                'failed_count': result['failed_count'],
                'total_recipients': result['total_recipients']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CampaignStatsView(APIView):
    """
    Get campaign statistics for the authenticated teacher
    GET: Get campaign stats
    """
    authentication_classes = [SupabaseTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get campaign statistics"""
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
        except TeacherProfile.DoesNotExist:
            return Response({
                'error': 'Only teachers can view campaign statistics'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get stats using email service
        email_service = ResendEmailService()
        stats = email_service.get_campaign_stats(teacher_profile)
        
        # Serialize and return
        serializer = CampaignStatsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_students(request):
    """
    Get list of all students available for campaign targeting
    GET: Get all students with basic info
    """
    try:
        teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
    except TeacherProfile.DoesNotExist:
        return Response({
            'error': 'Only teachers can view student lists'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all students
    from core.models import User
    students = User.objects.filter(role=User.Role.STUDENT).select_related('profile')
    
    # Format student data
    student_list = []
    for student in students:
        student_data = {
            'id': student.id,
            'email': student.email,
            'name': student.get_full_name() or student.username,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'username': student.username,
            'date_joined': student.date_joined
        }
        student_list.append(student_data)
    
    return Response({
        'count': len(student_list),
        'students': student_list
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_preview(request, campaign_id):
    """
    Preview how the campaign email will look
    GET: Get formatted email preview
    """
    try:
        teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
    except TeacherProfile.DoesNotExist:
        return Response({
            'error': 'Only teachers can preview campaigns'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get campaign
    try:
        campaign = Campaign.objects.get(id=campaign_id, teacher=teacher_profile)
    except Campaign.DoesNotExist:
        return Response({
            'error': 'Campaign not found or you do not have permission to view it'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Generate preview
    email_service = ResendEmailService()
    sample_student_name = "John Doe"  # Sample name for preview
    formatted_content = email_service._format_email_content(campaign.content, sample_student_name)
    
    return Response({
        'campaign_id': campaign.id,
        'title': campaign.title,
        'subject': campaign.subject,
        'from_name': campaign.from_name,
        'from_email': campaign.from_email,
        'sample_student_name': sample_student_name,
        'formatted_content': formatted_content,
        'raw_content': campaign.content
    }, status=status.HTTP_200_OK)
