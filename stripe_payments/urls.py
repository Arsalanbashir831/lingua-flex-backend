"""
URL configuration for stripe_payments app
"""
from django.urls import path
from . import views
from . import refund_views
from .backend_views import AddPaymentMethodView, ProcessPaymentView, ProcessDirectPaymentView, ProcessBookingPaymentView
from .payment_tracking_views import (
    UserPaymentHistoryView, AdminPaymentTrackingView, PaymentAnalyticsView,
    UserFinancialSummaryView, PlatformFinancialReportView
)

app_name = 'stripe_payments'

urlpatterns = [
    # Backend-only payment endpoints (NEW)
    path('add-payment-method/', AddPaymentMethodView.as_view(), name='add_payment_method'),
    path('process-payment/', ProcessPaymentView.as_view(), name='process_payment'),
    path('process-direct-payment/', ProcessDirectPaymentView.as_view(), name='process_direct_payment'),
    path('process-booking-payment/', ProcessBookingPaymentView.as_view(), name='process_booking_payment'),
    
    # Payment Intent endpoints (existing)
    path('create-payment-intent/', views.CreatePaymentIntentView.as_view(), name='create_payment_intent'),
    path('confirm-payment/', views.ConfirmPaymentView.as_view(), name='confirm_payment'),
    
    # Payment management
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    
    # Saved payment methods
    path('payment-methods/', views.SavedPaymentMethodListView.as_view(), name='payment_method_list'),
    path('payment-methods/save/', views.SavePaymentMethodView.as_view(), name='save_payment_method'),
    path('payment-methods/<str:payment_method_id>/delete/', views.DeletePaymentMethodView.as_view(), name='delete_payment_method'),
    
    # Refund requests (existing)
    path('refund-requests/', views.RefundRequestListView.as_view(), name='refund_request_list'),
    path('refund-requests/<int:pk>/', views.RefundRequestDetailView.as_view(), name='refund_request_detail'),
    path('refund-requests/<int:refund_request_id>/process/', views.ProcessRefundView.as_view(), name='process_refund'),
    
    # Enhanced Refund System (NEW)
    path('refund/request/', refund_views.StudentRefundRequestView.as_view(), name='student_refund_request'),
    path('refund/status/<int:payment_id>/', refund_views.RefundStatusView.as_view(), name='refund_status'),
    path('admin/refund/manage/', refund_views.AdminRefundManagementView.as_view(), name='admin_refund_management'),
    
    # Admin dashboard
    path('dashboard/', views.PaymentDashboardView.as_view(), name='payment_dashboard'),
    
    # Enhanced Payment Tracking & Analytics (NEW)
    path('history/', UserPaymentHistoryView.as_view(), name='user_payment_history'),
    path('admin/tracking/', AdminPaymentTrackingView.as_view(), name='admin_payment_tracking'),
    path('admin/analytics/', PaymentAnalyticsView.as_view(), name='payment_analytics'),
    path('summary/', UserFinancialSummaryView.as_view(), name='user_financial_summary'),
    path('admin/summary/<int:user_id>/', UserFinancialSummaryView.as_view(), name='admin_user_summary'),
    path('admin/report/', PlatformFinancialReportView.as_view(), name='platform_financial_report'),
    
    # Stripe webhooks
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
