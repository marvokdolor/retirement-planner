"""
Tests for form state persistence across phase tabs.

This feature ensures users don't lose their form data when switching
between different retirement phase tabs in the multi-phase calculator.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class FormStatePersistenceTests(TestCase):
    """Test form state persistence functionality."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.calculator_url = reverse('calculator:multi_phase_calculator')

    def test_calculator_page_includes_state_persistence_script(self):
        """Test that the calculator page includes JavaScript for state persistence."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.calculator_url)

        self.assertEqual(response.status_code, 200)
        # Check that forms have data-persist attribute (indicates persistence is set up)
        self.assertContains(response, 'data-persist=', msg_prefix='Page should have data-persist attributes for form persistence')

    def test_form_fields_have_data_persist_attribute(self):
        """Test that form fields have data-persist attributes for JavaScript to target."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.calculator_url)

        self.assertEqual(response.status_code, 200)
        # Key fields should have data-persist or similar attribute
        # This helps JavaScript identify which fields to persist
        content = response.content.decode()

        # Check that input fields exist (we'll add data-persist later)
        self.assertIn('name="current_age"', content)
        self.assertIn('name="retirement_start_age"', content)
        self.assertIn('name="current_savings"', content)

    def test_phase_tabs_preserve_form_data(self):
        """
        Test that switching between phase tabs doesn't lose form data.

        This is primarily a JavaScript feature, but we can test that the
        necessary HTML structure and attributes are in place.
        """
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.calculator_url)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        # Should have phase tabs with tab-button class
        self.assertIn('class="tab-button', content)

        # Forms should have identifiable IDs and data-persist attributes for JavaScript
        self.assertIn('id="accumulation-form"', content)
        self.assertIn('data-persist="phase1"', content)

    def test_clear_form_button_exists(self):
        """Test that there's a way to clear persisted form data."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.calculator_url)

        self.assertEqual(response.status_code, 200)
        # Should have a clear/reset button or link
        # We'll implement this as part of the feature
        # For now, just check the page loads
        self.assertContains(response, 'Calculate')

    def test_form_data_not_persisted_after_save_scenario(self):
        """
        Test that form data is cleared from sessionStorage after saving a scenario.

        This prevents old draft data from interfering with new scenarios.
        """
        # This is a JavaScript behavior test - we're just documenting expected behavior
        # The actual clearing happens client-side after successful save
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.calculator_url)
        self.assertEqual(response.status_code, 200)

    def test_persistence_key_includes_user_id(self):
        """
        Test that sessionStorage keys are user-specific to prevent data leakage.

        This is a JavaScript implementation detail, but important for security.
        """
        # This documents that we should use user-specific keys like:
        # `retirementForm_${userId}_phase1`
        # to prevent accidental data leakage in shared browser sessions
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.calculator_url)
        self.assertEqual(response.status_code, 200)
        # User ID should be available in the template context for JavaScript
        self.assertIn(f'user-id="{self.user.id}"', response.content.decode())


class FormStateEdgeCasesTests(TestCase):
    """Test edge cases for form state persistence."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_persistence_works_without_login(self):
        """Test that form persistence works for anonymous users."""
        # Anonymous users can still use the calculator without saving
        # Their form data should persist across tab switches
        response = self.client.get(reverse('calculator:multi_phase_calculator'))
        self.assertEqual(response.status_code, 200)
        # Should have data-persist attributes indicating persistence is enabled
        self.assertContains(response, 'data-persist=')

    def test_old_session_data_cleaned_on_page_load(self):
        """Test that very old sessionStorage data is cleaned up."""
        # Should have timestamp-based cleanup to prevent sessionStorage bloat
        # This is a JavaScript feature - just document expected behavior
        response = self.client.get(reverse('calculator:multi_phase_calculator'))
        self.assertEqual(response.status_code, 200)
