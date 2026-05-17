from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class UserAccountAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="old-secret-123",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            username="other",
            password="other-secret-123",
        )
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="admin-secret-123",
        )

    def test_create_user_hashes_password_and_hides_it(self):
        response = self.client.post(
            reverse("account-list"),
            {
                "email": "new@example.com",
                "username": "newuser",
                "password": "new-secret-123",
                "first_name": "New",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)

        created = User.objects.get(email="new@example.com")
        self.assertTrue(created.check_password("new-secret-123"))
        self.assertNotEqual(created.password, "new-secret-123")

    def test_anonymous_user_cannot_read_accounts(self):
        response = self.client.get(reverse("account-list"))

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_admin_can_list_accounts(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(reverse("account-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 3)

    def test_admin_can_get_users_list_endpoint(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 3)
        self.assertNotIn("password", response.data[0])

    def test_regular_user_cannot_get_users_list_endpoint(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_retrieve_self(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("account-detail", args=[self.user.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertNotIn("password", response.data)

    def test_user_cannot_retrieve_another_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("account-detail", args=[self.other_user.pk]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_update_self_and_change_password(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            reverse("account-detail", args=[self.user.pk]),
            {"first_name": "Updated", "password": "updated-secret-123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("password", response.data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertTrue(self.user.check_password("updated-secret-123"))
        self.assertNotEqual(self.user.password, "updated-secret-123")

    def test_user_can_delete_self(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(reverse("account-detail", args=[self.user.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
