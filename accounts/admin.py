from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.admin.sites import NotRegistered
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    fieldsets = (
        ("Account", {"fields": ("email", "username", "password"), "classes": ("tab",)}),
        ("Profile", {"fields": ("first_name", "last_name"), "classes": ("tab",)}),
        (
            "Access",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "user_permissions"),
                "classes": ("tab",),
            },
        ),
        ("Dates", {"fields": ("last_login", "date_joined"), "classes": ("tab",)}),
    )
    add_fieldsets = (
        (
            "Create account",
            {
                "classes": ("wide",),
                "fields": ("email", "username", "usable_password", "password1", "password2"),
            },
        ),
    )
    readonly_fields = ("last_login", "date_joined")
    list_display = ("email", "username", "full_name", "role", "status", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser")
    list_filter_submit = True
    list_fullwidth = True
    list_per_page = 25
    ordering = ("email",)
    search_fields = ("email", "username", "first_name", "last_name")
    date_hierarchy = "date_joined"
    actions = ("activate_users", "deactivate_users")

    @display(description="Name", ordering="first_name", empty_value="-")
    def full_name(self, obj):
        return obj.get_full_name() or "-"

    @display(
        description="Role",
        label={
            "superuser": "danger",
            "staff": "warning",
            "user": "info",
        },
    )
    def role(self, obj):
        if obj.is_superuser:
            return ("superuser", "Superuser")

        if obj.is_staff:
            return ("staff", "Staff")

        return ("user", "User")

    @display(
        description="Status",
        label={
            "active": "success",
            "inactive": "danger",
        },
    )
    def status(self, obj):
        if obj.is_active:
            return ("active", "Active")

        return ("inactive", "Inactive")

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} user(s).", messages.SUCCESS)

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} user(s).", messages.WARNING)


try:
    admin.site.unregister(Group)
except NotRegistered:
    pass


@admin.register(LogEntry)
class ActivityLogAdmin(ModelAdmin):
    list_display = (
        "action_time",
        "user_display",
        "action_type",
        "model_name",
        "object_repr",
        "change_summary",
    )
    list_filter = ("action_flag", "content_type", "user", "action_time")
    list_fullwidth = True
    list_per_page = 25
    ordering = ("-action_time",)
    date_hierarchy = "action_time"
    search_fields = (
        "object_repr",
        "change_message",
        "user__email",
        "user__username",
        "content_type__app_label",
        "content_type__model",
    )
    readonly_fields = (
        "action_time",
        "user",
        "content_type",
        "object_id",
        "object_repr",
        "action_flag",
        "change_message",
    )

    @display(description="User", ordering="user__email")
    def user_display(self, obj):
        return obj.user.get_username()

    @display(
        description="Action",
        label={
            "added": "success",
            "updated": "info",
            "deleted": "danger",
        },
    )
    def action_type(self, obj):
        if obj.action_flag == ADDITION:
            return ("added", "Added")

        if obj.action_flag == CHANGE:
            return ("updated", "Updated")

        if obj.action_flag == DELETION:
            return ("deleted", "Deleted")

        return None

    @display(description="Model", ordering="content_type__model")
    def model_name(self, obj):
        if obj.content_type:
            return obj.content_type.name.title()

        return "-"

    @display(description="Details")
    def change_summary(self, obj):
        return obj.get_change_message() or "-"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
