from django.urls import path
from .views import (
    FamilyTreeView, FamilyMemberListView, FamilyMemberDetailView,
    FamilyRelationshipView, FamilyRelationshipRemoveView,
    FamilyTreeUsersListView
)

urlpatterns = [
    # Nodes/Edges summary
    path('', FamilyTreeView.as_view(), name='family-tree-summary'),

    # Users Autocomplete
    path('users/', FamilyTreeUsersListView.as_view(), name='family-tree-users-list'),

    # Members management
    path('members/', FamilyMemberListView.as_view(), name='family-member-list'),
    path('members/<uuid:pk>/', FamilyMemberDetailView.as_view(), name='family-member-detail'),

    # Relationships management
    path('relationships/', FamilyRelationshipView.as_view(), name='family-relationship'),
    path('relationships/remove/', FamilyRelationshipRemoveView.as_view(), name='family-relationship-remove'),
]
