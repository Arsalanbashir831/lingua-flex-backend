from rest_framework import serializers
from .models import PaymentRecord, PaymentRefund
from core.serializers import UserSerializer

class PaymentRecordSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PaymentRecord
        fields = ['id', 'user', 'amount', 'currency', 'status',
                 'stripe_payment_intent_id', 'created_at', 'updated_at',
                 'description', 'metadata']
        read_only_fields = ['stripe_payment_intent_id', 'created_at', 'updated_at']

    def validate(self, data):
        if 'amount' in data and data['amount'] <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return data

class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRefund
        fields = ['id', 'payment', 'amount', 'reason', 'stripe_refund_id', 'created_at', 'metadata']
        read_only_fields = ['stripe_refund_id', 'created_at']

    def validate(self, data):
        payment = data['payment']
        if data['amount'] > payment.amount:
            raise serializers.ValidationError("Refund amount cannot be greater than payment amount")
        if payment.status != 'completed':
            raise serializers.ValidationError("Can only refund completed payments")
        return data
