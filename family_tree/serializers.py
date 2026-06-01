from rest_framework import serializers
from .models import FamilyMember, FamilyRelationship

from core.models import User

class FamilyMemberSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    connected_user_id = serializers.UUIDField(required=False, write_only=True, allow_null=True)
    connected_user_email = serializers.EmailField(required=False, write_only=True, allow_null=True, allow_blank=True)
    
    is_connected = serializers.SerializerMethodField()
    connected_user_details = serializers.SerializerMethodField()

    class Meta:
        model = FamilyMember
        fields = [
            'id', 'name', 'gender',
            'birth_date', 'birth_time', 'birth_place',
            'connected_user_id', 'connected_user_email',
            'is_connected', 'connected_user_details',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_connected(self, obj):
        return obj.connected_user is not None

    def get_connected_user_details(self, obj):
        if obj.connected_user:
            return {
                "id": str(obj.connected_user.id),
                "email": obj.connected_user.email,
                "first_name": obj.connected_user.first_name,
                "last_name": obj.connected_user.last_name
            }
        return None

    def validate(self, data):
        # Resolve the final name, falling back to instance's name if not provided in the update
        name = data.get('name')
        if name is None and self.instance:
            name = self.instance.name

        # Resolve the final connected user connection status
        has_id = 'connected_user_id' in data
        has_email = 'connected_user_email' in data
        
        user_id = data.get('connected_user_id') if has_id else None
        email = data.get('connected_user_email') if has_email else None
        
        connected_user = None
        if has_id or has_email:
            # Attempt to resolve the connection from the input data
            if user_id:
                try:
                    connected_user = User.objects.get(pk=user_id)
                except User.DoesNotExist:
                    pass
            elif email:
                try:
                    connected_user = User.objects.get(email__iexact=email)
                except User.DoesNotExist:
                    pass
        else:
            # Fall back to the existing connected user if not updating the connection
            if self.instance:
                connected_user = self.instance.connected_user

        if not connected_user and not name:
            raise serializers.ValidationError({
                "name": "This field is required when no registered application user is connected."
            })

        return data

    def _resolve_connected_user(self, validated_data):
        user_id = validated_data.pop('connected_user_id', None)
        email = validated_data.pop('connected_user_email', None)
        
        # If explicitly set to None, it means unlink
        if user_id is None and email is None:
            return None, False

        connected_user = None
        if user_id:
            try:
                connected_user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                pass
        elif email:
            try:
                connected_user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                pass
                
        return connected_user, True

    def create(self, validated_data):
        connected_user, provided = self._resolve_connected_user(validated_data)
        if connected_user:
            validated_data['connected_user'] = connected_user
            
            # Pre-populate fields from connected user if not supplied
            if not validated_data.get('name'):
                validated_data['name'] = connected_user.get_full_name() or connected_user.username
            if not validated_data.get('gender') and connected_user.gender:
                gender_lower = connected_user.gender.lower()
                if gender_lower in ['male', 'female', 'other']:
                    validated_data['gender'] = gender_lower
            if not validated_data.get('birth_date') and connected_user.date_of_birth:
                validated_data['birth_date'] = connected_user.date_of_birth
                
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Check if connection fields were supplied
        has_id = 'connected_user_id' in validated_data
        has_email = 'connected_user_email' in validated_data
        
        if has_id or has_email:
            connected_user, provided = self._resolve_connected_user(validated_data)
            # If provided was True but resolved to None, or if we got a user, we update it
            if connected_user:
                instance.connected_user = connected_user
                
                # Pre-populate empty fields from connected user if not supplied
                if not validated_data.get('name') and not instance.name:
                    validated_data['name'] = connected_user.get_full_name() or connected_user.username
                if not validated_data.get('gender') and not instance.gender and connected_user.gender:
                    gender_lower = connected_user.gender.lower()
                    if gender_lower in ['male', 'female', 'other']:
                        validated_data['gender'] = gender_lower
                if not validated_data.get('birth_date') and not instance.birth_date and connected_user.date_of_birth:
                    validated_data['birth_date'] = connected_user.date_of_birth
            else:
                # If explicit None was sent, unlink
                instance.connected_user = None

        return super().update(instance, validated_data)


class FamilyRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyRelationship
        fields = ['id', 'profile', 'relative', 'relationship_type', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        profile = data['profile']
        relative = data['relative']
        relationship_type = data['relationship_type']
        request = self.context.get('request')

        if profile == relative:
            raise serializers.ValidationError("A family member cannot be related to themselves.")

        # Guard: Check ownership permissions
        if request and request.user:
            user = request.user
            if str(profile.user_id) != str(user.id):
                raise serializers.ValidationError("You do not have permission to manage this profile.")
            if str(relative.user_id) != str(user.id):
                raise serializers.ValidationError("You do not have permission to manage this relative profile.")

        # Check maximum parent limit (profile can have at most 2 parents)
        if relationship_type == FamilyRelationship.RelationshipType.PARENT:
            parent_count = FamilyRelationship.objects.filter(
                profile=profile,
                relationship_type=FamilyRelationship.RelationshipType.PARENT
            ).count()
            if parent_count >= 2:
                raise serializers.ValidationError(f"{profile.name} already has 2 parents defined.")

        # Check for cycles
        if relationship_type == FamilyRelationship.RelationshipType.PARENT:
            # Make sure 'profile' is not a parent/ancestor of 'relative'
            if self._has_ancestor_path(start_node=relative, target_node=profile):
                raise serializers.ValidationError(
                    f"Cannot set {relative.name} as a parent of {profile.name} "
                    f"because it creates a circular lineage cycle."
                )

        return data

    def _has_ancestor_path(self, start_node, target_node):
        """BFS to check if target_node is an ancestor/parent of start_node"""
        visited = set()
        queue = [start_node]
        
        while queue:
            current = queue.pop(0)
            if current == target_node:
                return True
            if current.id not in visited:
                visited.add(current.id)
                # Find all parents of current
                parents = FamilyRelationship.objects.filter(
                    profile=current,
                    relationship_type=FamilyRelationship.RelationshipType.PARENT
                ).select_related('relative')
                for p in parents:
                    if p.relative.id not in visited:
                        queue.append(p.relative)
        return False
