"""
Enhanced refund system for LinguaFlex
- Automatic refunds for incomplete sessions
- Manual admin approval for completed sessions
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import stripe
import logging

from .models import Payment, RefundRequest
from .serializers import RefundRequestSerializer, CreateRefundRequestSerializer
from .services import StripePaymentService
from bookings.models import SessionBooking

logger = logging.getLogger(__name__)


class StudentRefundRequestView(APIView):
    """
    Handle student refund requests with automatic processing for incomplete sessions
    and manual approval for completed sessions
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Create a refund request
        - Automatic refund if booking is not completed
        - Manual review if booking is completed
        """
        try:
            with transaction.atomic():
                # Get payment and validate ownership
                payment_id = request.data.get('payment_id')
                if not payment_id:
                    return Response({
                        'success': False,
                        'error': 'Payment ID is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                payment = get_object_or_404(Payment, id=payment_id, student=request.user)
                
                # Check if payment can be refunded
                if payment.status not in ['COMPLETED']:
                    return Response({
                        'success': False,
                        'error': 'Only completed payments can be refunded'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check if refund already exists
                existing_refund = RefundRequest.objects.filter(
                    payment=payment, 
                    status__in=['PENDING', 'APPROVED', 'PROCESSED']
                ).first()
                
                if existing_refund:
                    return Response({
                        'success': False,
                        'error': 'Refund request already exists for this payment',
                        'existing_refund_id': existing_refund.id,
                        'status': existing_refund.status
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get booking details
                booking = payment.session_booking
                reason = request.data.get('reason', 'Student requested refund')
                requested_amount = request.data.get('requested_amount_dollars', payment.amount_dollars)
                
                # Validate requested amount
                if Decimal(str(requested_amount)) > payment.amount_dollars:
                    return Response({
                        'success': False,
                        'error': 'Requested amount cannot exceed payment amount'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check booking status to determine refund flow
                is_automatic_refund = booking.status in ['PENDING', 'CONFIRMED', 'CANCELLED']
                
                # Create refund request
                refund_request = RefundRequest.objects.create(
                    payment=payment,
                    student=request.user,
                    reason=reason,
                    requested_amount_cents=int(Decimal(str(requested_amount)) * 100),
                    status='APPROVED' if is_automatic_refund else 'PENDING'
                )
                
                if is_automatic_refund:
                    # Process refund immediately for incomplete sessions
                    try:
                        result = StripePaymentService.create_refund(refund_request)
                        
                        # Update booking status if cancelled
                        if booking.status != 'CANCELLED':
                            booking.status = 'CANCELLED'
                            booking.cancellation_reason = f"Refund processed: {reason}"
                            booking.payment_status = 'REFUNDED'
                            booking.save()
                        
                        return Response({
                            'success': True,
                            'refund_type': 'automatic',
                            'message': 'Refund processed immediately (session not completed)',
                            'refund_request_id': refund_request.id,
                            'refund_amount': float(requested_amount),
                            'stripe_refund_id': refund_request.stripe_refund_id,
                            'booking_status': booking.status,
                            'refund_status': refund_request.status
                        })
                        
                    except Exception as e:
                        # If Stripe refund fails, mark as failed
                        refund_request.status = 'REJECTED'
                        refund_request.admin_notes = f"Automatic refund failed: {str(e)}"
                        refund_request.save()
                        
                        logger.error(f"Automatic refund failed for payment {payment_id}: {e}")
                        
                        return Response({
                            'success': False,
                            'error': 'Refund processing failed. Please contact support.',
                            'refund_request_id': refund_request.id
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                else:
                    # Manual review required for completed sessions
                    return Response({
                        'success': True,
                        'refund_type': 'manual_review',
                        'message': 'Refund request submitted for admin review (session was completed)',
                        'refund_request_id': refund_request.id,
                        'requested_amount': float(requested_amount),
                        'status': 'PENDING',
                        'note': 'Completed sessions require manual admin approval'
                    })
        
        except Exception as e:
            logger.error(f"Error processing refund request: {e}")
            return Response({
                'success': False,
                'error': 'An error occurred processing your refund request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """
        Get student's refund requests
        """
        refund_requests = RefundRequest.objects.filter(
            student=request.user
        ).select_related('payment', 'payment__session_booking')
        
        refunds_data = []
        for refund in refund_requests:
            payment = refund.payment
            booking = payment.session_booking
            
            refunds_data.append({
                'id': refund.id,
                'payment_id': payment.id,
                'amount_requested': float(refund.requested_amount_dollars),
                'amount_refunded': float(refund.refunded_amount_dollars) if refund.refunded_amount_dollars else None,
                'status': refund.status,
                'reason': refund.reason,
                'created_at': refund.created_at.isoformat(),
                'refunded_at': refund.refunded_at.isoformat() if refund.refunded_at else None,
                'booking_details': {
                    'id': booking.id,
                    'status': booking.status,
                    'teacher_name': payment.teacher.get_full_name() or payment.teacher.email,
                    'gig_title': payment.gig.service_title,
                    'session_date': booking.scheduled_datetime.isoformat() if booking.scheduled_datetime else None
                },
                'admin_notes': refund.admin_notes if refund.admin_notes else None
            })
        
        return Response({
            'success': True,
            'refund_requests': refunds_data
        })


class AdminRefundManagementView(APIView):
    """
    Admin view for managing refund requests
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """
        Get all pending refund requests for admin review
        """
        status_filter = request.query_params.get('status', 'PENDING')
        
        refund_requests = RefundRequest.objects.filter(
            status=status_filter
        ).select_related(
            'payment', 'payment__session_booking', 'payment__teacher', 'student'
        ).order_by('-created_at')
        
        refunds_data = []
        for refund in refund_requests:
            payment = refund.payment
            booking = payment.session_booking
            
            refunds_data.append({
                'id': refund.id,
                'student_email': refund.student.email,
                'student_name': refund.student.get_full_name(),
                'teacher_email': payment.teacher.email,
                'teacher_name': payment.teacher.get_full_name(),
                'payment_id': payment.id,
                'original_amount': float(payment.amount_dollars),
                'requested_amount': float(refund.requested_amount_dollars),
                'reason': refund.reason,
                'booking_status': booking.status,
                'session_date': booking.scheduled_datetime.isoformat() if booking.scheduled_datetime else None,
                'gig_title': payment.gig.service_title,
                'request_date': refund.created_at.isoformat(),
                'status': refund.status,
                'admin_notes': refund.admin_notes
            })
        
        return Response({
            'success': True,
            'refund_requests': refunds_data,
            'total': len(refunds_data)
        })
    
    def post(self, request):
        """
        Admin approve or reject refund request
        """
        refund_request_id = request.data.get('refund_request_id')
        action = request.data.get('action')  # 'approve' or 'reject'
        admin_notes = request.data.get('admin_notes', '')
        
        if not refund_request_id or action not in ['approve', 'reject']:
            return Response({
                'success': False,
                'error': 'Invalid request. Provide refund_request_id and action (approve/reject)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                refund_request = get_object_or_404(
                    RefundRequest, 
                    id=refund_request_id, 
                    status='PENDING'
                )
                
                if action == 'approve':
                    # Approve and process refund
                    refund_request.status = 'APPROVED'
                    refund_request.admin_notes = admin_notes or 'Approved by admin'
                    refund_request.reviewed_by = request.user
                    refund_request.reviewed_at = timezone.now()
                    refund_request.save()
                    
                    # Process the refund through Stripe
                    try:
                        result = StripePaymentService.create_refund(refund_request)
                        
                        return Response({
                            'success': True,
                            'message': 'Refund approved and processed',
                            'refund_request_id': refund_request.id,
                            'stripe_refund_id': refund_request.stripe_refund_id,
                            'amount_refunded': float(refund_request.refunded_amount_dollars)
                        })
                        
                    except Exception as e:
                        # If processing fails, mark as approved but not processed
                        refund_request.admin_notes += f" | Stripe processing failed: {str(e)}"
                        refund_request.save()
                        
                        return Response({
                            'success': False,
                            'error': f'Refund approved but processing failed: {str(e)}',
                            'refund_request_id': refund_request.id
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                else:  # reject
                    refund_request.status = 'REJECTED'
                    refund_request.admin_notes = admin_notes or 'Rejected by admin'
                    refund_request.reviewed_by = request.user
                    refund_request.reviewed_at = timezone.now()
                    refund_request.save()
                    
                    return Response({
                        'success': True,
                        'message': 'Refund request rejected',
                        'refund_request_id': refund_request.id,
                        'admin_notes': refund_request.admin_notes
                    })
        
        except Exception as e:
            logger.error(f"Error processing admin refund action: {e}")
            return Response({
                'success': False,
                'error': 'An error occurred processing the refund request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefundStatusView(APIView):
    """
    Check refund status for a specific payment
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, payment_id):
        """
        Get refund status for a payment
        """
        # Verify payment belongs to user (unless admin)
        if request.user.is_staff:
            payment = get_object_or_404(Payment, id=payment_id)
        else:
            payment = get_object_or_404(Payment, id=payment_id, student=request.user)
        
        # Get refund requests for this payment
        refund_requests = RefundRequest.objects.filter(payment=payment).order_by('-created_at')
        
        refund_data = []
        for refund in refund_requests:
            refund_data.append({
                'id': refund.id,
                'status': refund.status,
                'requested_amount': float(refund.requested_amount_dollars),
                'refunded_amount': float(refund.refunded_amount_dollars) if refund.refunded_amount_dollars else None,
                'reason': refund.reason,
                'admin_notes': refund.admin_notes,
                'created_at': refund.created_at.isoformat(),
                'refunded_at': refund.refunded_at.isoformat() if refund.refunded_at else None,
                'stripe_refund_id': refund.stripe_refund_id
            })
        
        booking = payment.session_booking
        can_request_refund = (
            payment.status == 'COMPLETED' and 
            not refund_requests.filter(status__in=['PENDING', 'APPROVED', 'PROCESSED']).exists()
        )
        
        return Response({
            'success': True,
            'payment_id': payment.id,
            'payment_amount': float(payment.amount_dollars),
            'payment_status': payment.status,
            'booking_status': booking.status,
            'can_request_refund': can_request_refund,
            'refund_requests': refund_data,
            'refund_eligibility': {
                'automatic': booking.status in ['PENDING', 'CONFIRMED', 'CANCELLED'],
                'manual_review': booking.status == 'COMPLETED',
                'reason': 'Incomplete sessions get automatic refunds, completed sessions require admin approval'
            }
        })
