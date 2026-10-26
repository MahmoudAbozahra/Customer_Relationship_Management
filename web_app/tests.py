from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import Client, SimpleTestCase, TestCase, TransactionTestCase
from django.urls import reverse

from main_CRM.settings import (
    _deployment_security_configuration,
    _security_configuration,
)
from web_app.models import Category, Clint


class SecurityConfigurationTests(SimpleTestCase):
    def test_development_defaults_are_local_and_do_not_require_a_secret(self):
        secret_key, debug, allowed_hosts = _security_configuration({})

        self.assertTrue(debug)
        self.assertTrue(secret_key.startswith("django-insecure-"))
        self.assertIn("localhost", allowed_hosts)

    def test_production_requires_a_secret(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "DJANGO_SECRET_KEY"):
            _security_configuration({"DJANGO_DEBUG": "false"})

    def test_production_rejects_weak_secret(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "strong production secret"):
            _security_configuration(
                {
                    "DJANGO_DEBUG": "false",
                    "DJANGO_SECRET_KEY": "short",
                    "DJANGO_ALLOWED_HOSTS": "crm.example.com",
                }
            )

    def test_production_requires_allowed_hosts(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "DJANGO_ALLOWED_HOSTS"):
            _security_configuration(
                {
                    "DJANGO_DEBUG": "false",
                    "DJANGO_SECRET_KEY": (
                        "this-is-a-long-test-secret-key-used-only-for-tests-0123456789"
                    ),
                }
            )

    def test_production_configuration_uses_secure_cookies_and_https(self):
        configuration = _deployment_security_configuration({}, debug=False)

        self.assertEqual(configuration[:3], (True, True, True))
        self.assertEqual(configuration[3], 0)

    def test_hsts_must_not_be_negative(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "cannot be negative"):
            _deployment_security_configuration(
                {"DJANGO_SECURE_HSTS_SECONDS": "-1"}, debug=False
            )


class CRMAccessTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="General")
        self.clint = Clint.objects.create(
            first_name="Rania", last_name="Test", category=self.category
        )
        self.staff_user = User.objects.create_user(
            username="staff", password="Strong-pass-4819", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username="regular", password="Strong-pass-4819"
        )

    def test_anonymous_users_cannot_access_customer_views(self):
        paths = [
            reverse("dashboard"),
            reverse("add_clint"),
            reverse("view", args=[self.clint.pk]),
            reverse("edit", args=[self.clint.pk]),
            reverse("search"),
        ]

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertRedirects(response, f"{reverse('my_login')}?next={path}")

    def test_regular_users_cannot_access_customer_views(self):
        self.client.force_login(self.regular_user)
        paths = [
            reverse("dashboard"),
            reverse("add_clint"),
            reverse("view", args=[self.clint.pk]),
            reverse("edit", args=[self.clint.pk]),
            reverse("search"),
        ]

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertRedirects(response, f"{reverse('my_login')}?next={path}")

    def test_staff_users_can_view_dashboard_detail_and_search(self):
        self.client.force_login(self.staff_user)

        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("view", args=[self.clint.pk])).status_code, 200
        )
        self.assertEqual(
            self.client.get(reverse("search"), {"query": "Rania"}).status_code, 200
        )

    def test_invalid_registration_displays_errors_without_creating_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "regular",
                "password1": "Strong-pass-4819",
                "password2": "Strong-pass-4819",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(User.objects.filter(username="regular").count(), 1)

    def test_successful_registration_creates_non_staff_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "new-user",
                "password1": "Strong-pass-4819",
                "password2": "Strong-pass-4819",
            },
        )

        self.assertRedirects(response, reverse("my_login"))
        new_user = User.objects.get(username="new-user")
        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)

    def test_invalid_login_preserves_the_bound_form_errors(self):
        response = self.client.post(
            reverse("my_login"), {"username": "regular", "password": "wrong"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(response.context["form"]["username"].value(), "regular")

    def test_regular_user_login_does_not_redirect_to_customer_dashboard(self):
        response = self.client.post(
            reverse("my_login"),
            {"username": "regular", "password": "Strong-pass-4819"},
        )

        self.assertRedirects(response, reverse("Home"))

    def test_delete_and_logout_reject_get_requests(self):
        self.client.force_login(self.staff_user)

        self.assertEqual(
            self.client.get(reverse("delete", args=[self.clint.pk])).status_code, 405
        )
        self.assertEqual(self.client.get(reverse("my_logout")).status_code, 405)

    def test_post_logout_ends_the_session(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(reverse("my_logout"))

        self.assertRedirects(response, reverse("my_login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_staff_can_create_edit_and_delete_clients(self):
        self.client.force_login(self.staff_user)
        add_response = self.client.post(
            reverse("add_clint"),
            {"first_name": "Mona", "category": self.category.pk},
        )
        self.assertRedirects(add_response, reverse("dashboard"))
        new_clint = Clint.objects.get(first_name="Mona")

        edit_response = self.client.post(
            reverse("edit", args=[new_clint.pk]),
            {"first_name": "Mona Updated", "category": self.category.pk},
        )
        self.assertRedirects(edit_response, reverse("dashboard"))
        new_clint.refresh_from_db()
        self.assertEqual(new_clint.first_name, "Mona Updated")

        delete_response = self.client.post(reverse("delete", args=[new_clint.pk]))
        self.assertRedirects(delete_response, reverse("dashboard"))
        self.assertFalse(Clint.objects.filter(pk=new_clint.pk).exists())

    def test_invalid_client_creation_returns_dashboard_with_errors(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("add_clint"), {"first_name": "", "category": self.category.pk}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "web/dashboard.html")
        self.assertTrue(response.context["form"].errors)

    def test_delete_requires_a_valid_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff_user)

        response = csrf_client.post(reverse("delete", args=[self.clint.pk]))
        self.assertEqual(response.status_code, 403)

        detail_response = csrf_client.get(reverse("view", args=[self.clint.pk]))
        csrf_token = detail_response.cookies["csrftoken"].value
        response = csrf_client.post(
            reverse("delete", args=[self.clint.pk]),
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Clint.objects.filter(pk=self.clint.pk).exists())

    def test_category_with_clients_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.category.delete()

        self.assertTrue(Clint.objects.filter(pk=self.clint.pk).exists())

    def test_client_string_conversion_accepts_missing_last_name(self):
        clint = Clint.objects.create(first_name="Samir", category=self.category)

        self.assertEqual(str(clint), "Samir")

    def test_phone_field_preserves_leading_zeroes(self):
        clint = Clint.objects.create(
            first_name="Hana", phone="012345", category=self.category
        )

        self.assertEqual(Clint.objects.get(pk=clint.pk).phone, "012345")

    def test_client_lists_are_paginated_and_search_query_is_preserved(self):
        self.client.force_login(self.staff_user)
        Clint.objects.bulk_create(
            [
                Clint(first_name=f"Batch {index}", category=self.category)
                for index in range(26)
            ]
        )

        response = self.client.get(reverse("search"), {"query": "Batch"})

        self.assertEqual(response.context["results"].paginator.per_page, 25)
        self.assertEqual(response.context["results"].paginator.num_pages, 2)
        self.assertContains(response, "query=Batch&amp;page=2")

    def test_select_related_loads_category_with_one_query(self):
        with self.assertNumQueries(1):
            list(Clint.objects.select_related("category").all())


class ClientDataMigrationTests(TransactionTestCase):
    migrate_from = (("web_app", "0003_alter_clint_options_alter_clint_created_at"),)
    migrate_to = (("web_app", "0004_alter_clint_category_alter_clint_phone"),)

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        category_model = old_apps.get_model("web_app", "Category")
        clint_model = old_apps.get_model("web_app", "Clint")
        category = category_model.objects.create(name="Legacy")
        clint_model.objects.create(
            first_name="Existing", last_name=None, phone=12345, category=category
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps_after_migration = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_phone_values_survive_conversion_to_text(self):
        clint_model = self.apps_after_migration.get_model("web_app", "Clint")

        self.assertEqual(clint_model.objects.get(first_name="Existing").phone, "12345")
