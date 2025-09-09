"""
Serializers for Stripe payment endpoints
"""
from rest_framework import serializers
from decimal import Decimal
from .models import Payment, SavedPaymentMethod, RefundRequest, StripeCustomer
from bookings.models import SessionBooking


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model
    """
    amount_dollars = serializers.ReadOnlyField()
    hourly_rate_dollars = serializers.ReadOnlyField()
    student_email = serializers.CharField(source='student.email', read_only=True)
    teacher_email = serializers.CharField(source='teacher.email', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    gig_title = serializers.CharField(source='gig.service_title', read_only=True)
    session_date = serializers.CharField(source='session_booking.scheduled_datetime', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'status', 'amount_cents', 'amount_dollars',
            'hourly_rate_cents', 'hourly_rate_dollars',
            'session_duration_hours', 'platform_fee_cents',
            'currency', 'payment_method_type',
            'student_email', 'teacher_email', 'teacher_name',
            'gig_title', 'session_date',
            'created_at', 'paid_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'amount_cents', 'hourly_rate_cents',
            'platform_fee_cents', 'created_at', 'paid_at', 'updated_at'
        ]
    
    def get_teacher_name(self, obj):
        """Get teacher's full name"""
        return obj.teacher.get_full_name() or obj.teacher.email


class CreatePaymentIntentSerializer(serializers.Serializer):
    """
    Serializer for creating payment intents
    """
    session_booking_id = serializers.IntegerField()
    payment_method_id = serializers.CharField(required=False, allow_blank=True)
    save_payment_method = serializers.BooleanField(default=False)
    
    def validate_session_booking_id(self, value):
        """Validate session booking exists and belongs to user"""
        try:
            booking = SessionBooking.objects.get(id=value)
            
            # Check if user is the student for this booking
            if booking.student != self.context['request'].user:
                raise serializers.ValidationError("You can only pay for your own bookings.")
            
            # Check if booking is not already paid
            if hasattr(booking, 'payment') and booking.payment.status == 'COMPLETED':
                raise serializers.ValidationError("This booking has already been paid for.")
            
            # Check if booking is confirmed by teacher
            if booking.status != 'CONFIRMED':
                raise serializers.ValidationError("Booking must be confirmed by teacher before payment.")
            
            return value
            
        except SessionBooking.DoesNotExist:
            raise serializers.ValidationError("Session booking not found.")


class ConfirmPaymentSerializer(serializers.Serializer):
    """
    Serializer for confirming payments
    """
    payment_intent_id = serializers.CharField()
    
    def validate_payment_intent_id(self, value):
        """Validate payment intent belongs to user"""
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=value)
            
            if payment.student != self.context['request'].user:
                raise serializers.ValidationError("You can only confirm your own payments.")
            
            return value
            
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found.")


class SavedPaymentMethodSerializer(serializers.ModelSerializer):
    """
    Serializer for saved payment methods
    """
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SavedPaymentMethod
        fields = [
            'id', 'stripe_payment_method_id', 'card_brand',
            'card_last_four', 'card_exp_month', 'card_exp_year',
            'is_default', 'display_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_display_name(self, obj):
        """Get formatted display name"""
        return str(obj)


class RefundRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for refund requests
    """
    requested_amount_dollars = serializers.ReadOnlyField()
    refunded_amount_dollars = serializers.ReadOnlyField()
    payment_details = serializers.SerializerMethodField()
    
    class Meta:
        model = RefundRequest
        fields = [
            'id', 'reason', 'requested_amount_cents', 'requested_amount_dollars',
            'status', 'admin_notes', 'refunded_amount_cents', 'refunded_amount_dollars',
            'payment_details', 'created_at', 'reviewed_at', 'refunded_at'
        ]
        read_only_fields = [
            'id', 'status', 'admin_notes', 'refunded_amount_cents',
            'created_at', 'reviewed_at', 'refunded_at'
        ]
    
    def get_payment_details(self, obj):
        """Get payment details"""
        payment = obj.payment
        return {
            'id': payment.id,
            'amount_dollars': payment.amount_dollars,
            'teacher_name': payment.teacher.get_full_name() or payment.teacher.email,
            'gig_title': payment.gig.service_title,
            'session_date': payment.session_booking.scheduled_datetime.isoformat() if payment.session_booking.scheduled_datetime else None
        }


class CreateRefundRequestSerializer(serializers.Serializer):
    """
    Serializer for creating refund requests
    """
    payment_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=1000)
    requested_amount_dollars = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    def validate_payment_id(self, value):
        """Validate payment exists and belongs to user"""
        try:
            payment = Payment.objects.get(id=value)
            
            if payment.student != self.context['request'].user:
                raise serializers.ValidationError("You can only request refunds for your own payments.")
            
            if payment.status != 'COMPLETED':
                raise serializers.ValidationError("Can only refund completed payments.")
            
            # Check if refund already requested
            if payment.refund_requests.filter(status__in=['PENDING', 'APPROVED']).exists():
                raise serializers.ValidationError("Refund already requested for this payment.")
            
            return value
            
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found.")
    
    def validate_requested_amount_dollars(self, value):
        """Validate refund amount"""
        if value <= 0:
            raise serializers.ValidationError("Refund amount must be greater than 0.")
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        try:
            payment = Payment.objects.get(id=data['payment_id'])
            requested_amount_cents = int(data['requested_amount_dollars'] * 100)
            
            if requested_amount_cents > payment.amount_cents:
                raise serializers.ValidationError(
                    "Refund amount cannot exceed the original payment amount."
                )
            
            data['requested_amount_cents'] = requested_amount_cents
            
        except Payment.DoesNotExist:
            pass  # Already validated in payment_id validation
        
        return data


class AdminRefundReviewSerializer(serializers.ModelSerializer):
    """
    Admin serializer for reviewing refund requests
    """
    payment_details = serializers.SerializerMethodField()
    student_details = serializers.SerializerMethodField()
    
    class Meta:
        model = RefundRequest
        fields = [
            'id', 'reason', 'requested_amount_dollars', 'status',
            'admin_notes', 'payment_details', 'student_details',
            'created_at', 'reviewed_at'
        ]
        read_only_fields = ['id', 'reason', 'requested_amount_dollars', 'created_at']
    
    def get_payment_details(self, obj):
        """Get detailed payment information"""
        payment = obj.payment
        return {
            'id': payment.id,
            'amount_dollars': payment.amount_dollars,
            'teacher_name': payment.teacher.get_full_name() or payment.teacher.email,
            'teacher_email': payment.teacher.email,
            'gig_title': payment.gig.service_title,
            'session_date': payment.session_booking.scheduled_datetime.isoformat() if payment.session_booking.scheduled_datetime else None,
            'payment_date': payment.paid_at.isoformat() if payment.paid_at else None
        }
    
    def get_student_details(self, obj):
        """Get student information"""
        student = obj.student
        return {
            'id': student.id,
            'name': student.get_full_name() or student.email,
            'email': student.email
        }


class PaymentDashboardSerializer(serializers.Serializer):
    """
    Serializer for payment dashboard data
    """
    total_payments = serializers.IntegerField()
    total_revenue_dollars = serializers.DecimalField(max_digits=12, decimal_places=2)
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    pending_refunds = serializers.IntegerField()
    recent_payments = PaymentSerializer(many=True)
    
    # Date range filters
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)


class StripeCustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Stripe customer data
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = StripeCustomer
        fields = [
            'id', 'stripe_customer_id', 'email', 'name',
            'user_email', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'stripe_customer_id', 'created_at']
