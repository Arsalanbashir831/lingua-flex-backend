from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from core.models import User

from .models import FamilyMember, FamilyRelationship
from .serializers import FamilyMemberSerializer, FamilyRelationshipSerializer

class FamilyTreeView(APIView):
    """
    GET — Fetches the entire family tree nodes and edges for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Fetch all family members owned by the user
        members = FamilyMember.objects.filter(user=user)
        member_map = {m.id: m for m in members}

        # Build nodes payload
        nodes = FamilyMemberSerializer(members, many=True).data

        # Fetch all relationships connecting these members
        relationships = FamilyRelationship.objects.filter(
            profile_id__in=member_map.keys(),
            relative_id__in=member_map.keys()
        )

        edges = []
        for r in relationships:
            edges.append({
                "id": str(r.id),
                "from_id": str(r.profile_id),
                "to_id": str(r.relative_id),
                "type": r.relationship_type,
            })

        return Response({
            "nodes": nodes,
            "edges": edges
        })


class FamilyMemberListView(APIView):
    """
    GET  — List all family members.
    POST — Create a new family member.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        members = FamilyMember.objects.filter(user=request.user)
        serializer = FamilyMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FamilyMemberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        member = serializer.save(user=request.user)
        return Response(FamilyMemberSerializer(member).data, status=status.HTTP_201_CREATED)


class FamilyMemberDetailView(APIView):
    """
    GET    — Retrieve a family member.
    PUT    — Update a family member.
    DELETE — Delete a family member.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return FamilyMember.objects.get(pk=pk, user=request.user)
        except FamilyMember.DoesNotExist:
            return None

    def get(self, request, pk):
        member = self.get_object(request, pk)
        if not member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(FamilyMemberSerializer(member).data)

    def put(self, request, pk):
        member = self.get_object(request, pk)
        if not member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = FamilyMemberSerializer(member, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        member = serializer.save()
        return Response(FamilyMemberSerializer(member).data)

    def delete(self, request, pk):
        member = self.get_object(request, pk)
        if not member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FamilyRelationshipView(APIView):
    """
    POST — Creates a relationship connection between two FamilyMember nodes.
    
    Expected Payload:
      {
        "profile_id": "uuid-1",
        "relative_id": "uuid-2",
        "relationship_type": "parent" | "spouse"
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile_id = request.data.get("profile_id")
        relative_id = request.data.get("relative_id")
        rel_type = request.data.get("relationship_type")

        if not all([profile_id, relative_id, rel_type]):
            return Response(
                {"detail": "profile_id, relative_id, and relationship_type are all required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            profile = FamilyMember.objects.get(pk=profile_id, user=request.user)
            relative = FamilyMember.objects.get(pk=relative_id, user=request.user)
        except FamilyMember.DoesNotExist:
            return Response({"detail": "One or both family members not found."}, status=status.HTTP_404_NOT_FOUND)

        # Build serializer payload & run permissions and cycle validations
        serializer = FamilyRelationshipSerializer(
            data={
                "profile": profile.id,
                "relative": relative.id,
                "relationship_type": rel_type
            },
            context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Save relationship
        relationship = serializer.save()

        # Symmetric spouse handling
        if rel_type == FamilyRelationship.RelationshipType.SPOUSE:
            FamilyRelationship.objects.get_or_create(
                profile=relative,
                relative=profile,
                relationship_type=FamilyRelationship.RelationshipType.SPOUSE
            )

        return Response(FamilyRelationshipSerializer(relationship).data, status=status.HTTP_201_CREATED)


class FamilyRelationshipRemoveView(APIView):
    """
    POST — Removes a relationship connection between two FamilyMember nodes.
    
    Expected Payload:
      {
        "profile_id": "uuid-1",
        "relative_id": "uuid-2",
        "relationship_type": "parent" | "spouse"
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile_id = request.data.get("profile_id")
        relative_id = request.data.get("relative_id")
        rel_type = request.data.get("relationship_type")

        if not all([profile_id, relative_id, rel_type]):
            return Response(
                {"detail": "profile_id, relative_id, and relationship_type are all required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            profile = FamilyMember.objects.get(pk=profile_id, user=request.user)
            relative = FamilyMember.objects.get(pk=relative_id, user=request.user)
        except FamilyMember.DoesNotExist:
            return Response({"detail": "One or both family members not found."}, status=status.HTTP_404_NOT_FOUND)

        # Delete relation
        deleted_count, _ = FamilyRelationship.objects.filter(
            profile=profile,
            relative=relative,
            relationship_type=rel_type
        ).delete()

        # Symmetric spouse deletion handling
        if rel_type == FamilyRelationship.RelationshipType.SPOUSE:
            FamilyRelationship.objects.filter(
                profile=relative,
                relative=profile,
                relationship_type=FamilyRelationship.RelationshipType.SPOUSE
            ).delete()

        if deleted_count == 0:
            return Response({"detail": "Relationship not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": "Relationship removed successfully."}, status=status.HTTP_200_OK)


class FamilyTreeUsersListView(APIView):
    """
    GET — Autocomplete list of registered users for the family tree combo box.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        users = User.objects.all()

        if query:
            users = users.filter(
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )

        # Exclude the requesting user to avoid self-linking in the autocomplete list
        users = users.exclude(id=request.user.id)

        # Limit to 50 results for optimal database performance
        users = users.order_by("first_name", "last_name", "email")[:50]

        data = []
        for u in users:
            data.append({
                "id": str(u.id),
                "email": u.email,
                "first_name": u.first_name or "",
                "last_name": u.last_name or "",
                "name": u.get_full_name() or u.username
            })

        return Response(data, status=status.HTTP_200_OK)
