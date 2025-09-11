# accounts/views_students.py
from django.db.models import Q, Count, Avg
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from core.authentication import SupabaseTokenAuthentication
from core.models import User
from .models import UserProfile, TeacherProfile
from .serializers_new import UserProfileSerializer
from core.serializers import UserSerializer


class StudentPagination(PageNumberPagination):
    """Custom pagination for student listings"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class StudentDetailSerializer(UserProfileSerializer):
    """Extended serializer for student details"""
    user = UserSerializer(read_only=True)
    
    class Meta(UserProfileSerializer.Meta):
        fields = UserProfileSerializer.Meta.fields + [
            'created_at', 'updated_at'
        ]


class TeacherStudentListView(generics.ListAPIView):
    """
    GET endpoint for teachers to retrieve all student details
    Supports filtering, searching, and pagination
    """
    authentication_classes = [SupabaseTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = StudentDetailSerializer
    pagination_class = StudentPagination
    
    def get_queryset(self):
        """Get all students with their profiles, with filtering and search capabilities"""
        
        # Verify that the user is a teacher
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=self.request.user)
        except TeacherProfile.DoesNotExist:
            # Return empty queryset if user is not a teacher
            return UserProfile.objects.none()
        
        # Get all student profiles (users with role STUDENT)
        queryset = UserProfile.objects.filter(
            role=User.Role.STUDENT
        ).select_related('user').order_by('-created_at')
        
        # Apply filters based on query parameters
        
        # Filter by country
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        # Filter by city
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filter by native language
        native_language = self.request.query_params.get('native_language')
        if native_language:
            queryset = queryset.filter(native_language__icontains=native_language)
        
        # Filter by learning language
        learning_language = self.request.query_params.get('learning_language')
        if learning_language:
            queryset = queryset.filter(learning_language__icontains=learning_language)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status__icontains=status_filter)
        
        # Search functionality - search across multiple fields
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__username__icontains=search) |
                Q(bio__icontains=search) |
                Q(city__icontains=search) |
                Q(country__icontains=search) |
                Q(native_language__icontains=search) |
                Q(learning_language__icontains=search)
            )
        
        # Filter by gender
        gender = self.request.query_params.get('gender')
        if gender:
            queryset = queryset.filter(user__gender__icontains=gender)
        
        # Filter by age range (calculated from date_of_birth)
        age_min = self.request.query_params.get('age_min')
        age_max = self.request.query_params.get('age_max')
        if age_min or age_max:
            from django.utils import timezone
            from datetime import date, timedelta
            
            current_date = timezone.now().date()
            
            if age_min:
                try:
                    min_age = int(age_min)
                    max_birth_date = current_date - timedelta(days=min_age * 365)
                    queryset = queryset.filter(user__date_of_birth__lte=max_birth_date)
                except (ValueError, TypeError):
                    pass
            
            if age_max:
                try:
                    max_age = int(age_max)
                    min_birth_date = current_date - timedelta(days=(max_age + 1) * 365)
                    queryset = queryset.filter(user__date_of_birth__gte=min_birth_date)
                except (ValueError, TypeError):
                    pass
        
        # Filter by registration date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Sort options
        sort_by = self.request.query_params.get('sort_by', '-created_at')
        allowed_sort_fields = [
            'created_at', '-created_at',
            'user__first_name', '-user__first_name',
            'user__last_name', '-user__last_name',
            'user__email', '-user__email',
            'country', '-country',
            'city', '-city',
            'native_language', '-native_language',
            'learning_language', '-learning_language'
        ]
        
        if sort_by in allowed_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Custom list method to add additional context"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get statistics
        total_students = queryset.count()
        
        # Country statistics
        country_stats = queryset.values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Language statistics
        native_language_stats = queryset.values('native_language').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        learning_language_stats = queryset.values('learning_language').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data)
            
            # Add statistics to the response
            response_data.data['statistics'] = {
                'total_students': total_students,
                'top_countries': country_stats,
                'top_native_languages': native_language_stats,
                'top_learning_languages': learning_language_stats,
            }
            return response_data
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'count': total_students,
            'statistics': {
                'total_students': total_students,
                'top_countries': country_stats,
                'top_native_languages': native_language_stats,
                'top_learning_languages': learning_language_stats,
            }
        })


class StudentDetailByIdView(generics.RetrieveAPIView):
    """
    GET endpoint for teachers to retrieve a specific student's details by ID
    """
    authentication_classes = [SupabaseTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = StudentDetailSerializer
    lookup_field = 'user__id'
    lookup_url_kwarg = 'student_id'
    
    def get_queryset(self):
        """Ensure only teachers can access student details"""
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=self.request.user)
            return UserProfile.objects.filter(role=User.Role.STUDENT).select_related('user')
        except TeacherProfile.DoesNotExist:
            return UserProfile.objects.none()
    
    def retrieve(self, request, *args, **kwargs):
        """Custom retrieve method with additional student information"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Add additional information about the student
        data = serializer.data
        
        # Calculate age if date_of_birth is available
        if instance.user.date_of_birth:
            from django.utils import timezone
            from datetime import date
            
            today = timezone.now().date()
            birth_date = instance.user.date_of_birth
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            data['calculated_age'] = age
        
        # Add account status information
        data['account_info'] = {
            'is_active': instance.user.is_active,
            'last_login': instance.user.last_login,
            'account_created': instance.user.created_at,
            'profile_completed': bool(
                instance.bio and 
                instance.city and 
                instance.country and 
                instance.native_language and 
                instance.learning_language
            )
        }
        
        return Response(data)


class StudentStatisticsView(APIView):
    """
    GET endpoint for teachers to get comprehensive student statistics
    """
    authentication_classes = [SupabaseTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive student statistics"""
        
        # Verify that the user is a teacher
        try:
            teacher_profile = TeacherProfile.objects.get(user_profile__user=request.user)
        except TeacherProfile.DoesNotExist:
            return Response({
                'error': 'Only teachers can access student statistics'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all student profiles
        students = UserProfile.objects.filter(role=User.Role.STUDENT).select_related('user')
        
        total_students = students.count()
        
        # Demographics
        country_breakdown = students.values('country').annotate(
            count=Count('id')
        ).order_by('-count')
        
        gender_breakdown = students.values('user__gender').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Language analysis
        native_languages = students.values('native_language').annotate(
            count=Count('id')
        ).order_by('-count')
        
        learning_languages = students.values('learning_language').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Activity analysis
        active_students = students.filter(user__is_active=True).count()
        inactive_students = total_students - active_students
        
        # Profile completion analysis
        complete_profiles = students.filter(
            bio__isnull=False,
            city__isnull=False,
            country__isnull=False,
            native_language__isnull=False,
            learning_language__isnull=False
        ).exclude(
            bio='',
            city='',
            country='',
            native_language='',
            learning_language=''
        ).count()
        
        incomplete_profiles = total_students - complete_profiles
        
        # Recent registrations (last 30 days)
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_registrations = students.filter(created_at__gte=thirty_days_ago).count()
        
        return Response({
            'summary': {
                'total_students': total_students,
                'active_students': active_students,
                'inactive_students': inactive_students,
                'recent_registrations_30_days': recent_registrations,
                'profile_completion_rate': round((complete_profiles / total_students * 100) if total_students > 0 else 0, 2)
            },
            'demographics': {
                'countries': country_breakdown,
                'genders': gender_breakdown
            },
            'languages': {
                'native_languages': native_languages,
                'learning_languages': learning_languages
            },
            'profiles': {
                'complete_profiles': complete_profiles,
                'incomplete_profiles': incomplete_profiles,
                'completion_percentage': round((complete_profiles / total_students * 100) if total_students > 0 else 0, 2)
            }
        })
