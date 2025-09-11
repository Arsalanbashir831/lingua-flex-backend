"""
URL configuration for stripe_payments app
"""
from django.urls import path
from . import views
from .backend_views import AddPaymentMethodView, ProcessPaymentView, ProcessDirectPaymentView, ProcessBookingPaymentView

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
    
    # Refund requests
    path('refund-requests/', views.RefundRequestListView.as_view(), name='refund_request_list'),
    path('refund-requests/<int:pk>/', views.RefundRequestDetailView.as_view(), name='refund_request_detail'),
    path('refund-requests/<int:refund_request_id>/process/', views.ProcessRefundView.as_view(), name='process_refund'),
    
    # Admin dashboard
    path('dashboard/', views.PaymentDashboardView.as_view(), name='payment_dashboard'),
    
    # Stripe webhooks
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
