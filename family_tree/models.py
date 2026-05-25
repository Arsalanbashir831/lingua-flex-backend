import uuid
from django.db import models
from core.models import User

class FamilyMember(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="family_members",
        help_text="The user who owns this family member profile."
    )
    name = models.CharField(max_length=255)
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        blank=True,
        null=True
    )
    birth_date = models.DateField(blank=True, null=True)
    birth_time = models.TimeField(blank=True, null=True)
    birth_place = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "family_members"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} (Member of {self.user.email})"


class FamilyRelationship(models.Model):
    class RelationshipType(models.TextChoices):
        PARENT = "parent", "Parent"
        SPOUSE = "spouse", "Spouse"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        FamilyMember,
        on_delete=models.CASCADE,
        related_name="relationships_from",
        help_text="The member whose relation is being defined"
    )
    relative = models.ForeignKey(
        FamilyMember,
        on_delete=models.CASCADE,
        related_name="relationships_to",
        help_text="The relative (parent or spouse)"
    )
    relationship_type = models.CharField(
        max_length=20,
        choices=RelationshipType.choices
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "family_tree_relationships"
        unique_together = ("profile", "relative", "relationship_type")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.relative.name} is the {self.relationship_type} of {self.profile.name}"
