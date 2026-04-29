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
    payment_method_id = serializers.CharField(help_text="Stripe payment method ID from Stripe Elements")


class AddPaymentMethodView(APIView):
    """
    Add a new payment method using Stripe Elements token
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = AddPaymentMethodSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': 'Invalid payment method', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = request.user
            payment_method_id = serializer.validated_data['payment_method_id']
            
            # Get or create Stripe customer
            from .services import StripePaymentService
            customer = StripePaymentService.create_or_get_customer(user)
            
            # Retrieve the payment method and attach it to the customer
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            if payment_method.customer != customer.stripe_customer_id:
                payment_method = stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=customer.stripe_customer_id
                )
            
            response_data = {
                'success': True,
                'message': 'Payment method added successfully',
                'payment_method_id': payment_method.id,
                'card_last4': payment_method.card.last4,
                'card_brand': payment_method.card.brand,
                'saved': True
            }
            
            # Save to database
            from .models import SavedPaymentMethod
            if not SavedPaymentMethod.objects.filter(stripe_payment_method_id=payment_method.id).exists():
                SavedPaymentMethod.objects.create(
                    student=user,
                    stripe_payment_method_id=payment_method.id,
                    stripe_customer_id=customer.stripe_customer_id,
                    card_last_four=payment_method.card.last4,
                    card_brand=payment_method.card.brand,
                    card_exp_month=payment_method.card.exp_month,
                    card_exp_year=payment_method.card.exp_year
                )
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return Response({
                'success': False,
                'error': f"Failed to attach payment method: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error adding payment method: {e}")
            return Response({
                'success': False,
                'error': f"Failed to add payment method: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessBookingPaymentView(APIView):
    """
    Process payment for an existing booking session using card data
    This handles payment for bookings created separately
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_test_payment_method_id(self, card_number):
        """Map test card numbers to Stripe's pre-built test payment method IDs"""
        test_payment_methods = {
            '4242424242424242': 'pm_card_visa',                    # Visa - succeeds
            '4000000000000002': 'pm_card_chargeDeclined',          # Visa - declined
            '4000000000009995': 'pm_card_chargeDeclinedInsufficientFunds',  # Insufficient funds
            '4000000000009987': 'pm_card_chargeDeclinedLostCard',  # Lost card
            '4000000000009979': 'pm_card_chargeDeclinedStolenCard',  # Stolen card
            '5555555555554444': 'pm_card_mastercard',              # Mastercard - succeeds
            '378282246310005': 'pm_card_amex',                     # Amex - succeeds
            '4000000000000101': 'pm_card_chargeDeclinedProcessingError',  # Processing error
        }
        return test_payment_methods.get(card_number)
    
    def create_payment_method_from_card(self, card_data, customer_id):
        """Create payment method using test card mapping"""
        test_pm_id = self.get_test_payment_method_id(card_data['card_number'])
        
        if not test_pm_id:
            raise stripe.error.CardError(
                message=f"Unsupported test card: {card_data['card_number']}. Please use a supported Stripe test card.",
                param="card_number",
                code="card_not_supported"
            )
        
        try:
            # Retrieve the test payment method
            test_pm = stripe.PaymentMethod.retrieve(test_pm_id)
            
            # Create a new customer-specific payment method by attaching the test one
            test_pm.attach(customer=customer_id)
            return test_pm
            
        except stripe.error.StripeError as e:
            # If attaching fails, try with SetupIntent
            try:
                setup_intent = stripe.SetupIntent.create(
                    customer=customer_id,
                    payment_method=test_pm_id,
                    confirm=True,
                    usage='off_session',
                    automatic_payment_methods={
                        'enabled': True,
                        'allow_redirects': 'never'
                    }
                )
                
                if setup_intent.payment_method:
                    return stripe.PaymentMethod.retrieve(setup_intent.payment_method)
                else:
                    # Fallback: just return the test PM
                    return stripe.PaymentMethod.retrieve(test_pm_id)
                    
            except Exception as setup_error:
                raise stripe.error.CardError(
                    message=f"Unable to process test card {card_data['card_number']}: {str(setup_error)}",
                    param="card_number",
                    code="processing_error"
                )
    
    
    def post(self, request):
        # Input validation
        required_fields = ['booking_id']
        
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        
        if missing_fields:
            return Response({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if using payment_method_id (Stripe Elements) or saved_payment_method_id
        payment_method_id = request.data.get('payment_method_id') or request.data.get('saved_payment_method_id')
        
        if not payment_method_id:
            return Response({
                'success': False,
                'error': 'Missing payment_method_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = request.user
            data = request.data
            
            # 1. Get and validate booking
            from bookings.models import SessionBooking
            try:
                booking = SessionBooking.objects.get(
                    id=data['booking_id'],
                    student=user
                )
            except SessionBooking.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Booking not found or does not belong to you'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if booking is already paid
            if booking.payment_status == 'PAID':
                return Response({
                    'success': False,
                    'error': 'Booking is already paid'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if booking is cancelled
            if booking.status == 'CANCELLED':
                return Response({
                    'success': False,
                    'error': 'Cannot pay for cancelled booking'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if booking is confirmed by teacher
            if booking.status != 'CONFIRMED':
                return Response({
                    'success': False,
                    'error': 'Booking must be confirmed by teacher before payment'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Get gig and validate
            gig = booking.gig
            if gig.status != 'active':
                return Response({
                    'success': False,
                    'error': 'Gig is no longer available'
                }, status=status.HTTP_400_BAD_REQUEST)
            
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
                        payment_method_id,
                        customer=customer.stripe_customer_id
                    )
            except stripe.error.StripeError as e:
                return Response({
                    'success': False,
                    'error': f'Invalid payment method: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save payment method to database if requested or if it was already saved
            save_requested = request.data.get('save_payment_method', False) or request.data.get('saved_payment_method_id')
            if save_requested:
                from .models import SavedPaymentMethod
                if not SavedPaymentMethod.objects.filter(stripe_payment_method_id=payment_method.id).exists():
                    SavedPaymentMethod.objects.create(
                        student=user,
                        stripe_payment_method_id=payment_method.id,
                        stripe_customer_id=customer.stripe_customer_id,
                        card_last_four=payment_method.card.last4,
                        card_brand=payment_method.card.brand,
                        card_exp_month=payment_method.card.exp_month,
                        card_exp_year=payment_method.card.exp_year
                    )
            
            # 6. Process payment with Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount=total_amount_cents,
                currency='usd',
                customer=customer.stripe_customer_id,
                payment_method=payment_method.id,
                confirm=True,
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'  # Prevent redirect-based payment methods
                },
                metadata={
                    'session_booking_id': booking.id,
                    'gig_id': gig.id,
                    'student_id': user.id,
                    'teacher_id': booking.teacher.id,
                    'platform': 'LinguaFlex',
                    'duration_hours': str(duration_hours)
                }
            )
            
            # 7. Create payment record
            from .models import Payment
            payment = Payment.objects.create(
                session_booking=booking,
                student=user,
                teacher=booking.teacher,
                gig=gig,
                stripe_payment_intent_id=payment_intent.id,
                stripe_charge_id=payment_intent.latest_charge if payment_intent.latest_charge else '',
                stripe_customer_id=customer.stripe_customer_id,
                amount_cents=total_amount_cents,
                hourly_rate_cents=int(hourly_rate * 100),
                platform_fee_cents=platform_fee_cents,
                session_duration_hours=duration_hours,
                status='COMPLETED' if payment_intent.status == 'succeeded' else 'FAILED',
                currency='USD'
            )
            
            # 8. Update booking status
            if payment_intent.status == 'succeeded':
                booking.payment_status = 'PAID'
                booking.status = 'CONFIRMED'
                booking.save()
                
                # Note: Zoom meeting should already exist from booking confirmation
                # No need to create or update Zoom meeting during payment
                
                return Response({
                    'success': True,
                    'message': 'Payment processed successfully',
                    'payment_intent_id': payment_intent.id,
                    'booking_id': booking.id,
                    'payment_id': payment.id,
                    'amount_paid': total_amount,
                    'session_cost': session_cost,
                    'platform_fee': platform_fee,
                    'duration_hours': duration_hours,
                    'hourly_rate': hourly_rate,
                    'status': payment_intent.status,
                    'card_last4': payment_method.card.last4,
                    'card_brand': payment_method.card.brand,
                    'zoom_join_url': getattr(booking, 'zoom_join_url', None),
                    'booking_details': {
                        'start_time': booking.start_time,
                        'end_time': booking.end_time,
                        'teacher_name': f"{booking.teacher.first_name} {booking.teacher.last_name}",
                        'gig_title': gig.title if hasattr(gig, 'title') else 'Language Session'
                    }
                }, status=status.HTTP_200_OK)
            else:
                # Payment failed
                booking.payment_status = 'FAILED'
                booking.save()
                
                return Response({
                    'success': False,
                    'error': 'Payment failed',
                    'details': {
                        'status': payment_intent.status,
                        'failure_reason': payment_intent.last_payment_error.message if payment_intent.last_payment_error else 'Unknown error'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except stripe.error.CardError as e:
            return Response({
                'success': False,
                'error': str(e.user_message or e.message),
                'details': {
                    'code': e.code,
                    'decline_code': getattr(e, 'decline_code', None),
                    'param': e.param
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return Response({
                'success': False,
                'error': f"Payment processing error: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error processing booking payment: {e}")
            return Response({
                'success': False,
                'error': f"Failed to process payment: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessDirectPaymentView(APIView):
    """
    Process payment directly using card data - Complete backend payment system
    This view handles booking creation and payment processing in a single step
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_test_payment_method_id(self, card_number):
        """Map test card numbers to Stripe's pre-built test payment method IDs"""
        test_payment_methods = {
            '4242424242424242': 'pm_card_visa',                    # Visa - succeeds
            '4000000000000002': 'pm_card_chargeDeclined',          # Visa - declined
            '4000000000009995': 'pm_card_chargeDeclinedInsufficientFunds',  # Insufficient funds
            '4000000000009987': 'pm_card_chargeDeclinedLostCard',  # Lost card
            '4000000000009979': 'pm_card_chargeDeclinedStolenCard',  # Stolen card
            '5555555555554444': 'pm_card_mastercard',              # Mastercard - succeeds
            '378282246310005': 'pm_card_amex',                     # Amex - succeeds
            '4000000000000101': 'pm_card_chargeDeclinedProcessingError',  # Processing error
        }
        return test_payment_methods.get(card_number)
    
    def create_payment_method_from_card(self, card_data, customer_id):
        """Create payment method using test card mapping"""
        test_pm_id = self.get_test_payment_method_id(card_data['card_number'])
        
        if not test_pm_id:
            raise stripe.error.CardError(
                message=f"Unsupported test card: {card_data['card_number']}. Please use a supported Stripe test card.",
                param="card_number",
                code="card_not_supported"
            )
        
        try:
            # Retrieve the test payment method
            test_pm = stripe.PaymentMethod.retrieve(test_pm_id)
            
            # Create a new customer-specific payment method by attaching the test one
            test_pm.attach(customer=customer_id)
            return test_pm
            
        except stripe.error.StripeError as e:
            # If attaching fails, try with SetupIntent
            try:
                setup_intent = stripe.SetupIntent.create(
                    customer=customer_id,
                    payment_method=test_pm_id,
                    confirm=True,
                    usage='off_session',
                    automatic_payment_methods={
                        'enabled': True,
                        'allow_redirects': 'never'
                    }
                )
                
                if setup_intent.payment_method:
                    return stripe.PaymentMethod.retrieve(setup_intent.payment_method)
                else:
                    # Fallback: just return the test PM
                    return stripe.PaymentMethod.retrieve(test_pm_id)
                    
            except Exception as setup_error:
                raise stripe.error.CardError(
                    message=f"Unable to process test card {card_data['card_number']}: {str(setup_error)}",
                    param="card_number",
                    code="processing_error"
                )
    
    def post(self, request):
        # Input validation
        required_fields = ['gig_id', 'session_duration_hours', 'start_time', 'end_time']
        card_fields = ['card_number', 'exp_month', 'exp_year', 'cvc', 'cardholder_name']
        
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        missing_card_fields = [field for field in card_fields if not request.data.get(field)]
        
        if missing_fields:
            return Response({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if missing_card_fields and not request.data.get('saved_payment_method_id'):
            return Response({
                'success': False,
                'error': f'Missing card fields: {", ".join(missing_card_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = request.user
            data = request.data
            
            # 1. Validate and get gig
            from accounts.models import Gig
            try:
                gig = Gig.objects.get(id=data['gig_id'])
            except Gig.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Gig not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if gig.status != 'active':
                return Response({
                    'success': False,
                    'error': 'Gig is not available for booking'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Calculate payment amounts
            session_duration = float(data['session_duration_hours'])
            hourly_rate = float(gig.price_per_session)
            session_cost = hourly_rate * session_duration
            platform_fee = session_cost * 0.05  # 5% of session cost
            total_amount = session_cost + platform_fee
            
            # Convert to cents for Stripe
            session_cost_cents = int(session_cost * 100)
            platform_fee_cents = int(platform_fee * 100)
            total_amount_cents = int(total_amount * 100)
            
            # 3. Get or create Stripe customer
            from .services import StripePaymentService
            customer = StripePaymentService.create_or_get_customer(user)
            
            # 4. Create or get payment method
            payment_method = None
            
            if data.get('saved_payment_method_id'):
                # Use saved payment method
                from .models import SavedPaymentMethod
                try:
                    saved_method = SavedPaymentMethod.objects.get(
                        stripe_payment_method_id=data['saved_payment_method_id'],
                        student=user
                    )
                    payment_method = stripe.PaymentMethod.retrieve(saved_method.stripe_payment_method_id)
                except SavedPaymentMethod.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Saved payment method not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Create payment method from card data
                card_data = {
                    'card_number': data['card_number'],
                    'exp_month': int(data['exp_month']),
                    'exp_year': int(data['exp_year']),
                    'cvc': data['cvc'],
                    'cardholder_name': data['cardholder_name']
                }
                
                payment_method = self.create_payment_method_from_card(card_data, customer.stripe_customer_id)
                
                # Save payment method if requested
                if data.get('save_payment_method', False):
                    from .models import SavedPaymentMethod
                    SavedPaymentMethod.objects.create(
                        student=user,
                        stripe_payment_method_id=payment_method.id,
                        stripe_customer_id=customer.stripe_customer_id,
                        card_last_four=payment_method.card.last4,
                        card_brand=payment_method.card.brand,
                        card_exp_month=payment_method.card.exp_month,
                        card_exp_year=payment_method.card.exp_year
                    )
            
            # 5. Create session booking first
            from bookings.models import SessionBooking
            from datetime import datetime
            
            booking = SessionBooking.objects.create(
                student=user,
                teacher=gig.teacher.user_profile.user,
                gig=gig,
                start_time=data['start_time'],
                end_time=data['end_time'],
                duration_hours=session_duration,
                scheduled_datetime=data['start_time'],
                status='CONFIRMED',
                payment_status='PENDING'
            )
            
            # 6. Process payment with Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount=total_amount_cents,
                currency='usd',
                customer=customer.stripe_customer_id,
                payment_method=payment_method.id,
                confirm=True,
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'  # Prevent redirect-based payment methods
                },
                metadata={
                    'session_booking_id': booking.id,
                    'gig_id': gig.id,
                    'student_id': user.id,
                    'teacher_id': gig.teacher.user_profile.user.id,
                    'platform': 'LinguaFlex'
                }
            )
            
            # 7. Create payment record
            from .models import Payment
            payment = Payment.objects.create(
                session_booking=booking,
                student=user,
                teacher=gig.teacher.user_profile.user,
                gig=gig,
                stripe_payment_intent_id=payment_intent.id,
                stripe_charge_id=payment_intent.latest_charge if payment_intent.latest_charge else '',
                stripe_customer_id=customer.stripe_customer_id,
                amount_cents=total_amount_cents,
                hourly_rate_cents=int(hourly_rate * 100),
                platform_fee_cents=platform_fee_cents,
                session_duration_hours=session_duration,
                status='COMPLETED' if payment_intent.status == 'succeeded' else 'FAILED',
                currency='USD'
            )
            
            # 8. Update booking payment status
            if payment_intent.status == 'succeeded':
                booking.payment_status = 'PAID'
                booking.save()
                
                # Note: Zoom meeting should already exist from booking confirmation
                # No need to create or update Zoom meeting during payment
                
                return Response({
                    'success': True,
                    'message': 'Payment processed successfully',
                    'payment_intent_id': payment_intent.id,
                    'booking_id': booking.id,
                    'payment_id': payment.id,
                    'amount_paid': total_amount,
                    'session_cost': session_cost,
                    'platform_fee': platform_fee,
                    'status': payment_intent.status,
                    'card_last4': payment_method.card.last4,
                    'card_brand': payment_method.card.brand,
                    'zoom_join_url': booking.zoom_join_url if hasattr(booking, 'zoom_join_url') else None
                }, status=status.HTTP_200_OK)
            else:
                # Payment failed
                booking.payment_status = 'FAILED'
                booking.status = 'CANCELLED'
                booking.save()
                
                return Response({
                    'success': False,
                    'error': 'Payment failed',
                    'details': {
                        'status': payment_intent.status,
                        'failure_reason': payment_intent.last_payment_error.message if payment_intent.last_payment_error else 'Unknown error'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except stripe.error.CardError as e:
            return Response({
                'success': False,
                'error': str(e.user_message or e.message),
                'details': {
                    'code': e.code,
                    'decline_code': getattr(e, 'decline_code', None),
                    'param': e.param
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return Response({
                'success': False,
                'error': f"Payment processing error: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            return Response({
                'success': False,
                'error': f"Failed to process payment: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessPaymentView(APIView):
    """
    Process payment for a gig using saved payment method or new card
    Complete backend payment processing - no frontend required
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ProcessPaymentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': 'Invalid payment data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = request.user
            data = serializer.validated_data
            
            # Get gig
            from accounts.models import Gig
            try:
                gig = Gig.objects.get(id=data['gig_id'])
            except Gig.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Gig not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if gig is active
            if gig.status != 'active':
                return Response({
                    'success': False,
                    'error': 'Gig is not available for booking'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create customer
            from .services import StripePaymentService
            customer = StripePaymentService.create_or_get_customer(user)
            
            # Determine payment method
            payment_method_id = None
            
            if data.get('saved_payment_method_id'):
                # Use saved payment method
                payment_method_id = data['saved_payment_method_id']
                
                # Verify it belongs to the user
                from .models import SavedPaymentMethod
                try:
                    saved_method = SavedPaymentMethod.objects.get(
                        stripe_payment_method_id=payment_method_id,
                        user=user
                    )
                except SavedPaymentMethod.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Payment method not found or does not belong to user'
                    }, status=status.HTTP_404_NOT_FOUND)
                
            elif data.get('card_details'):
                # Create new payment method from card details
                card_details = data['card_details']
                
                try:
                    payment_method = stripe.PaymentMethod.create(
                        type='card',
                        card={
                            'number': card_details['card_number'],
                            'exp_month': card_details['exp_month'],
                            'exp_year': card_details['exp_year'],
                            'cvc': card_details['cvc'],
                        },
                        billing_details={
                            'name': card_details['cardholder_name'],
                            'email': user.email,
                        }
                    )
                    
                    # Attach to customer
                    payment_method.attach(customer=customer.stripe_customer_id)
                    payment_method_id = payment_method.id
                    
                    # Save for future use if requested
                    if data.get('save_card'):
                        from .models import SavedPaymentMethod
                        SavedPaymentMethod.objects.create(
                            user=user,
                            stripe_payment_method_id=payment_method_id,
                            card_last4=payment_method.card.last4,
                            card_brand=payment_method.card.brand,
                            card_exp_month=payment_method.card.exp_month,
                            card_exp_year=payment_method.card.exp_year
                        )
                        
                except stripe.error.CardError as e:
                    return Response({
                        'success': False,
                        'error': str(e.user_message or e.message),
                        'details': {
                            'code': e.code,
                            'decline_code': getattr(e, 'decline_code', None),
                            'param': e.param
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate amount (gig price in cents)
            amount_cents = int(gig.price_per_session * 100)
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                customer=customer.stripe_customer_id,
                payment_method=payment_method_id,
                confirm=True,
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'  # Prevent redirect-based payment methods
                },
                metadata={
                    'gig_id': gig.id,
                    'student_id': user.id,
                    'platform': 'LinguaFlex'
                }
            )
            
            # Create booking record
            from bookings.models import SessionBooking
            booking = SessionBooking.objects.create(
                gig=gig,
                student=user,
                teacher=gig.teacher.user_profile.user,
                total_amount=gig.price_per_session,
                status='CONFIRMED',
                payment_status='PAID'
            )
            
            # Create payment record
            from .models import Payment
            payment = Payment.objects.create(
                user=user,
                booking=booking,
                stripe_payment_intent_id=payment_intent.id,
                amount=gig.price_per_session,
                currency='USD',
                status='COMPLETED',
                payment_method_id=payment_method_id
            )
            
            return Response({
                'success': True,
                'message': 'Payment processed successfully',
                'payment_id': payment.id,
                'payment_intent_id': payment_intent.id,
                'amount': float(gig.price_per_session),
                'currency': 'usd',
                'status': 'succeeded',
                'booking_id': booking.id,
                'payment_method_saved': data.get('save_card', False),
                'used_saved_card': bool(data.get('saved_payment_method_id'))
            }, status=status.HTTP_200_OK)
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return Response({
                'success': False,
                'error': f"Payment processing error: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            return Response({
                'success': False,
                'error': f"Failed to process payment: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Required imports
from django.shortcuts import get_object_or_404
