"""
LinguaFlex Django Admin Configuration
Enhanced admin interface with custom dashboard
"""
from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Count, Q
from django.utils.html import format_html
from django.shortcuts import render
from datetime import datetime, timedelta
from django.utils import timezone


class LinguaFlexAdminSite(admin.AdminSite):
    """Custom admin site for LinguaFlex"""
    
    site_header = "LinguaFlex Admin Dashboard"
    site_title = "LinguaFlex Admin"
    index_title = "Welcome to LinguaFlex Administration"
    
    def index(self, request, extra_context=None):
        """Custom admin index with dashboard statistics"""
        extra_context = extra_context or {}
        
        # Import models here to avoid circular imports
        from core.models import User, Session
        from bookings.models import SessionBooking
        from campaigns.models import Campaign
        from accounts.models import UserProfile
        
        # Get current date and time ranges
        now = timezone.now()
        today = now.date()
        this_week_start = today - timedelta(days=today.weekday())
        this_month_start = today.replace(day=1)
        last_30_days = now - timedelta(days=30)
        
        # User Statistics
        total_users = User.objects.count()
        students_count = User.objects.filter(role=User.Role.STUDENT).count()
        teachers_count = User.objects.filter(role=User.Role.TEACHER).count()
        new_users_this_week = User.objects.filter(created_at__gte=this_week_start).count()
        new_users_this_month = User.objects.filter(created_at__gte=this_month_start).count()
        
        # Session Statistics
        total_sessions = SessionBooking.objects.count()
        completed_sessions = SessionBooking.objects.filter(status='COMPLETED').count()
        upcoming_sessions = SessionBooking.objects.filter(
            status__in=['PENDING', 'CONFIRMED'],
            start_time__gte=now
        ).count()
        sessions_today = SessionBooking.objects.filter(
            start_time__date=today
        ).count()
        
        # Campaign Statistics
        total_campaigns = Campaign.objects.count()
        active_campaigns = Campaign.objects.filter(status=Campaign.StatusChoices.SENT).count()
        draft_campaigns = Campaign.objects.filter(status=Campaign.StatusChoices.DRAFT).count()
        
        # Revenue Statistics (if you have payment data)
        try:
            from core.models import SessionBilling
            total_revenue = SessionBilling.objects.filter(is_paid=True).count()
            monthly_revenue = SessionBilling.objects.filter(
                is_paid=True,
                payment_date__gte=this_month_start
            ).count()
        except:
            total_revenue = 0
            monthly_revenue = 0
        
        # Recent Activity
        recent_users = User.objects.order_by('-created_at')[:5]
        recent_sessions = SessionBooking.objects.order_by('-created_at')[:5]
        recent_campaigns = Campaign.objects.order_by('-created_at')[:5]
        
        # Top Teachers by Session Count
        top_teachers = User.objects.filter(
            role=User.Role.TEACHER
        ).annotate(
            session_count=Count('teaching_sessions')
        ).order_by('-session_count')[:5]
        
        # Dashboard data
        dashboard_stats = {
            'user_stats': {
                'total_users': total_users,
                'students_count': students_count,
                'teachers_count': teachers_count,
                'new_users_this_week': new_users_this_week,
                'new_users_this_month': new_users_this_month,
            },
            'session_stats': {
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'upcoming_sessions': upcoming_sessions,
                'sessions_today': sessions_today,
                'completion_rate': round((completed_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1),
            },
            'campaign_stats': {
                'total_campaigns': total_campaigns,
                'active_campaigns': active_campaigns,
                'draft_campaigns': draft_campaigns,
            },
            'revenue_stats': {
                'total_revenue': total_revenue,
                'monthly_revenue': monthly_revenue,
            },
            'recent_activity': {
                'recent_users': recent_users,
                'recent_sessions': recent_sessions,
                'recent_campaigns': recent_campaigns,
            },
            'top_teachers': top_teachers,
        }
        
        extra_context['dashboard_stats'] = dashboard_stats
        extra_context['show_dashboard'] = True
        
        return super().index(request, extra_context)
    
    def get_urls(self):
        """Add custom URLs for admin site"""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('reports/', self.admin_view(self.reports_view), name='reports'),
            path('analytics/', self.admin_view(self.analytics_view), name='analytics'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom dashboard view"""
        context = {
            'title': 'Dashboard',
            'opts': {'app_label': 'dashboard'},
        }
        return TemplateResponse(request, 'admin/dashboard.html', context)
    
    def reports_view(self, request):
        """Custom reports view"""
        context = {
            'title': 'Reports',
            'opts': {'app_label': 'reports'},
        }
        return TemplateResponse(request, 'admin/reports.html', context)
    
    def analytics_view(self, request):
        """Custom analytics view"""
        context = {
            'title': 'Analytics',
            'opts': {'app_label': 'analytics'},
        }
        return TemplateResponse(request, 'admin/analytics.html', context)


# Create the custom admin site instance
admin_site = LinguaFlexAdminSite(name='linguaflex_admin')
