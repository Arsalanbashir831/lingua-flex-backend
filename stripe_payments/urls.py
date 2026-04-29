"""
URL configuration for stripe_payments app
"""

from django.urls import path
from . import views

app_name = "stripe_payments"

urlpatterns = [
    path(
        "process-booking-payment/",
        views.ProcessBookingPaymentView.as_view(),
        name="process_booking_payment",
    ),
    # Saved payment methods
    path(
        "payment-methods/",
        views.SavedPaymentMethodListView.as_view(),
        name="payment_method_list",
    ),
    path(
        "payment-methods/<str:payment_method_id>/delete/",
        views.DeletePaymentMethodView.as_view(),
        name="delete_payment_method",
    ),
    # Enhanced Refund System
    path(
        "refund/request/",
        views.StudentRefundRequestView.as_view(),
        name="student_refund_request",
    ),
    # Stripe webhooks
    path("webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),
]
