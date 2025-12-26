from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class ProfileViewTests(TestCase):
    """Test suite for user profile edit functionality."""

    def setUp(self):
        """Create test user and client."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile_url = reverse('calculator:profile')

    # Authentication Tests
    def test_profile_requires_login(self):
        """Unauthenticated users redirected to login."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_profile_loads_for_authenticated_user(self):
        """Authenticated users can access profile page."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calculator/profile.html')

    # Form Display Tests
    def test_profile_displays_username_readonly(self):
        """Username shown but not editable."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)
        self.assertContains(response, 'testuser')
        # Verify no username input field in forms
        self.assertNotContains(response, 'name="username"')

    def test_profile_displays_current_email(self):
        """Email field pre-populated with current value."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.profile_url)
        self.assertContains(response, 'test@example.com')

    # Email Update Tests
    def test_update_email_success(self):
        """Valid email update succeeds."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.profile_url, {
            'action': 'update_profile',
            'email': 'newemail@example.com'
        }, follow=True)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertContains(response, 'Profile updated successfully')

    def test_update_email_to_blank(self):
        """Can clear email (it's optional)."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.profile_url, {
            'action': 'update_profile',
            'email': ''
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, '')

    def test_update_email_duplicate_validation(self):
        """Cannot use another user's email."""
        User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='pass123'
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.profile_url, {
            'action': 'update_profile',
            'email': 'other@example.com'
        })
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, 'other@example.com')
        self.assertContains(response, 'already in use')

    # Password Change Tests
    def test_change_password_success(self):
        """Valid password change succeeds."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.profile_url, {
            'action': 'change_password',
            'old_password': 'testpass123',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        })
        # Verify user can login with new password
        self.client.logout()
        login_success = self.client.login(username='testuser', password='newpass456')
        self.assertTrue(login_success)

    def test_change_password_wrong_old_password(self):
        """Wrong current password rejected."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.profile_url, {
            'action': 'change_password',
            'old_password': 'wrongpass',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        })
        # Verify old password still works
        self.client.logout()
        login_success = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_success)

    def test_change_password_mismatch(self):
        """Mismatched new passwords rejected."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.profile_url, {
            'action': 'change_password',
            'old_password': 'testpass123',
            'new_password1': 'newpass456',
            'new_password2': 'different789'
        })
        # Verify old password still works (password wasn't changed)
        self.client.logout()
        login_success = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_success)

    def test_password_change_keeps_user_logged_in(self):
        """User remains authenticated after password change."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.profile_url, {
            'action': 'change_password',
            'old_password': 'testpass123',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456'
        }, follow=True)
        # Verify still logged in
        self.assertTrue(response.context['user'].is_authenticated)
