from rest_framework import serializers
from .models import BirthProfile


class BirthProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BirthProfile
        fields = [
            'id', 'user_name',
            'birth_year', 'birth_month', 'birth_day',
            'birth_hour', 'birth_minute',
            'city', 'country_code',
            'timezone_str', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user_name', 'timezone_str', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.email
