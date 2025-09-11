"""
API views for Stripe payment system
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Q, Count
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.conf import settings
import stripe
import json
import logging
from datetime import datetime, timedelta

from .models import Payment, SavedPaymentMethod, RefundRequest, PaymentAnalytics
from .serializers import (
    PaymentSerializer, CreatePaymentIntentSerializer, ConfirmPaymentSerializer,
    SavedPaymentMethodSerializer, RefundRequestSerializer, CreateRefundRequestSerializer,
    AdminRefundReviewSerializer, PaymentDashboardSerializer
)
from .services import StripePaymentService, StripeWebhookService
from bookings.models import SessionBooking

logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    """
    Create a Stripe PaymentIntent for session booking
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CreatePaymentIntentSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session_booking = SessionBooking.objects.get(
                id=serializer.validated_data['session_booking_id']
            )
            
            result = StripePaymentService.create_payment_intent(
                session_booking=session_booking,
                payment_method_id=serializer.validated_data.get('payment_method_id'),
                save_payment_method=serializer.validated_data.get('save_payment_method', False)
            )
            
            return Response({
                'success': True,
                'client_secret': result['client_secret'],
                'payment_id': result['payment'].id,
                'amount_dollars': result['payment'].amount_dollars
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating PaymentIntent: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ConfirmPaymentView(APIView):
    """
    Confirm a PaymentIntent
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ConfirmPaymentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = StripePaymentService.confirm_payment_intent(
                serializer.validated_data['payment_intent_id']
            )
            
            payment_intent = result['payment_intent']
            
            return Response({
                'success': True,
                'status': payment_intent.status,
                'requires_action': payment_intent.status == 'requires_action',
                'client_secret': payment_intent.client_secret if payment_intent.status == 'requires_action' else None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error confirming payment: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentListView(generics.ListAPIView):
    """
    List user's payments
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all().select_related(
                'student', 'teacher', 'gig', 'session_booking'
            )
        else:
            return Payment.objects.filter(
                Q(student=user) | Q(teacher=user)
            ).select_related('student', 'teacher', 'gig', 'session_booking')


class PaymentDetailView(generics.RetrieveAPIView):
    """
    Get payment details
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        else:
            return Payment.objects.filter(Q(student=user) | Q(teacher=user))


class SavedPaymentMethodListView(generics.ListAPIView):
    """
    List user's saved payment methods
    """
    serializer_class = SavedPaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SavedPaymentMethod.objects.filter(
            student=self.request.user,
            is_active=True
        )


class SavePaymentMethodView(APIView):
    """
    Save a payment method for future use
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        payment_method_id = request.data.get('payment_method_id')
        
        if not payment_method_id:
            return Response(
                {'error': 'payment_method_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            saved_method = StripePaymentService.save_payment_method(
                request.user, 
                payment_method_id
            )
            
            serializer = SavedPaymentMethodSerializer(saved_method)
            return Response({
                'success': True,
                'payment_method': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DeletePaymentMethodView(APIView):
    """
    Delete a saved payment method
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, payment_method_id):
        try:
            # Check if payment method belongs to user
            saved_method = get_object_or_404(
                SavedPaymentMethod,
                stripe_payment_method_id=payment_method_id,
                student=request.user,
                is_active=True
            )
            
            success = StripePaymentService.delete_payment_method(payment_method_id)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Payment method deleted successfully'
                })
            else:
                return Response(
                    {'error': 'Failed to delete payment method'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RefundRequestListView(generics.ListCreateAPIView):
    """
    List and create refund requests
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateRefundRequestSerializer
        return RefundRequestSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return RefundRequest.objects.all().select_related('payment', 'student')
        else:
            return RefundRequest.objects.filter(student=user).select_related('payment')
    
    def perform_create(self, serializer):
        payment = Payment.objects.get(id=serializer.validated_data['payment_id'])
        serializer.save(
            payment=payment,
            student=self.request.user,
            requested_amount_cents=serializer.validated_data['requested_amount_cents']
        )


class RefundRequestDetailView(generics.RetrieveUpdateAPIView):
    """
    Get and update refund request details (admin only for updates)
    """
    serializer_class = RefundRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return RefundRequest.objects.all()
        else:
            return RefundRequest.objects.filter(student=user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH'] and self.request.user.is_staff:
            return AdminRefundReviewSerializer
        return RefundRequestSerializer
    
    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            return Response(
                {'error': 'Only admins can update refund requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save(
            reviewed_by=self.request.user,
            reviewed_at=timezone.now()
        )


class ProcessRefundView(APIView):
    """
    Process an approved refund (admin only)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, refund_request_id):
        try:
            refund_request = get_object_or_404(
                RefundRequest,
                id=refund_request_id,
                status='APPROVED'
            )
            
            result = StripePaymentService.create_refund(refund_request)
            
            return Response({
                'success': True,
                'refund_id': result['refund'].id,
                'amount_refunded': result['refund_request'].refunded_amount_dollars
            })
            
        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentDashboardView(APIView):
    """
    Payment analytics dashboard for admins
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        # Date filters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        # Default to last 30 days
        if not date_from:
            date_from = (timezone.now() - timedelta(days=30)).date()
        else:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        
        if not date_to:
            date_to = timezone.now().date()
        else:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Filter payments
        payments_qs = Payment.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )
        
        # Calculate metrics
        total_payments = payments_qs.count()
        successful_payments = payments_qs.filter(status='COMPLETED').count()
        failed_payments = payments_qs.filter(status='FAILED').count()
        
        total_revenue_cents = payments_qs.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('amount_cents'))['total'] or 0
        
        pending_refunds = RefundRequest.objects.filter(
            status='PENDING',
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).count()
        
        # Recent payments
        recent_payments = payments_qs.select_related(
            'student', 'teacher', 'gig', 'session_booking'
        ).order_by('-created_at')[:10]
        
        dashboard_data = {
            'total_payments': total_payments,
            'total_revenue_dollars': total_revenue_cents / 100,
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'pending_refunds': pending_refunds,
            'recent_payments': PaymentSerializer(recent_payments, many=True).data,
            'date_from': date_from,
            'date_to': date_to
        }
        
        return Response(dashboard_data)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload in Stripe webhook")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in Stripe webhook")
        return HttpResponse(status=400)
    
    # Handle the event
    try:
        if event['type'] == 'payment_intent.succeeded':
            StripeWebhookService.handle_payment_intent_succeeded(event['data'])
        elif event['type'] == 'payment_intent.payment_failed':
            StripeWebhookService.handle_payment_intent_payment_failed(event['data'])
        else:
            logger.info(f"Unhandled Stripe webhook event: {event['type']}")
    
    except Exception as e:
        logger.error(f"Error handling Stripe webhook: {e}")
        return HttpResponse(status=500)
    
    return HttpResponse(status=200)
