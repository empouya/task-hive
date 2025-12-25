from django.contrib import admin
from .models import Team, TeamMembership

# This allows us to edit memberships directly inside the Team page
class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 1  # Provides one empty row to add a member easily
    autocomplete_fields = ['user']

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    inlines = [TeamMembershipInline]

@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('team', 'user', 'role', 'joined_at')
    list_filter = ('role', 'team')
    search_fields = ('user__email', 'user__username', 'team__name')