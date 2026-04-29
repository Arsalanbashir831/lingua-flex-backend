"""
Serializers for Stripe payment endpoints
"""

from rest_framework import serializers
from .models import SavedPaymentMethod


class SavedPaymentMethodSerializer(serializers.ModelSerializer):
    """
    Serializer for saved payment methods
    """

    display_name = serializers.SerializerMethodField()

    class Meta:
        model = SavedPaymentMethod
        fields = [
            "id",
            "stripe_payment_method_id",
            "card_brand",
            "card_last_four",
            "card_exp_month",
            "card_exp_year",
            "is_default",
            "display_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_display_name(self, obj):
        """Get formatted display name"""
        return str(obj)
