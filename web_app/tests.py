from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from main_CRM.settings import (
    _deployment_security_configuration,
    _security_configuration,
)


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
                    "DJANGO_SECRET_KEY": "this-is-a-long-test-secret-key-used-only-for-tests-0123456789",
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
