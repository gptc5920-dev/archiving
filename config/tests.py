from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from django.test import SimpleTestCase, TestCase


class RootURLTests(SimpleTestCase):
    def test_root_redirects_to_admin(self):
        response = self.client.get("/")

        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)


class SidebarSettingsTests(SimpleTestCase):
    def test_dashboard_is_above_student_records(self):
        navigation = settings.UNFOLD["SIDEBAR"]["navigation"]
        section_titles = [section["title"] for section in navigation]
        sidebar_titles = [
            item["title"]
            for section in navigation
            for item in section.get("items", [])
        ]

        self.assertNotIn("Workspace", section_titles)
        self.assertNotIn("Staff", sidebar_titles)
        self.assertEqual(navigation[0]["title"], "Dashboard")
        self.assertEqual(navigation[0]["items"][0]["title"], "Overall Dashboard")
        self.assertEqual(navigation[1]["title"], "Student Records")
        self.assertEqual(navigation[-1]["title"], "System")
        self.assertEqual(navigation[-1]["items"][-1]["title"], "Activity Log")

    def test_sidebar_search_is_disabled(self):
        sidebar = settings.UNFOLD["SIDEBAR"]

        self.assertFalse(sidebar["show_search"])
        self.assertFalse(sidebar["command_search"])


class ActivityLogAdminTests(TestCase):
    def test_activity_log_is_registered_as_admin_table(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="admin-secret-123",
        )
        model_admin = admin.site._registry[LogEntry]

        self.assertIn(LogEntry, admin.site._registry)
        self.assertEqual(model_admin.list_display[0], "action_time")
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None, user))
        self.assertFalse(model_admin.has_delete_permission(None, user))

    def test_activity_log_admin_table_loads(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="admin-secret-123",
        )
        self.client.force_login(user)

        response = self.client.get("/admin/admin/logentry/")

        self.assertEqual(response.status_code, 200)


class AdminDashboardSearchTests(TestCase):
    def test_dashboard_contains_main_search_launcher(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="admin-secret-123",
        )
        self.client.force_login(user)

        response = self.client.get("/admin/")

        self.assertContains(response, "Search students, documents, users, and activity logs")
        self.assertContains(response, "opencommand")

    def test_dashboard_contains_registrar_overview_sections(self):
        User = get_user_model()
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="admin-secret-123",
        )
        self.client.force_login(user)

        response = self.client.get("/admin/")

        self.assertContains(response, "Overall Dashboard")
        self.assertContains(response, "Registrar archive summary")
        self.assertContains(response, "Student Status")
        self.assertContains(response, "Document Types")
        self.assertContains(response, "Recent Documents")
        self.assertContains(response, "Recent Students")
        self.assertContains(response, "Add student")
        self.assertContains(response, "Upload document")


class AdminPasswordResetTests(TestCase):
    def test_login_shows_forgot_password_link(self):
        response = self.client.get("/admin/login/?next=/admin/")

        self.assertContains(response, reverse("admin_password_reset"))
        self.assertContains(response, "Forgotten your password")

    def test_password_reset_page_loads(self):
        response = self.client.get(reverse("admin_password_reset"))

        self.assertEqual(response.status_code, 200)
