from rest_framework import serializers
from .models import File, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone_number", "gender", "date_of_birth", "profile_picture"]
        read_only_fields = ["id", "email"]

class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False)

    def create(self, validated_data):
        # Creation logic should use Supabase Auth client instead
        raise NotImplementedError("Use Supabase Auth client for user creation")

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["id", "filename", "file", "uploaded_at", "storage_key"]
        read_only_fields = ["id", "uploaded_at"]
