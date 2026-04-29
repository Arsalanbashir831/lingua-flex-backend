from rest_framework import serializers
from .models import TeacherAvailability, SessionBooking


class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAvailability
        fields = "__all__"
        read_only_fields = ["teacher"]

    def create(self, validated_data):
        validated_data["teacher"] = self.context["request"].user
        return super().create(validated_data)


class SessionBookingSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    duration_hours = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=True
    )
    payment_id = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()

    class Meta:
        model = SessionBooking
        fields = "__all__"
        read_only_fields = [
            "student",
            "status",
            "zoom_meeting_id",
            "zoom_join_url",
            "payment_id",
            "payment_details",
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}"

    def get_payment_id(self, obj):
        """Get the payment ID associated with this booking"""
        try:
            if hasattr(obj, "payment") and obj.payment:
                return obj.payment.id
            return None
        except Exception:
            return None

    def get_payment_details(self, obj):
        """Get payment details for this booking"""
        try:
            if hasattr(obj, "payment") and obj.payment:
                payment = obj.payment
                return {
                    "payment_id": payment.id,
                    "amount_paid": float(payment.amount_dollars),
                    "payment_status": payment.status,
                    "stripe_payment_intent_id": payment.stripe_payment_intent_id,
                    "platform_fee": float(payment.platform_fee_cents / 100),
                    "session_cost": float(
                        (payment.amount_cents - payment.platform_fee_cents) / 100
                    ),
                    "total_amount": float(payment.amount_cents / 100),
                    "payment_date": payment.created_at.isoformat()
                    if payment.created_at
                    else None,
                    "currency": payment.currency,
                }

            # If no payment exists, calculate expected amounts
            if obj.gig and getattr(obj, "duration_hours", None):
                hourly_rate = float(obj.gig.price_per_session)
                duration = float(obj.duration_hours)
                session_cost = hourly_rate * duration

                # Calculate platform fee using the centralized service
                from stripe_payments.services import StripePaymentService
                from decimal import Decimal

                platform_fee_cents = StripePaymentService.calculate_platform_fee(
                    int(hourly_rate * 100), Decimal(str(duration))
                )
                platform_fee = float(platform_fee_cents / 100)

                total_amount = session_cost + platform_fee

                return {
                    "payment_id": None,
                    "amount_paid": 0.0,
                    "payment_status": obj.payment_status or "UNPAID",
                    "stripe_payment_intent_id": None,
                    "platform_fee": round(platform_fee, 2),
                    "session_cost": round(session_cost, 2),
                    "total_amount": round(total_amount, 2),
                    "payment_date": None,
                    "currency": "USD",
                }
            return None
        except Exception:
            return None

    def validate(self, attrs):
        """Validate start_time, end_time, and duration_hours"""
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        duration_hours = attrs.get("duration_hours")

        if start_time and end_time and duration_hours:
            # Calculate actual duration from start and end times
            duration_seconds = (end_time - start_time).total_seconds()
            actual_duration_hours = duration_seconds / 3600

            # Allow for small rounding differences (within 1 minute tolerance)
            duration_diff = abs(actual_duration_hours - float(duration_hours))
            if duration_diff > 0.017:  # 1 minute = 0.017 hours
                raise serializers.ValidationError(
                    f"Duration mismatch: provided duration_hours ({duration_hours}) doesn't match "
                    f"the time difference between start_time and end_time ({actual_duration_hours:.2f} hours)"
                )

            # Set scheduled_datetime if not provided
            if not attrs.get("scheduled_datetime"):
                attrs["scheduled_datetime"] = start_time

        return attrs

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user
        validated_data["status"] = "PENDING"
        return super().create(validated_data)
