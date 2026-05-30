from __future__ import annotations

from rest_framework.permissions import BasePermission, IsAdminUser
from rest_framework.request import Request
from rest_framework.views import View

from apps.client_portal import models as orm


def _get_user_profile(request: Request) -> orm.UserProfile | None:
    """Return the UserProfile for the authenticated user, or None."""
    if not request.user or not request.user.is_authenticated:
        return None
    try:
        return orm.UserProfile.objects.get(user=request.user)
    except orm.UserProfile.DoesNotExist:
        return None


def _get_obj_org_id(obj: object) -> object:
    """Extract the organization id from an ORM object by convention."""
    if hasattr(obj, 'organization_id'):
        return obj.organization_id
    if hasattr(obj, 'organization'):
        org = obj.organization
        return org.id if org else None
    if hasattr(obj, 'project'):
        project = obj.project
        if project:
            return project.organization_id
    if hasattr(obj, 'milestone'):
        milestone = obj.milestone
        if milestone:
            return milestone.project.organization_id
    if hasattr(obj, 'deliverable'):
        deliverable = obj.deliverable
        if deliverable:
            return deliverable.milestone.project.organization_id
    if hasattr(obj, 'deliverable_version'):
        dv = obj.deliverable_version
        if dv:
            return dv.deliverable.milestone.project.organization_id
    if hasattr(obj, 'thread'):
        thread = obj.thread
        if thread:
            return thread.project.organization_id
    return None


class IsClientOfOrganization(BasePermission):
    """Allow access only to client users acting within their own organization."""

    message = 'You do not have permission to access this resource.'

    def has_permission(self, request: Request, view: View) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: View, obj: object) -> bool:
        profile = _get_user_profile(request)
        if profile is None:
            return False
        if not profile.is_client:
            return False
        obj_org_id = _get_obj_org_id(obj)
        return str(obj_org_id) == str(profile.organization_id)


class IsStaffOrClientOfOrganization(BasePermission):
    """Staff users bypass all restrictions; client users are org-scoped."""

    message = 'You do not have permission to access this resource.'

    def has_permission(self, request: Request, view: View) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: View, obj: object) -> bool:
        if request.user.is_staff:
            return True
        profile = _get_user_profile(request)
        if profile is None:
            return False
        if not profile.is_client:
            return True
        obj_org_id = _get_obj_org_id(obj)
        return str(obj_org_id) == str(profile.organization_id)


class IsApprover(BasePermission):
    """Only the assigned reviewer on an Approval may approve/reject/revise it."""

    message = 'Only the assigned reviewer may act on this approval.'

    def has_permission(self, request: Request, view: View) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: View, obj: object) -> bool:
        if request.user.is_staff:
            return True
        profile = _get_user_profile(request)
        if profile is None:
            return False
        if hasattr(obj, 'reviewer_id'):
            return str(obj.reviewer_id) == str(profile.id)
        return False
