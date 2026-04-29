"""
Unified API views for Stripe payment system
"""

import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, RefundRequest, SavedPaymentMethod
from .serializers import SavedPaymentMethodSerializer
from .services import StripePaymentService, StripeWebhookService

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class ProcessBookingPaymentView(APIView):
    """
    Process payment for an existing booking session using card data
    This handles payment for bookings created separately
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Input validation
        required_fields = ["booking_id"]

        missing_fields = [
            field for field in required_fields if not request.data.get(field)
        ]

        if missing_fields:
            return Response(
                {
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if using payment_method_id (Stripe Elements) or saved_payment_method_id
        payment_method_id = request.data.get("payment_method_id") or request.data.get(
            "saved_payment_method_id"
        )

        if not payment_method_id:
            return Response(
                {"success": False, "error": "Missing payment_method_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = request.user
            data = request.data

            # 1. Get and validate booking
            from bookings.models import SessionBooking

            try:
                booking = SessionBooking.objects.get(
                    id=data["booking_id"], student=user
                )
            except SessionBooking.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "error": "Booking not found or does not belong to you",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Check if booking is already paid
            if booking.payment_status == "PAID":
                return Response(
                    {"success": False, "error": "Booking is already paid"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if booking is cancelled
            if booking.status == "CANCELLED":
                return Response(
                    {"success": False, "error": "Cannot pay for cancelled booking"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if booking is confirmed by teacher
            if booking.status != "CONFIRMED":
                return Response(
                    {
                        "success": False,
                        "error": "Booking must be confirmed by teacher before payment",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 2. Get gig and validate
            gig = booking.gig
            if gig.status != "active":
                return Response(
                    {"success": False, "error": "Gig is no longer available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 3. Calculate payment amounts
            # Use duration_hours from booking (provided in payload)
            duration_hours = float(booking.duration_hours)

            # Get hourly rate from gig
            hourly_rate = float(gig.price_per_session)
            session_cost = hourly_rate * duration_hours

            # Use centralized fee calculation service
            platform_fee_cents = StripePaymentService.calculate_platform_fee(
                int(hourly_rate * 100), Decimal(str(duration_hours))
            )
            platform_fee = float(platform_fee_cents) / 100
            total_amount = session_cost + platform_fee

            # Convert to cents for Stripe
            total_amount_cents = int(total_amount * 100)

            # 4. Get or create Stripe customer
            customer = StripePaymentService.create_or_get_customer(user)

            # 5. Create or get payment method
            try:
                payment_method = stripe.PaymentMethod.retrieve(payment_method_id)

                # Attach to customer if not already attached
                if payment_method.customer != customer.stripe_customer_id:
                    payment_method = stripe.PaymentMethod.attach(
                        payment_method_id, customer=customer.stripe_customer_id
                    )
            except stripe.error.StripeError as e:
                error_msg = (
                    getattr(e, "user_message", None) or str(e).split(":")[-1].strip()
                )
                return Response(
                    {"success": False, "error": error_msg},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Save payment method to database if requested or if it was already saved
            save_requested = request.data.get(
                "save_payment_method", False
            ) or request.data.get("saved_payment_method_id")
            if save_requested:
                if not SavedPaymentMethod.objects.filter(
                    stripe_payment_method_id=payment_method.id
                ).exists():
                    SavedPaymentMethod.objects.create(
                        student=user,
                        stripe_payment_method_id=payment_method.id,
                        stripe_customer_id=customer.stripe_customer_id,
                        card_last_four=payment_method.card.last4,
                        card_brand=payment_method.card.brand,
                        card_exp_month=payment_method.card.exp_month,
                        card_exp_year=payment_method.card.exp_year,
                    )

            # 6. Process payment with Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount=total_amount_cents,
                currency="usd",
                customer=customer.stripe_customer_id,
                payment_method=payment_method.id,
                confirm=True,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",  # Prevent redirect-based payment methods
                },
                metadata={
                    "session_booking_id": booking.id,
                    "gig_id": gig.id,
                    "student_id": user.id,
                    "teacher_id": booking.teacher.id,
                    "platform": "LinguaFlex",
                    "duration_hours": str(duration_hours),
                },
            )

            # 7. Create payment record and update booking status atomically
            with transaction.atomic():
                payment = Payment.objects.create(
                    session_booking=booking,
                    student=user,
                    teacher=booking.teacher,
                    gig=gig,
                    stripe_payment_intent_id=payment_intent.id,
                    stripe_charge_id=payment_intent.latest_charge
                    if payment_intent.latest_charge
                    else "",
                    stripe_customer_id=customer.stripe_customer_id,
                    amount_cents=total_amount_cents,
                    hourly_rate_cents=int(hourly_rate * 100),
                    platform_fee_cents=platform_fee_cents,
                    session_duration_hours=duration_hours,
                    status="COMPLETED"
                    if payment_intent.status == "succeeded"
                    else "FAILED",
                    currency="USD",
                )

                # 8. Update booking status and return response
                if payment_intent.status == "succeeded":
                    booking.payment_status = "PAID"
                    booking.status = "CONFIRMED"
                    booking.save()

                    return Response(
                        {
                            "success": True,
                            "message": "Payment processed successfully",
                            "payment_intent_id": payment_intent.id,
                            "booking_id": booking.id,
                            "payment_id": payment.id,
                            "amount_paid": total_amount,
                            "session_cost": session_cost,
                            "platform_fee": platform_fee,
                            "duration_hours": duration_hours,
                            "hourly_rate": hourly_rate,
                            "status": payment_intent.status,
                            "card_last4": payment_method.card.last4,
                            "card_brand": payment_method.card.brand,
                            "zoom_join_url": getattr(booking, "zoom_join_url", None),
                            "booking_details": {
                                "start_time": booking.start_time,
                                "end_time": booking.end_time,
                                "teacher_name": f"{booking.teacher.first_name} {booking.teacher.last_name}",
                                "gig_title": gig.title
                                if hasattr(gig, "title")
                                else "Language Session",
                            },
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    # Payment failed
                    booking.payment_status = "FAILED"
                    booking.save()

                    return Response(
                        {
                            "success": False,
                            "error": "Payment failed",
                            "details": {
                                "status": payment_intent.status,
                                "failure_reason": payment_intent.last_payment_error.message
                                if payment_intent.last_payment_error
                                else "Unknown error",
                            },
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except stripe.error.CardError as e:
            return Response(
                {
                    "success": False,
                    "error": e.user_message or str(e).split(":")[-1].strip(),
                    "details": {
                        "code": e.code,
                        "decline_code": getattr(e, "decline_code", None),
                        "param": e.param,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            error_msg = (
                getattr(e, "user_message", None) or str(e).split(":")[-1].strip()
            )
            return Response(
                {"success": False, "error": error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error processing booking payment: {e}")
            return Response(
                {"success": False, "error": f"Failed to process payment: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SavedPaymentMethodListView(generics.ListAPIView):
    """
    List user's saved payment methods
    """

    serializer_class = SavedPaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedPaymentMethod.objects.filter(
            student=self.request.user, is_active=True
        )


class DeletePaymentMethodView(APIView):
    """
    Delete a saved payment method
    """

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, payment_method_id):
        try:
            # Check if payment method belongs to user
            get_object_or_404(
                SavedPaymentMethod,
                stripe_payment_method_id=payment_method_id,
                student=request.user,
                is_active=True,
            )

            success = StripePaymentService.delete_payment_method(payment_method_id)

            if success:
                return Response(
                    {"success": True, "message": "Payment method deleted successfully"}
                )
            else:
                return Response(
                    {"error": "Failed to delete payment method"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
                payment_id = request.data.get("payment_id")
                if not payment_id:
                    return Response(
                        {"success": False, "error": "Payment ID is required"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                payment = get_object_or_404(
                    Payment, id=payment_id, student=request.user
                )

                # Check if payment can be refunded
                if payment.status not in ["COMPLETED"]:
                    return Response(
                        {
                            "success": False,
                            "error": "Only completed payments can be refunded",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Check if refund already exists
                existing_refund = RefundRequest.objects.filter(
                    payment=payment, status__in=["PENDING", "APPROVED", "PROCESSED"]
                ).first()

                if existing_refund:
                    return Response(
                        {
                            "success": False,
                            "error": "Refund request already exists for this payment",
                            "existing_refund_id": existing_refund.id,
                            "status": existing_refund.status,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Get booking details
                booking = payment.session_booking
                reason = request.data.get("reason", "Student requested refund")
                requested_amount = request.data.get(
                    "requested_amount_dollars", payment.amount_dollars
                )

                # Validate requested amount
                if Decimal(str(requested_amount)) > payment.amount_dollars:
                    return Response(
                        {
                            "success": False,
                            "error": "Requested amount cannot exceed payment amount",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Check booking status to determine refund flow
                is_automatic_refund = booking.status in [
                    "PENDING",
                    "CONFIRMED",
                    "CANCELLED",
                ]

                # Create refund request
                refund_request = RefundRequest.objects.create(
                    payment=payment,
                    student=request.user,
                    reason=reason,
                    requested_amount_cents=int(Decimal(str(requested_amount)) * 100),
                    status="APPROVED" if is_automatic_refund else "PENDING",
                )

                if is_automatic_refund:
                    # Process refund immediately for incomplete sessions
                    try:
                        StripePaymentService.create_refund(refund_request)

                        # Update booking status if cancelled
                        if booking.status != "CANCELLED":
                            booking.status = "CANCELLED"
                            booking.cancellation_reason = f"Refund processed: {reason}"
                            booking.payment_status = "REFUNDED"
                            booking.save()

                        return Response(
                            {
                                "success": True,
                                "refund_type": "automatic",
                                "message": "Refund processed immediately (session not completed)",
                                "refund_request_id": refund_request.id,
                                "refund_amount": float(requested_amount),
                                "stripe_refund_id": refund_request.stripe_refund_id,
                                "booking_status": booking.status,
                                "refund_status": refund_request.status,
                            }
                        )

                    except Exception as e:
                        # If Stripe refund fails, mark as failed
                        refund_request.status = "REJECTED"
                        refund_request.admin_notes = (
                            f"Automatic refund failed: {str(e)}"
                        )
                        refund_request.save()

                        logger.error(
                            f"Automatic refund failed for payment {payment_id}: {e}"
                        )

                        return Response(
                            {
                                "success": False,
                                "error": "Refund processing failed. Please contact support.",
                                "refund_request_id": refund_request.id,
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                else:
                    # Manual review required for completed sessions
                    return Response(
                        {
                            "success": True,
                            "refund_type": "manual_review",
                            "message": "Refund request submitted for admin review (session was completed)",
                            "refund_request_id": refund_request.id,
                            "requested_amount": float(requested_amount),
                            "status": "PENDING",
                            "note": "Completed sessions require manual admin approval",
                        }
                    )

        except Exception as e:
            logger.error(f"Error processing refund request: {e}")
            return Response(
                {
                    "success": False,
                    "error": "An error occurred processing your refund request",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        """
        Get student's refund requests
        """
        refund_requests = RefundRequest.objects.filter(
            student=request.user
        ).select_related("payment", "payment__session_booking")

        refunds_data = []
        for refund in refund_requests:
            payment = refund.payment
            booking = payment.session_booking

            refunds_data.append(
                {
                    "id": refund.id,
                    "payment_id": payment.id,
                    "amount_requested": float(refund.requested_amount_dollars),
                    "amount_refunded": float(refund.refunded_amount_dollars)
                    if refund.refunded_amount_dollars
                    else None,
                    "status": refund.status,
                    "reason": refund.reason,
                    "created_at": refund.created_at.isoformat(),
                    "refunded_at": refund.refunded_at.isoformat()
                    if refund.refunded_at
                    else None,
                    "booking_details": {
                        "id": booking.id,
                        "status": booking.status,
                        "teacher_name": payment.teacher.get_full_name()
                        or payment.teacher.email,
                        "gig_title": payment.gig.service_title,
                        "session_date": booking.scheduled_datetime.isoformat()
                        if booking.scheduled_datetime
                        else None,
                    },
                    "admin_notes": refund.admin_notes if refund.admin_notes else None,
                }
            )

        return Response({"success": True, "refund_requests": refunds_data})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

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
        if event["type"] == "payment_intent.succeeded":
            StripeWebhookService.handle_payment_intent_succeeded(event["data"])
        elif event["type"] == "payment_intent.payment_failed":
            StripeWebhookService.handle_payment_intent_payment_failed(event["data"])
        else:
            logger.info(f"Unhandled Stripe webhook event: {event['type']}")

    except Exception as e:
        logger.error(f"Error handling Stripe webhook: {e}")
        return HttpResponse(status=500)

    return HttpResponse(status=200)
