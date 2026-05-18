from teams.models import TeamMembership


ROLE_ORDER = {
    TeamMembership.Role.VIEWER: 10,
    TeamMembership.Role.MEMBER: 20,
    TeamMembership.Role.MANAGER: 30,
    TeamMembership.Role.ADMIN: 40,
    TeamMembership.Role.OWNER: 50,
}


def get_team_membership(user, team):
    if not user or not user.is_authenticated:
        return None

    return (
        TeamMembership.objects
        .filter(user=user, team=team)
        .select_related("user", "team")
        .first()
    )


def is_team_member(user, team):
    return get_team_membership(user, team) is not None


def has_team_role(user, team, minimum_role):
    membership = get_team_membership(user, team)

    if membership is None:
        return False

    return ROLE_ORDER[membership.role] >= ROLE_ORDER[minimum_role]


def can_read_team(user, team):
    return is_team_member(user, team)


def can_manage_team(user, team):
    return has_team_role(user, team, TeamMembership.Role.ADMIN)


def can_manage_members(user, team):
    return has_team_role(user, team, TeamMembership.Role.ADMIN)


def can_manage_projects(user, team):
    return has_team_role(user, team, TeamMembership.Role.MANAGER)


def can_write_tasks(user, team):
    return has_team_role(user, team, TeamMembership.Role.MEMBER)


def can_reorder_tasks(user, team):
    return has_team_role(user, team, TeamMembership.Role.MEMBER)


def can_comment(user, team):
    return has_team_role(user, team, TeamMembership.Role.MEMBER)