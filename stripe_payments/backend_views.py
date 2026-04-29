"""
Additional views for backend-only payment system using Stripe test tokens
"""

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
import stripe
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class AddPaymentMethodSerializer(serializers.Serializer):
    """Serializer for adding payment method using a Stripe token"""

    payment_method_id = serializers.CharField(
        help_text="Stripe payment method ID from Stripe Elements"
    )


class AddPaymentMethodView(APIView):
    """
    Add a new payment method using Stripe Elements token
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AddPaymentMethodSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": "Invalid payment method",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = request.user
            payment_method_id = serializer.validated_data["payment_method_id"]

            # Get or create Stripe customer
            from .services import StripePaymentService

            customer = StripePaymentService.create_or_get_customer(user)

            # Retrieve the payment method and attach it to the customer
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            if payment_method.customer != customer.stripe_customer_id:
                payment_method = stripe.PaymentMethod.attach(
                    payment_method_id, customer=customer.stripe_customer_id
                )

            response_data = {
                "success": True,
                "message": "Payment method added successfully",
                "payment_method_id": payment_method.id,
                "card_last4": payment_method.card.last4,
                "card_brand": payment_method.card.brand,
                "saved": True,
            }

            # Save to database
            from .models import SavedPaymentMethod

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

            return Response(response_data, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            error_msg = getattr(e, 'user_message', None) or str(e).split(':')[-1].strip()
            return Response(
                {
                    "success": False,
                    "error": error_msg,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error adding payment method: {e}")
            return Response(
                {"success": False, "error": f"Failed to add payment method: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
            platform_fee = session_cost * 0.05  # 5% of session cost
            total_amount = session_cost + platform_fee

            # Convert to cents for Stripe
            session_cost_cents = int(session_cost * 100)
            platform_fee_cents = int(platform_fee * 100)
            total_amount_cents = int(total_amount * 100)

            # 4. Get or create Stripe customer
            from .services import StripePaymentService

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
                error_msg = getattr(e, 'user_message', None) or str(e).split(':')[-1].strip()
                return Response(
                    {"success": False, "error": error_msg},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Save payment method to database if requested or if it was already saved
            save_requested = request.data.get(
                "save_payment_method", False
            ) or request.data.get("saved_payment_method_id")
            if save_requested:
                from .models import SavedPaymentMethod

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

            # 7. Create payment record
            from .models import Payment

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

            # 8. Update booking status
            if payment_intent.status == "succeeded":
                booking.payment_status = "PAID"
                booking.status = "CONFIRMED"
                booking.save()

                # Note: Zoom meeting should already exist from booking confirmation
                # No need to create or update Zoom meeting during payment

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
                    "error": e.user_message or str(e).split(':')[-1].strip(),
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
            error_msg = getattr(e, 'user_message', None) or str(e).split(':')[-1].strip()
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
