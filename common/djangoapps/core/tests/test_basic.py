"""
Basic tests to verify test configuration.

This module contains basic tests to ensure that the test environment
is properly set up and that both Django test cases and pytest work correctly.
"""
import pytest
from django.test import TestCase, SimpleTestCase
from django.conf import settings


@pytest.mark.unit
class TestEnvironment(SimpleTestCase):
    """Test the basic test environment setup."""

    def test_django_settings_loaded(self):
        """Verify that Django settings are properly loaded."""
        self.assertIsNotNone(settings.BASE_DIR)
        self.assertTrue(hasattr(settings, 'INSTALLED_APPS'))
        self.assertTrue(hasattr(settings, 'DATABASES'))

    def test_debug_mode(self):
        """Verify that DEBUG mode is set correctly for tests."""
        self.assertTrue(settings.DEBUG)

    def test_installed_apps(self):
        """Verify that core apps are in INSTALLED_APPS."""
        self.assertIn('ems.djangoapps.core', settings.INSTALLED_APPS)
        self.assertIn('rest_framework', settings.INSTALLED_APPS)


@pytest.mark.unit
class TestBasicMath(TestCase):
    """Simple test case to verify that basic assertions work."""

    def test_addition(self):
        """Test that basic addition works."""
        self.assertEqual(1 + 1, 2)
        self.assertEqual(2 + 2, 4)

    def test_subtraction(self):
        """Test that basic subtraction works."""
        self.assertEqual(5 - 3, 2)
        self.assertEqual(10 - 5, 5)

    def test_multiplication(self):
        """Test that basic multiplication works."""
        self.assertEqual(2 * 3, 6)
        self.assertEqual(5 * 5, 25)


@pytest.mark.parametrize("a,b,expected", [
    (1, 1, 2),
    (2, 3, 5),
    (5, 5, 10),
    (-1, 1, 0),
])
def test_addition_parametrized(a, b, expected):
    """Test addition with multiple inputs using pytest parametrize."""
    assert a + b == expected


@pytest.mark.parametrize("a,b,expected", [
    (5, 2, 3),
    (10, 5, 5),
    (3, 3, 0),
    (0, 5, -5),
])
def test_subtraction_parametrized(a, b, expected):
    """Test subtraction with multiple inputs using pytest parametrize."""
    assert a - b == expected

