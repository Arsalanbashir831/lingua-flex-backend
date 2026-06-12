"""
Stripe service layer for payment processing
"""

import stripe
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from typing import Dict, Any, Optional
import logging

from .models import Payment, StripeCustomer, SavedPaymentMethod, RefundRequest
# ReportPayment is imported lazily inside methods to avoid circular imports

logger = logging.getLogger(__name__)

# Initialize Stripe with secret key
stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "")


class StripePaymentService:
    """
    Main service class for Stripe payment operations
    """

    @staticmethod
    def create_or_get_customer(user) -> StripeCustomer:
        """
        Create or retrieve Stripe customer for a user
        Ensures the customer exists in the current Stripe environment (Test vs Live)
        """
        customer_obj = None
        try:
            # Try to get existing customer from database
            customer_obj = StripeCustomer.objects.get(user=user)

            # Verify the customer exists in the current Stripe environment
            try:
                stripe.Customer.retrieve(customer_obj.stripe_customer_id)
                return customer_obj
            except stripe.error.StripeError:
                # If Stripe says it doesn't exist, it's likely an environment mismatch (Test vs Live)
                logger.warning(
                    f"Customer {customer_obj.stripe_customer_id} not found in Stripe (Mode mismatch?). Creating new one."
                )
                # Clear invalid saved payment methods associated with the old customer ID
                SavedPaymentMethod.objects.filter(student=user).delete()
                # Delete the invalid local customer record
                customer_obj.delete()
                customer_obj = None
        except StripeCustomer.DoesNotExist:
            pass

        try:
            # Create new Stripe customer
            stripe_customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.email,
                metadata={"user_id": user.id, "platform": "LinguaFlex"},
            )

            # Save to database
            customer_obj = StripeCustomer.objects.create(
                user=user,
                stripe_customer_id=stripe_customer.id,
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.email,
            )

            logger.info(
                f"Created Stripe customer {stripe_customer.id} for user {user.id}"
            )
            return customer_obj

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer for user {user.id}: {e}")
            raise Exception(f"Payment system error: {e}")

    @staticmethod
    def create_payment_intent(
        session_booking,
        payment_method_id: Optional[str] = None,
        save_payment_method: bool = False,
    ) -> Dict[str, Any]:
        """
        Create Stripe PaymentIntent for a session booking
        """
        try:
            # Get or create customer
            customer = StripePaymentService.create_or_get_customer(
                session_booking.student
            )

            # Calculate payment amount
            gig = session_booking.gig
            hourly_rate_cents = int(gig.price_per_session * 100)  # Convert to cents
            session_duration = Decimal(str(session_booking.duration_hours))
            platform_fee_cents = StripePaymentService.calculate_platform_fee(
                hourly_rate_cents, session_duration
            )
            total_amount_cents = int(
                (Decimal(hourly_rate_cents) * session_duration) + platform_fee_cents
            )

            # Create payment intent parameters
            intent_params = {
                "amount": total_amount_cents,
                "currency": "usd",
                "customer": customer.stripe_customer_id,
                "metadata": {
                    "session_booking_id": session_booking.id,
                    "teacher_id": session_booking.teacher.id,
                    "student_id": session_booking.student.id,
                    "gig_id": gig.id,
                    "platform": "LinguaFlex",
                },
                "description": f"Language lesson: {gig.service_title} with {session_booking.teacher.get_full_name()}",
                "statement_descriptor": "LINGUAFLEX LESSON",
                "setup_future_usage": "on_session" if save_payment_method else None,
            }

            # Configure payment method handling
            if payment_method_id:
                # Manual confirmation with specific payment method
                intent_params["payment_method"] = payment_method_id
                intent_params["confirmation_method"] = "manual"
                intent_params["confirm"] = True
                intent_params["payment_method_types"] = [
                    "card"
                ]  # Only accept cards (no redirects)
            else:
                # Automatic payment methods for frontend integration
                intent_params["automatic_payment_methods"] = {
                    "enabled": True,
                    "allow_redirects": "never",  # Only allow non-redirect payment methods (like cards)
                }

            # Create PaymentIntent
            payment_intent = stripe.PaymentIntent.create(**intent_params)

            # Create Payment record
            payment = Payment.objects.create(
                session_booking=session_booking,
                student=session_booking.student,
                teacher=session_booking.teacher,
                gig=gig,
                stripe_payment_intent_id=payment_intent.id,
                stripe_customer_id=customer.stripe_customer_id,
                amount_cents=total_amount_cents,
                hourly_rate_cents=hourly_rate_cents,
                session_duration_hours=session_duration,
                platform_fee_cents=platform_fee_cents,
                status="PROCESSING" if payment_method_id else "PENDING",
            )

            logger.info(
                f"Created PaymentIntent {payment_intent.id} for booking {session_booking.id}"
            )

            return {
                "payment_intent": payment_intent,
                "payment": payment,
                "client_secret": payment_intent.client_secret,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating PaymentIntent: {e}")
            raise Exception(f"Payment processing error: {e}")
        except Exception as e:
            logger.error(f"Error creating PaymentIntent: {e}")
            raise

    @staticmethod
    def calculate_platform_fee(hourly_rate_cents: int, duration_hours: Decimal) -> int:
        """
        Calculate platform fee (5% of session cost)
        """
        # 5% platform fee (no minimum)
        session_amount = Decimal(hourly_rate_cents) * duration_hours
        fee_percentage = Decimal("0.05")  # 5%
        calculated_fee = session_amount * fee_percentage

        return int(calculated_fee)

    @staticmethod
    def confirm_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """
        Confirm a PaymentIntent
        """
        try:
            # Confirm with return URL as fallback for redirect-based methods
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                return_url=f"{settings.FRONTEND_URL}/payment/return"
                if hasattr(settings, "FRONTEND_URL")
                else "https://localhost:3000/payment/return",
            )

            # Update payment status
            try:
                payment = Payment.objects.get(
                    stripe_payment_intent_id=payment_intent_id
                )

                if payment_intent.status == "succeeded":
                    payment.status = "COMPLETED"
                    payment.paid_at = timezone.now()
                    payment.stripe_charge_id = (
                        payment_intent.charges.data[0].id
                        if payment_intent.charges.data
                        else None
                    )
                elif payment_intent.status == "requires_action":
                    payment.status = "PROCESSING"
                else:
                    payment.status = "FAILED"

                payment.save()

            except Payment.DoesNotExist:
                logger.error(f"Payment not found for PaymentIntent {payment_intent_id}")

            return {"payment_intent": payment_intent}

        except stripe.error.StripeError as e:
            logger.error(f"Error confirming PaymentIntent {payment_intent_id}: {e}")
            raise Exception(f"Payment confirmation error: {e}")

    @staticmethod
    def save_payment_method(user, payment_method_id: str) -> SavedPaymentMethod:
        """
        Save a payment method for future use
        """
        try:
            # Get customer
            customer = StripePaymentService.create_or_get_customer(user)

            # Get payment method from Stripe
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)

            # Attach to customer if not already
            if not payment_method.customer:
                stripe.PaymentMethod.attach(
                    payment_method_id, customer=customer.stripe_customer_id
                )

            # Save to database
            saved_method = SavedPaymentMethod.objects.create(
                student=user,
                stripe_payment_method_id=payment_method_id,
                stripe_customer_id=customer.stripe_customer_id,
                card_brand=payment_method.card.brand,
                card_last_four=payment_method.card.last4,
                card_exp_month=payment_method.card.exp_month,
                card_exp_year=payment_method.card.exp_year,
                card_country=payment_method.card.country or "",
                is_default=not SavedPaymentMethod.objects.filter(
                    student=user, is_active=True
                ).exists(),
            )

            logger.info(f"Saved payment method {payment_method_id} for user {user.id}")
            return saved_method

        except stripe.error.StripeError as e:
            logger.error(f"Error saving payment method: {e}")
            raise Exception(f"Error saving payment method: {e}")

    @staticmethod
    def create_refund(refund_request: RefundRequest) -> Dict[str, Any]:
        """
        Process a refund through Stripe
        """
        try:
            payment = refund_request.payment

            # Create refund in Stripe
            refund = stripe.Refund.create(
                charge=payment.stripe_charge_id,
                amount=refund_request.requested_amount_cents,
                metadata={
                    "refund_request_id": refund_request.id,
                    "reason": refund_request.reason[:500],  # Stripe metadata limit
                    "platform": "LinguaFlex",
                },
            )

            # Update refund request
            refund_request.status = "PROCESSED"
            refund_request.stripe_refund_id = refund.id
            refund_request.refunded_amount_cents = refund.amount
            refund_request.refunded_at = timezone.now()
            refund_request.save()

            # Update payment status
            if refund.amount >= payment.amount_cents:
                payment.status = "REFUNDED"
            else:
                payment.status = "REFUND_REQUESTED"  # Partial refund
            payment.save()

            logger.info(f"Processed refund {refund.id} for payment {payment.id}")

            return {"refund": refund, "refund_request": refund_request}

        except stripe.error.StripeError as e:
            logger.error(f"Error processing refund: {e}")
            raise Exception(f"Refund processing error: {e}")

    @staticmethod
    def get_customer_payment_methods(user) -> list:
        """
        Get all saved payment methods for a customer
        """
        try:
            customer = StripePaymentService.create_or_get_customer(user)

            payment_methods = stripe.PaymentMethod.list(
                customer=customer.stripe_customer_id, type="card"
            )

            return payment_methods.data

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment methods: {e}")
            return []

    @staticmethod
    def delete_payment_method(payment_method_id: str) -> bool:
        """
        Delete a saved payment method
        """
        try:
            stripe.PaymentMethod.detach(payment_method_id)

            # Update in database
            SavedPaymentMethod.objects.filter(
                stripe_payment_method_id=payment_method_id
            ).update(is_active=False)

            return True

        except stripe.error.StripeError as e:
            logger.error(f"Error deleting payment method: {e}")
            return False

    @staticmethod
    def create_report_payment_intent(user, report) -> Dict[str, Any]:
        """
        Create a one-time Stripe PaymentIntent for a report purchase.

        Reuses create_or_get_customer() — no new Stripe customer logic needed.
        Amount comes from settings.ASTROLOGY_REPORT_PRICE_CENTS (default 999 = $9.99).
        A metadata tag {payment_type: "report"} lets the webhook handler route
        this payment separately from session-booking payments.
        """
        from astrology.models import ReportPayment

        price_cents = getattr(settings, "ASTROLOGY_REPORT_PRICE_CENTS", 999)
        customer = StripePaymentService.create_or_get_customer(user)

        payment_intent = stripe.PaymentIntent.create(
            amount=price_cents,
            currency="usd",
            customer=customer.stripe_customer_id,
            automatic_payment_methods={
                "enabled": True,
                "allow_redirects": "never",
            },
            metadata={
                "payment_type":     "report",
                "report_id":        str(report.id),
                "birth_profile_id": str(report.birth_profile_id),
                "user_id":          str(user.id),
                "platform":         "ParlezHub",
            },
        )

        report_payment = ReportPayment.objects.create(
            report=report,
            user=user,
            stripe_payment_intent_id=payment_intent.id,
            stripe_customer_id=customer.stripe_customer_id,
            amount_cents=price_cents,
            status=ReportPayment.Status.PENDING,
        )

        logger.info(
            f"Created report PaymentIntent {payment_intent.id} "
            f"for report #{report.id} / user {user.id}"
        )

        return {
            "payment_intent": payment_intent,
            "report_payment": report_payment,
            "client_secret":  payment_intent.client_secret,
        }


class StripeWebhookService:
    """
    Handle Stripe webhook events
    """

    @staticmethod
    def handle_payment_intent_succeeded(event_data: Dict[str, Any]):
        """
        Handle successful payment intent.

        Routes by metadata["payment_type"]:
          - "report"  → mark ReportPayment as COMPLETED and trigger report generation
          - (default) → existing session-booking logic
        """
        payment_intent = event_data["object"]
        payment_type = payment_intent.get("metadata", {}).get("payment_type", "")

        if payment_type == "report":
            StripeWebhookService._handle_report_payment_succeeded(payment_intent)
            return

        # ── Session-booking payment (existing logic) ──────────────────────
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent["id"])

            payment.status = "COMPLETED"
            payment.paid_at = timezone.now()
            payment.stripe_charge_id = (
                payment_intent.get("charges", {}).get("data", [{}])[0].get("id")
            )
            payment.save()

            # Update session booking status
            payment.session_booking.payment_status = "PAID"
            payment.session_booking.save()

            logger.info(f"Payment {payment.id} marked as completed via webhook")

        except Payment.DoesNotExist:
            logger.error(f"Payment not found for PaymentIntent {payment_intent['id']}")

    @staticmethod
    def _handle_report_payment_succeeded(payment_intent: Dict[str, Any]):
        """
        Safety-net webhook handler for report payments.

        Called when Stripe confirms payment_intent.succeeded with
        metadata[payment_type] == 'report'.  Marks the ReportPayment as
        COMPLETED so the report becomes downloadable even if the user closed
        the tab before our /confirm-payment/ endpoint was called.

        Report generation itself is intentionally NOT triggered here —
        the full PDF build (which includes Supabase upload) requires a
        synchronous response context that webhooks don't provide cleanly.
        Generation is triggered by ConfirmReportPaymentView.  If payment is
        confirmed via webhook before /confirm-payment/ is called, the view
        will detect the COMPLETED status and generate the PDF at that point.
        """
        from astrology.models import ReportPayment

        intent_id = payment_intent["id"]
        try:
            report_payment = ReportPayment.objects.get(
                stripe_payment_intent_id=intent_id
            )
            if report_payment.status != ReportPayment.Status.COMPLETED:
                report_payment.status = ReportPayment.Status.COMPLETED
                report_payment.paid_at = timezone.now()
                report_payment.save(update_fields=["status", "paid_at", "updated_at"])
                logger.info(
                    f"ReportPayment #{report_payment.id} marked COMPLETED via webhook "
                    f"(PaymentIntent {intent_id})"
                )
        except ReportPayment.DoesNotExist:
            logger.warning(
                f"Webhook: no ReportPayment found for PaymentIntent {intent_id}"
            )

    @staticmethod
    def handle_payment_intent_payment_failed(event_data: Dict[str, Any]):
        """
        Handle failed payment intent
        """
        payment_intent = event_data["object"]

        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent["id"])

            payment.status = "FAILED"
            payment.save()

            # Update session booking status
            payment.session_booking.payment_status = "FAILED"
            payment.session_booking.save()

            logger.info(f"Payment {payment.id} marked as failed via webhook")

        except Payment.DoesNotExist:
            logger.error(f"Payment not found for PaymentIntent {payment_intent['id']}")
