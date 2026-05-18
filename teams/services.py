from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from common.exceptions import BusinessLogicError, PermissionDeniedError
from common.permissions import can_manage_members, can_manage_team, can_read_team
from tasks.models import Task
from teams.models import Invitation, Team, TeamMembership


@transaction.atomic
def create_team(*, user, data):
    team = Team.objects.create(
        name=data["name"],
        description=data.get("description", ""),
    )
    TeamMembership.objects.create(
        user=user,
        team=team,
        role=TeamMembership.Role.OWNER,
    )
    return team


def list_user_teams(*, user):
    return (
        Team.objects
        .filter(memberships__user=user)
        .prefetch_related("memberships")
        .distinct()
    )


def get_team_for_user(*, user, team_id):
    team = get_object_or_404(Team, id=team_id)

    if not can_read_team(user, team):
        raise PermissionDeniedError("You do not have access to this team.")

    return team


@transaction.atomic
def update_team(*, user, team_id, serializer_class, data):
    team = get_object_or_404(Team, id=team_id)

    if not can_manage_team(user, team):
        raise PermissionDeniedError("Admin rights required.")

    serializer = serializer_class(team, data=data, partial=True, context={"request": _RequestUser(user)})
    serializer.is_valid(raise_exception=True)
    return serializer.save()


@transaction.atomic
def soft_delete_team(*, user, team_id):
    team = get_object_or_404(Team, id=team_id)

    if not can_manage_team(user, team):
        raise PermissionDeniedError("Admin rights required.")

    team.soft_delete(deleted_by=user)
    return team


@transaction.atomic
def create_invitation(*, user, team_id, email):
    team = get_object_or_404(Team, id=team_id)

    if not can_manage_members(user, team):
        raise PermissionDeniedError("Admin rights required.")

    if not email:
        raise BusinessLogicError("Email is required.")

    if TeamMembership.objects.filter(team=team, user__email=email).exists():
        raise BusinessLogicError("User is already a member.")

    invitation, _ = Invitation.objects.update_or_create(
        team=team,
        email=email,
        defaults={
            "invited_by": user,
            "created_at": timezone.now(),
            "accepted_at": None,
        },
    )
    return invitation


def list_pending_invitations(*, user, team_id):
    team = get_object_or_404(Team, id=team_id)

    if not can_manage_members(user, team):
        raise PermissionDeniedError("Admin rights required.")

    return Invitation.objects.filter(team=team, accepted_at__isnull=True)


@transaction.atomic
def accept_invitation(*, user, token):
    invitation = get_object_or_404(Invitation, token=token)

    if not invitation.is_valid():
        raise BusinessLogicError("Invitation is invalid or expired.")

    if invitation.email != user.email:
        raise PermissionDeniedError("This invitation was not intended for this user.")

    TeamMembership.objects.get_or_create(
        team=invitation.team,
        user=user,
        defaults={"role": TeamMembership.Role.MEMBER},
    )
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["accepted_at"])

    return invitation


@transaction.atomic
def delete_invitation(*, user, team_id, invite_id):
    team = get_object_or_404(Team, id=team_id)

    if not can_manage_members(user, team):
        raise PermissionDeniedError("Admin rights required.")

    invitation = get_object_or_404(Invitation, id=invite_id, team_id=team_id)
    invitation.delete()


def list_members(*, user, team_id):
    team = get_object_or_404(Team, id=team_id)

    if not can_read_team(user, team):
        raise PermissionDeniedError("You do not have access to this team.")

    return team.memberships.all().select_related("user").order_by("joined_at")


@transaction.atomic
def remove_member(*, user, team_id, user_id):
    team = get_object_or_404(Team, id=team_id)

    if not can_manage_members(user, team):
        raise PermissionDeniedError("Admin rights required.")

    requester_membership = get_object_or_404(TeamMembership, team=team, user=user)
    target_membership = get_object_or_404(TeamMembership, team=team, user_id=user_id)

    if (
        target_membership.role == TeamMembership.Role.OWNER
        and requester_membership.role != TeamMembership.Role.OWNER
    ):
        raise PermissionDeniedError("Only owners can remove owners.")

    if target_membership.role == TeamMembership.Role.OWNER:
        owner_count = team.memberships.filter(role=TeamMembership.Role.OWNER).count()
        if owner_count <= 1:
            raise BusinessLogicError("Cannot remove the last owner.")

    Task.objects.filter(project__team=team, assignee_id=user_id).update(assignee=None)
    target_membership.delete()


class _RequestUser:
    def __init__(self, user):
        self.user = user