from rest_framework import serializers
from .models import FamilyMember, FamilyRelationship

class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = [
            'id', 'name', 'gender',
            'birth_date', 'birth_time', 'birth_place',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
