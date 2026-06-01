import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import User
from .models import FamilyMember, FamilyRelationship

class FamilyTreeTests(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            id=str(uuid.uuid4()),
            email="user1@example.com",
            password="testpassword123",
            first_name="User",
            last_name="One"
        )
        self.user2 = User.objects.create_user(
            id=str(uuid.uuid4()),
            email="user2@example.com",
            password="testpassword123",
            first_name="User",
            last_name="Two"
        )

        # URLs
        self.summary_url = reverse("family-tree-summary")
        self.member_list_url = reverse("family-member-list")
        self.relationship_url = reverse("family-relationship")
        self.relationship_remove_url = reverse("family-relationship-remove")

    def test_authentication_required(self):
        """Verify that all family tree endpoints require authentication."""
        urls = [
            (self.summary_url, "get", None),
            (self.member_list_url, "get", None),
            (self.member_list_url, "post", {}),
            (self.relationship_url, "post", {}),
            (self.relationship_remove_url, "post", {})
        ]
        for url, method, data in urls:
            if method == "get":
                response = self.client.get(url)
            else:
                response = self.client.post(url, data)
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_member_crud(self):
        """Verify standard CRUD operations for family members."""
        self.client.force_authenticate(user=self.user1)

        # 1. Create a member
        payload = {
            "name": "Member A",
            "gender": "male",
            "birth_date": "1990-05-15",
            "birth_time": "12:30:00",
            "birth_place": "New York, USA"
        }
        response = self.client.post(self.member_url_for_list(), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        member_id = response.data["id"]
        self.assertEqual(response.data["name"], "Member A")

        # 2. Get list of members
        response = self.client.get(self.member_url_for_list())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], member_id)

        # 3. Retrieve single member
        detail_url = reverse("family-member-detail", kwargs={"pk": member_id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["birth_place"], "New York, USA")

        # 4. Update member
        update_payload = {"name": "Member A Updated"}
        response = self.client.put(detail_url, update_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Member A Updated")

        # 5. Delete member
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(FamilyMember.objects.filter(pk=member_id).count(), 0)

    def test_ownership_isolation(self):
        """Verify that users cannot see or modify other users' family members."""
        # User 1 creates a member
        member1 = FamilyMember.objects.create(
            user=self.user1,
            name="User 1 Family Member"
        )

        # Authenticate User 2
        self.client.force_authenticate(user=self.user2)

        # Attempt to retrieve User 1's member
        detail_url = reverse("family-member-detail", kwargs={"pk": member1.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Attempt to delete User 1's member
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(FamilyMember.objects.filter(pk=member1.id).count(), 1)

    def test_relationship_creation_and_removal(self):
        """Verify parent and spouse relationship workflows."""
        self.client.force_authenticate(user=self.user1)

        # Create two members
        member_a = FamilyMember.objects.create(user=self.user1, name="Child")
        member_b = FamilyMember.objects.create(user=self.user1, name="Parent")

        # Create parent-child relationship (B is parent of A)
        payload = {
            "profile_id": str(member_a.id),
            "relative_id": str(member_b.id),
            "relationship_type": "parent"
        }
        response = self.client.post(self.relationship_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify in DB
        rel_exists = FamilyRelationship.objects.filter(
            profile=member_a,
            relative=member_b,
            relationship_type="parent"
        ).exists()
        self.assertTrue(rel_exists)

        # Remove the relationship
        response = self.client.post(self.relationship_remove_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(FamilyRelationship.objects.filter(profile=member_a, relative=member_b).exists())

    def test_symmetric_spouse_handling(self):
        """Verify that spouse relationship handles symmetric link creation and deletion automatically."""
        self.client.force_authenticate(user=self.user1)

        # Create spouse A and B
        spouse_a = FamilyMember.objects.create(user=self.user1, name="Spouse A")
        spouse_b = FamilyMember.objects.create(user=self.user1, name="Spouse B")

        # Create spouse relationship
        payload = {
            "profile_id": str(spouse_a.id),
            "relative_id": str(spouse_b.id),
            "relationship_type": "spouse"
        }
        response = self.client.post(self.relationship_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify symmetric relationship exists in DB
        self.assertTrue(FamilyRelationship.objects.filter(profile=spouse_a, relative=spouse_b, relationship_type="spouse").exists())
        self.assertTrue(FamilyRelationship.objects.filter(profile=spouse_b, relative=spouse_a, relationship_type="spouse").exists())

        # Remove spouse relationship
        response = self.client.post(self.relationship_remove_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify both links deleted
        self.assertFalse(FamilyRelationship.objects.filter(profile=spouse_a, relative=spouse_b).exists())
        self.assertFalse(FamilyRelationship.objects.filter(profile=spouse_b, relative=spouse_a).exists())

    def test_double_parent_limit(self):
        """Verify that a member cannot have more than 2 parents."""
        self.client.force_authenticate(user=self.user1)

        child = FamilyMember.objects.create(user=self.user1, name="Child")
        parent1 = FamilyMember.objects.create(user=self.user1, name="Parent 1")
        parent2 = FamilyMember.objects.create(user=self.user1, name="Parent 2")
        parent3 = FamilyMember.objects.create(user=self.user1, name="Parent 3")

        # Add parent 1 and 2
        FamilyRelationship.objects.create(profile=child, relative=parent1, relationship_type="parent")
        FamilyRelationship.objects.create(profile=child, relative=parent2, relationship_type="parent")

        # Try to add parent 3
        payload = {
            "profile_id": str(child.id),
            "relative_id": str(parent3.id),
            "relationship_type": "parent"
        }
        response = self.client.post(self.relationship_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already has 2 parents defined", str(response.data))

    def test_cycle_detection(self):
        """Verify that lineage cycle detection blocks circular parent relationships."""
        self.client.force_authenticate(user=self.user1)

        # Create members: Grandparent (A), Parent (B), Child (C)
        a = FamilyMember.objects.create(user=self.user1, name="A")
        b = FamilyMember.objects.create(user=self.user1, name="B")
        c = FamilyMember.objects.create(user=self.user1, name="C")

        # Set B as parent of C (C --parent--> B)
        FamilyRelationship.objects.create(profile=c, relative=b, relationship_type="parent")

        # Set A as parent of B (B --parent--> A)
        FamilyRelationship.objects.create(profile=b, relative=a, relationship_type="parent")

        # Try to set C as parent of A (A --parent--> C). This should create a cycle: A -> C -> B -> A.
        payload = {
            "profile_id": str(a.id),
            "relative_id": str(c.id),
            "relationship_type": "parent"
        }
        response = self.client.post(self.relationship_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("circular lineage cycle", str(response.data))

    def test_cascading_deletes(self):
        """Verify that deleting a member automatically deletes all relationships they are involved in."""
        self.client.force_authenticate(user=self.user1)

        member_a = FamilyMember.objects.create(user=self.user1, name="A")
        member_b = FamilyMember.objects.create(user=self.user1, name="B")

        # Link as spouses
        FamilyRelationship.objects.create(profile=member_a, relative=member_b, relationship_type="spouse")
        FamilyRelationship.objects.create(profile=member_b, relative=member_a, relationship_type="spouse")

        self.assertEqual(FamilyRelationship.objects.filter(relationship_type="spouse").count(), 2)

        # Delete member A
        member_a.delete()

        # Both relationship rows should be cascades deleted
        self.assertEqual(FamilyRelationship.objects.count(), 0)

    def test_tree_summary(self):
        """Verify tree summary retrieves nodes and edges correctly."""
        self.client.force_authenticate(user=self.user1)

        member_a = FamilyMember.objects.create(user=self.user1, name="A", gender="male")
        member_b = FamilyMember.objects.create(user=self.user1, name="B", gender="female")
        FamilyRelationship.objects.create(profile=member_a, relative=member_b, relationship_type="spouse")

        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify nodes and edges shape
        self.assertEqual(len(response.data["nodes"]), 2)
        self.assertEqual(len(response.data["edges"]), 1)
        self.assertEqual(response.data["edges"][0]["type"], "spouse")

    def test_users_autocomplete_search(self):
        """Verify the autocomplete search API works and excludes the self user."""
        self.client.force_authenticate(user=self.user1)
        
        users_url = reverse("family-tree-users-list")
        
        # 1. Standard listing without query should show user2
        response = self.client.get(users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should contain user2, but exclude user1 (requesting user)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.user2.id))
        self.assertEqual(response.data[0]["email"], "user2@example.com")
        self.assertEqual(response.data[0]["name"], "User Two")

        # 2. Filter query matching user2 email
        response = self.client.get(f"{users_url}?q=user2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # 3. Filter query not matching anything
        response = self.client.get(f"{users_url}?q=nonexistent")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_member_linking_by_uuid(self):
        """Verify creating a member and linking by connected_user_id pre-populates details."""
        self.client.force_authenticate(user=self.user1)
        
        # Give user2 some profile details
        self.user2.gender = "female"
        self.user2.date_of_birth = "1992-08-20"
        self.user2.save()

        payload = {
            "connected_user_id": str(self.user2.id)
            # Empty name, gender, birth_date to verify pre-population
        }
        response = self.client.post(self.member_url_for_list(), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["is_connected"], True)
        self.assertEqual(response.data["name"], "User Two")
        self.assertEqual(response.data["gender"], "female")
        self.assertEqual(response.data["birth_date"], "1992-08-20")
        self.assertEqual(response.data["connected_user_details"]["email"], "user2@example.com")

    def test_create_member_linking_by_email(self):
        """Verify creating a member and linking by connected_user_email."""
        self.client.force_authenticate(user=self.user1)

        payload = {
            "name": "Custom Name override",
            "connected_user_email": "user2@example.com"
        }
        response = self.client.post(self.member_url_for_list(), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["is_connected"], True)
        # Kept the manual name since it was explicitly supplied
        self.assertEqual(response.data["name"], "Custom Name override")
        self.assertEqual(response.data["connected_user_details"]["id"], str(self.user2.id))

    def test_create_member_linking_fallback(self):
        """Verify that a non-existent connection email falls back gracefully to a manual node."""
        self.client.force_authenticate(user=self.user1)

        payload = {
            "name": "Manual Member",
            "gender": "male",
            "connected_user_email": "doesnotexist@example.com"
        }
        response = self.client.post(self.member_url_for_list(), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["is_connected"], False)
        self.assertIsNone(response.data["connected_user_details"])
        self.assertEqual(response.data["name"], "Manual Member")

    def test_update_member_linking_and_unlinking(self):
        """Verify that updating connection fields can link or unlink an existing member."""
        self.client.force_authenticate(user=self.user1)

        # Create a manual member
        member = FamilyMember.objects.create(user=self.user1, name="Old Member")
        detail_url = reverse("family-member-detail", kwargs={"pk": member.id})

        # 1. Update to link the user
        response = self.client.put(detail_url, {"connected_user_id": str(self.user2.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_connected"], True)
        self.assertEqual(response.data["connected_user_details"]["email"], "user2@example.com")

        # 2. Update connection fields to None to unlink
        response = self.client.put(detail_url, {"connected_user_id": None, "connected_user_email": None}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_connected"], False)
        self.assertIsNone(response.data["connected_user_details"])

    def member_url_for_list(self):
        return self.member_list_url
