"""
Enhanced payment tracking and history views for LinguaFlex
Provides comprehensive payment history, admin tracking, and financial summaries
"""

from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q, Count, Avg
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Payment, PaymentAnalytics, RefundRequest
from .serializers import PaymentSerializer, PaymentDashboardSerializer
from core.models import User
from bookings.models import SessionBooking


class PaymentHistoryPagination(PageNumberPagination):
    """Custom pagination for payment history"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserPaymentHistoryView(generics.ListAPIView):
    """
    Get complete payment history for a user (student or teacher)
    Includes filtering, sorting, and summary statistics
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaymentHistoryPagination
    
    def get_queryset(self):
        user = self.request.user
        
        # Base queryset - payments user is involved in
        queryset = Payment.objects.filter(
            Q(student=user) | Q(teacher=user)
        ).select_related(
            'student', 'teacher', 'gig', 'session_booking'
        ).order_by('-created_at')
        
        # Apply filters
        queryset = self.apply_filters(queryset)
        return queryset
    
    def apply_filters(self, queryset):
        """Apply query parameter filters"""
        # Status filter
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)
        
        # Date range filter
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        # Role filter (payments as student vs teacher)
        role = self.request.query_params.get('role')
        if role == 'student':
            queryset = queryset.filter(student=self.request.user)
        elif role == 'teacher':
            queryset = queryset.filter(teacher=self.request.user)
        
        # Amount range
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        
        if min_amount:
            try:
                min_cents = int(float(min_amount) * 100)
                queryset = queryset.filter(amount_cents__gte=min_cents)
            except ValueError:
                pass
        
        if max_amount:
            try:
                max_cents = int(float(max_amount) * 100)
                queryset = queryset.filter(amount_cents__lte=max_cents)
            except ValueError:
                pass
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Enhanced list response with summary statistics"""
        response = super().list(request, *args, **kwargs)
        
        # Add summary statistics to response
        queryset = self.get_queryset()
        
        # Calculate summaries
        summary = {
            'total_payments': queryset.count(),
            'total_amount_dollars': self.calculate_total_amount(queryset),
            'successful_payments': queryset.filter(status='COMPLETED').count(),
            'pending_payments': queryset.filter(status='PENDING').count(),
            'failed_payments': queryset.filter(status='FAILED').count(),
            'as_student': queryset.filter(student=request.user).count(),
            'as_teacher': queryset.filter(teacher=request.user).count(),
        }
        
        # Add platform fee earned (for teachers)
        if request.user.role == 'TEACHER':
            platform_fees = queryset.filter(
                teacher=request.user,
                status='COMPLETED'
            ).aggregate(total_fees=Sum('platform_fee_cents'))
            
            summary['platform_fees_paid_dollars'] = (
                platform_fees['total_fees'] or 0
            ) / 100
        
        response.data['summary'] = summary
        return response
    
    def calculate_total_amount(self, queryset):
        """Calculate total amount in dollars"""
        total_cents = queryset.aggregate(
            total=Sum('amount_cents')
        )['total'] or 0
        return total_cents / 100


class AdminPaymentTrackingView(APIView):
    """
    Comprehensive admin view for tracking all payments, platform fees, and financial metrics
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        # Date filters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        # Default to last 30 days if no dates provided
        if not date_from:
            date_from = (timezone.now() - timedelta(days=30)).date()
        else:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            except ValueError:
                date_from = (timezone.now() - timedelta(days=30)).date()
        
        if not date_to:
            date_to = timezone.now().date()
        else:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                date_to = timezone.now().date()
        
        # Base queryset
        payments_qs = Payment.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).select_related('student', 'teacher', 'gig', 'session_booking')
        
        # Overall metrics
        total_payments = payments_qs.count()
        successful_payments = payments_qs.filter(status='COMPLETED')
        
        # Financial metrics
        total_revenue_cents = successful_payments.aggregate(
            total=Sum('amount_cents')
        )['total'] or 0
        
        total_platform_fees_cents = successful_payments.aggregate(
            total=Sum('platform_fee_cents')
        )['total'] or 0
        
        teacher_earnings_cents = total_revenue_cents - total_platform_fees_cents
        
        # Status breakdown
        status_breakdown = {
            'completed': successful_payments.count(),
            'pending': payments_qs.filter(status='PENDING').count(),
            'failed': payments_qs.filter(status='FAILED').count(),
            'refunded': payments_qs.filter(status='REFUNDED').count(),
        }
        
        # Top teachers by earnings
        top_teachers = successful_payments.values(
            'teacher__email', 'teacher__first_name', 'teacher__last_name'
        ).annotate(
            total_earnings_cents=Sum('amount_cents') - Sum('platform_fee_cents'),
            total_sessions=Count('id'),
            avg_session_rate=Avg('hourly_rate_cents')
        ).order_by('-total_earnings_cents')[:10]
        
        # Top students by spending
        top_students = successful_payments.values(
            'student__email', 'student__first_name', 'student__last_name'
        ).annotate(
            total_spent_cents=Sum('amount_cents'),
            total_sessions=Count('id')
        ).order_by('-total_spent_cents')[:10]
        
        # Monthly revenue trend
        monthly_revenue = successful_payments.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_revenue=Sum('amount_cents'),
            total_fees=Sum('platform_fee_cents'),
            payment_count=Count('id')
        ).order_by('month')
        
        # Daily revenue for the period (last 7 days for detailed view)
        daily_start = max(date_from, (timezone.now() - timedelta(days=7)).date())
        daily_revenue = successful_payments.filter(
            created_at__date__gte=daily_start
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total_revenue=Sum('amount_cents'),
            total_fees=Sum('platform_fee_cents'),
            payment_count=Count('id')
        ).order_by('date')
        
        # Recent high-value payments
        high_value_payments = successful_payments.filter(
            amount_cents__gte=10000  # $100+
        ).order_by('-created_at')[:5]
        
        # Refund analytics
        refunds = RefundRequest.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )
        
        refund_stats = {
            'pending_refunds': refunds.filter(status='PENDING').count(),
            'approved_refunds': refunds.filter(status='APPROVED').count(),
            'rejected_refunds': refunds.filter(status='REJECTED').count(),
            'total_refund_amount_cents': refunds.filter(
                status__in=['APPROVED', 'COMPLETED']
            ).aggregate(total=Sum('requested_amount_cents'))['total'] or 0
        }
        
        # Compile response
        tracking_data = {
            'date_range': {
                'from': date_from,
                'to': date_to
            },
            'overview': {
                'total_payments': total_payments,
                'total_revenue_dollars': total_revenue_cents / 100,
                'platform_fees_earned_dollars': total_platform_fees_cents / 100,
                'teacher_earnings_dollars': teacher_earnings_cents / 100,
                'average_transaction_dollars': (
                    total_revenue_cents / max(total_payments, 1)
                ) / 100,
                'platform_fee_percentage': (
                    (total_platform_fees_cents / max(total_revenue_cents, 1)) * 100
                ) if total_revenue_cents > 0 else 0
            },
            'status_breakdown': status_breakdown,
            'top_performers': {
                'teachers': [
                    {
                        'email': t['teacher__email'],
                        'name': f"{t['teacher__first_name']} {t['teacher__last_name']}".strip(),
                        'earnings_dollars': t['total_earnings_cents'] / 100,
                        'sessions': t['total_sessions'],
                        'avg_hourly_rate_dollars': t['avg_session_rate'] / 100 if t['avg_session_rate'] else 0
                    }
                    for t in top_teachers
                ],
                'students': [
                    {
                        'email': s['student__email'],
                        'name': f"{s['student__first_name']} {s['student__last_name']}".strip(),
                        'spent_dollars': s['total_spent_cents'] / 100,
                        'sessions': s['total_sessions']
                    }
                    for s in top_students
                ]
            },
            'trends': {
                'monthly': [
                    {
                        'month': m['month'].strftime('%Y-%m'),
                        'revenue_dollars': m['total_revenue'] / 100,
                        'fees_dollars': m['total_fees'] / 100,
                        'payments': m['payment_count']
                    }
                    for m in monthly_revenue
                ],
                'daily': [
                    {
                        'date': d['date'].strftime('%Y-%m-%d'),
                        'revenue_dollars': d['total_revenue'] / 100,
                        'fees_dollars': d['total_fees'] / 100,
                        'payments': d['payment_count']
                    }
                    for d in daily_revenue
                ]
            },
            'high_value_payments': PaymentSerializer(high_value_payments, many=True).data,
            'refunds': {
                **refund_stats,
                'total_refund_amount_dollars': refund_stats['total_refund_amount_cents'] / 100
            }
        }
        
        return Response(tracking_data)


class PaymentAnalyticsView(APIView):
    """
    Get payment analytics for different time periods and user segments
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        period = request.query_params.get('period', '30d')  # 7d, 30d, 90d, 365d
        
        # Calculate date range based on period
        now = timezone.now()
        if period == '7d':
            start_date = now - timedelta(days=7)
        elif period == '30d':
            start_date = now - timedelta(days=30)
        elif period == '90d':
            start_date = now - timedelta(days=90)
        elif period == '365d':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)
        
        payments = Payment.objects.filter(
            created_at__gte=start_date,
            status='COMPLETED'
        )
        
        # User engagement analytics
        unique_students = payments.values('student').distinct().count()
        unique_teachers = payments.values('teacher').distinct().count()
        
        # Session type analytics
        gig_payments = payments.filter(gig__isnull=False).count()
        booking_payments = payments.filter(session_booking__isnull=False).count()
        
        # Payment method analytics
        payment_methods = payments.values('payment_method_type').annotate(
            count=Count('id'),
            revenue=Sum('amount_cents')
        ).order_by('-count')
        
        # Hour of day analytics (when do payments occur?)
        hourly_distribution = {}
        for payment in payments.values('created_at'):
            hour = payment['created_at'].hour
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
        
        analytics = {
            'period': period,
            'engagement': {
                'unique_students': unique_students,
                'unique_teachers': unique_teachers,
                'repeat_students': payments.values('student').annotate(
                    sessions=Count('id')
                ).filter(sessions__gt=1).count(),
                'repeat_teachers': payments.values('teacher').annotate(
                    sessions=Count('id')
                ).filter(sessions__gt=1).count()
            },
            'session_types': {
                'gig_sessions': gig_payments,
                'booking_sessions': booking_payments,
                'gig_percentage': (gig_payments / max(payments.count(), 1)) * 100,
                'booking_percentage': (booking_payments / max(payments.count(), 1)) * 100
            },
            'payment_methods': [
                {
                    'method': pm['payment_method_type'] or 'unknown',
                    'count': pm['count'],
                    'revenue_dollars': pm['revenue'] / 100
                }
                for pm in payment_methods
            ],
            'timing': {
                'hourly_distribution': [
                    {'hour': hour, 'count': count}
                    for hour, count in sorted(hourly_distribution.items())
                ]
            }
        }
        
        return Response(analytics)


class UserFinancialSummaryView(APIView):
    """
    Get financial summary for a specific user (earnings as teacher, spending as student)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id=None):
        # Admin can view any user, users can only view themselves
        if user_id and request.user.is_staff:
            user = get_object_or_404(User, id=user_id)
        else:
            user = request.user
        
        # Date range (default to all time)
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        filters = {'status': 'COMPLETED'}
        if date_from:
            try:
                filters['created_at__date__gte'] = datetime.strptime(date_from, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if date_to:
            try:
                filters['created_at__date__lte'] = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # As student (money spent)
        student_payments = Payment.objects.filter(
            student=user, **filters
        )
        
        student_summary = {
            'total_spent_dollars': (student_payments.aggregate(
                total=Sum('amount_cents')
            )['total'] or 0) / 100,
            'total_sessions': student_payments.count(),
            'average_session_cost_dollars': 0,
            'unique_teachers': student_payments.values('teacher').distinct().count()
        }
        
        if student_summary['total_sessions'] > 0:
            student_summary['average_session_cost_dollars'] = (
                student_summary['total_spent_dollars'] / student_summary['total_sessions']
            )
        
        # As teacher (money earned)
        teacher_payments = Payment.objects.filter(
            teacher=user, **filters
        )
        
        total_earnings_cents = teacher_payments.aggregate(
            earnings=Sum('amount_cents') - Sum('platform_fee_cents')
        )['earnings'] or 0
        
        platform_fees_cents = teacher_payments.aggregate(
            fees=Sum('platform_fee_cents')
        )['fees'] or 0
        
        teacher_summary = {
            'total_earned_dollars': total_earnings_cents / 100,
            'platform_fees_paid_dollars': platform_fees_cents / 100,
            'gross_revenue_dollars': (total_earnings_cents + platform_fees_cents) / 100,
            'total_sessions': teacher_payments.count(),
            'unique_students': teacher_payments.values('student').distinct().count(),
            'average_session_earnings_dollars': 0,
            'average_hourly_rate_dollars': 0
        }
        
        if teacher_summary['total_sessions'] > 0:
            teacher_summary['average_session_earnings_dollars'] = (
                teacher_summary['total_earned_dollars'] / teacher_summary['total_sessions']
            )
            
            avg_rate = teacher_payments.aggregate(
                avg_rate=Avg('hourly_rate_cents')
            )['avg_rate']
            
            if avg_rate:
                teacher_summary['average_hourly_rate_dollars'] = avg_rate / 100
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}".strip(),
                'role': user.role
            },
            'as_student': student_summary,
            'as_teacher': teacher_summary,
            'date_range': {
                'from': date_from,
                'to': date_to
            }
        })


class PlatformFinancialReportView(APIView):
    """
    Generate comprehensive financial report for platform admins
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        # This month vs last month comparison
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Last month
        if current_month_start.month == 1:
            last_month_start = current_month_start.replace(
                year=current_month_start.year - 1,
                month=12
            )
        else:
            last_month_start = current_month_start.replace(
                month=current_month_start.month - 1
            )
        
        # Current month data
        current_payments = Payment.objects.filter(
            status='COMPLETED',
            created_at__gte=current_month_start
        )
        
        # Last month data
        last_payments = Payment.objects.filter(
            status='COMPLETED',
            created_at__gte=last_month_start,
            created_at__lt=current_month_start
        )
        
        def calculate_metrics(queryset):
            """Calculate financial metrics for a queryset"""
            return {
                'total_revenue_cents': queryset.aggregate(Sum('amount_cents'))['amount_cents__sum'] or 0,
                'platform_fees_cents': queryset.aggregate(Sum('platform_fee_cents'))['platform_fee_cents__sum'] or 0,
                'payment_count': queryset.count(),
                'unique_users': (
                    queryset.values('student').distinct().count() + 
                    queryset.values('teacher').distinct().count()
                )
            }
        
        current_metrics = calculate_metrics(current_payments)
        last_metrics = calculate_metrics(last_payments)
        
        # Calculate growth rates
        def growth_rate(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return ((current - previous) / previous) * 100
        
        report = {
            'period': {
                'current_month': current_month_start.strftime('%Y-%m'),
                'last_month': last_month_start.strftime('%Y-%m')
            },
            'current_month': {
                'revenue_dollars': current_metrics['total_revenue_cents'] / 100,
                'platform_fees_dollars': current_metrics['platform_fees_cents'] / 100,
                'payments': current_metrics['payment_count'],
                'unique_users': current_metrics['unique_users']
            },
            'last_month': {
                'revenue_dollars': last_metrics['total_revenue_cents'] / 100,
                'platform_fees_dollars': last_metrics['platform_fees_cents'] / 100,
                'payments': last_metrics['payment_count'],
                'unique_users': last_metrics['unique_users']
            },
            'growth': {
                'revenue_growth': growth_rate(
                    current_metrics['total_revenue_cents'],
                    last_metrics['total_revenue_cents']
                ),
                'fees_growth': growth_rate(
                    current_metrics['platform_fees_cents'],
                    last_metrics['platform_fees_cents']
                ),
                'payments_growth': growth_rate(
                    current_metrics['payment_count'],
                    last_metrics['payment_count']
                ),
                'users_growth': growth_rate(
                    current_metrics['unique_users'],
                    last_metrics['unique_users']
                )
            },
            'year_to_date': self.get_ytd_metrics(),
            'projections': self.get_monthly_projection(current_metrics)
        }
        
        return Response(report)
    
    def get_ytd_metrics(self):
        """Get year-to-date financial metrics"""
        now = timezone.now()
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        ytd_payments = Payment.objects.filter(
            status='COMPLETED',
            created_at__gte=year_start
        )
        
        total_revenue = ytd_payments.aggregate(Sum('amount_cents'))['amount_cents__sum'] or 0
        platform_fees = ytd_payments.aggregate(Sum('platform_fee_cents'))['platform_fee_cents__sum'] or 0
        
        return {
            'revenue_dollars': total_revenue / 100,
            'platform_fees_dollars': platform_fees / 100,
            'payments': ytd_payments.count(),
            'months_elapsed': now.month
        }
    
    def get_monthly_projection(self, current_metrics):
        """Project end-of-month metrics based on current progress"""
        now = timezone.now()
        days_in_month = (now.replace(month=now.month + 1, day=1) - timezone.timedelta(days=1)).day
        current_day = now.day
        
        if current_day == 0:
            return current_metrics
        
        projection_factor = days_in_month / current_day
        
        return {
            'projected_revenue_dollars': (current_metrics['total_revenue_cents'] * projection_factor) / 100,
            'projected_fees_dollars': (current_metrics['platform_fees_cents'] * projection_factor) / 100,
            'projected_payments': int(current_metrics['payment_count'] * projection_factor)
        }
