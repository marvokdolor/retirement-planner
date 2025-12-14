from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Scenario
from .calculator import calculate_retirement_savings
from .phase_calculator import calculate_accumulation_phase
from .admin import ScenarioAdmin


class ScenarioModelTests(TestCase):
    """Test the Scenario model."""

    def setUp(self):
        """Create a test user for scenario tests."""
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_create_scenario(self):
        """Test creating a scenario with valid data."""
        scenario = Scenario.objects.create(
            user=self.user,
            name="Test Scenario",
            data={"age": 30, "savings": 50000}
        )
        self.assertEqual(scenario.name, "Test Scenario")
        self.assertEqual(scenario.data["age"], 30)
        self.assertEqual(scenario.user, self.user)
        self.assertIsNotNone(scenario.created_at)
        self.assertIsNotNone(scenario.updated_at)

    def test_scenario_str_representation(self):
        """Test the string representation of a scenario."""
        scenario = Scenario.objects.create(
            user=self.user,
            name="My Retirement Plan",
            data={}
        )
        self.assertEqual(str(scenario), "My Retirement Plan")

    def test_scenarios_ordered_by_updated_at(self):
        """Test that scenarios are ordered by most recently updated."""
        scenario1 = Scenario.objects.create(user=self.user, name="First", data={})
        scenario2 = Scenario.objects.create(user=self.user, name="Second", data={})

        scenarios = Scenario.objects.all()
        self.assertEqual(scenarios[0], scenario2)  # Most recent first
        self.assertEqual(scenarios[1], scenario1)


class CalculatorFunctionTests(TestCase):
    """Test retirement calculation functions."""

    def test_basic_retirement_calculation(self):
        """Test basic retirement savings calculation."""
        result = calculate_retirement_savings(
            current_age=30,
            retirement_age=65,
            current_savings=Decimal('10000'),
            monthly_contribution=Decimal('500'),
            annual_return_rate=Decimal('7'),
            variance=Decimal('2')
        )

        self.assertIsNotNone(result)
        self.assertGreater(result.future_value, 0)
        self.assertGreater(result.total_contributions, 0)
        self.assertEqual(result.years_to_retirement, 35)

    def test_accumulation_phase_calculation(self):
        """Test Phase 1 accumulation calculation."""
        data = {
            'current_age': 30,
            'retirement_start_age': 60,
            'current_savings': '50000',
            'monthly_contribution': '1000',
            'employer_match_rate': '50',
            'expected_return': '7',
            'annual_salary_increase': '2'
        }
        result = calculate_accumulation_phase(data)

        self.assertIsNotNone(result)
        self.assertGreater(result.future_value, 0)
        self.assertGreater(result.total_personal_contributions, 0)
        self.assertEqual(result.years_to_retirement, 30)

    def test_calculation_with_zero_contributions(self):
        """Test calculation with only starting portfolio."""
        data = {
            'current_age': 30,
            'retirement_start_age': 50,
            'current_savings': '100000',
            'monthly_contribution': '0',
            'employer_match_rate': '0',
            'expected_return': '7',
        }
        result = calculate_accumulation_phase(data)

        self.assertGreater(result.future_value, Decimal('100000'))


class ScenarioViewTests(TestCase):
    """Test scenario CRUD views."""

    def setUp(self):
        """Set up test client and test data."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.scenario = Scenario.objects.create(
            user=self.user,
            name="Test Scenario",
            data={"starting_portfolio": "50000", "monthly_contribution": "1000"}
        )

    def test_scenario_list_view(self):
        """Test the scenario list view."""
        response = self.client.get(reverse('calculator:scenario_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Scenario")
        self.assertTemplateUsed(response, 'calculator/scenario_list.html')

    def test_scenario_create_view_get(self):
        """Test GET request to scenario create view."""
        response = self.client.get(reverse('calculator:scenario_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calculator/scenario_form.html')

    def test_scenario_create_view_post(self):
        """Test POST request to create a new scenario."""
        response = self.client.post(reverse('calculator:scenario_create'), {
            'name': 'New Test Scenario',
            'data': '{"age": 35, "savings": 75000}'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Scenario.objects.filter(name='New Test Scenario').exists())

    def test_scenario_update_view(self):
        """Test updating an existing scenario."""
        response = self.client.post(
            reverse('calculator:scenario_update', kwargs={'pk': self.scenario.pk}),
            {
                'name': 'Updated Scenario',
                'data': '{"age": 40}'
            }
        )
        self.scenario.refresh_from_db()
        self.assertEqual(self.scenario.name, 'Updated Scenario')

    def test_scenario_delete_view(self):
        """Test deleting a scenario."""
        response = self.client.post(
            reverse('calculator:scenario_delete', kwargs={'pk': self.scenario.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Scenario.objects.filter(pk=self.scenario.pk).exists())

    def test_load_scenario_view(self):
        """Test loading a scenario into the calculator."""
        response = self.client.get(
            reverse('calculator:load_scenario', kwargs={'scenario_id': self.scenario.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Scenario")
        self.assertContains(response, "Scenario Loaded")


class MultiPhaseCalculatorViewTests(TestCase):
    """Test multi-phase calculator views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_multi_phase_calculator_get(self):
        """Test GET request to multi-phase calculator."""
        response = self.client.get(reverse('calculator:multi_phase_calculator'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calculator/multi_phase_calculator.html')
        self.assertContains(response, 'Phase 1: Accumulation')
        self.assertContains(response, 'Save This Scenario')

    def test_multi_phase_calculator_with_scenario(self):
        """Test multi-phase calculator loads scenario data."""
        scenario = Scenario.objects.create(
            user=self.user,
            name="Loaded Plan",
            data={"starting_portfolio": "100000"}
        )
        response = self.client.get(
            reverse('calculator:load_scenario', kwargs={'scenario_id': scenario.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Loaded Plan")


class SaveScenarioTests(TestCase):
    """Test save scenario HTMX endpoint."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_save_scenario_with_valid_data(self):
        """Test saving a scenario via HTMX."""
        response = self.client.post(
            reverse('calculator:save_scenario'),
            {
                'name': 'My Conservative Plan',
                'starting_portfolio': '50000',
                'monthly_contribution': '500',
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Scenario.objects.filter(name='My Conservative Plan').exists())
        self.assertContains(response, 'saved successfully')

    def test_save_scenario_without_name(self):
        """Test that saving without a name returns error."""
        response = self.client.post(
            reverse('calculator:save_scenario'),
            {
                'starting_portfolio': '50000',
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name')


class ScenarioAdminTests(TestCase):
    """Test Django admin customizations for Scenario model."""

    def setUp(self):
        """Set up admin site and test user."""
        self.site = AdminSite()
        self.admin = ScenarioAdmin(Scenario, self.site)
        self.user = User.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client.login(username='testadmin', password='testpass123')

    def test_admin_list_display_fields(self):
        """Test that admin list view shows correct fields."""
        self.assertIn('name', self.admin.list_display)
        self.assertIn('created_at', self.admin.list_display)
        self.assertIn('updated_at', self.admin.list_display)

    def test_admin_search_fields(self):
        """Test that search is configured."""
        self.assertIn('name', self.admin.search_fields)

    def test_admin_has_list_filters(self):
        """Test that list filters are configured for date filtering."""
        self.assertIn('created_at', self.admin.list_filter)
        self.assertIn('updated_at', self.admin.list_filter)

    def test_duplicate_scenario_action_exists(self):
        """Test that duplicate action is registered."""
        actions = [action for action in self.admin.actions]
        self.assertIn('duplicate_scenarios', actions)

    def test_duplicate_scenario_action_functionality(self):
        """Test custom admin action to duplicate a scenario."""
        scenario = Scenario.objects.create(
            name="Original Plan",
            data={"savings": "50000", "age": 30}
        )

        # Simulate admin action with proper request mock
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage

        factory = RequestFactory()
        request = factory.post('/admin/calculator/scenario/')
        request.user = self.user

        # Add messages middleware support
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        queryset = Scenario.objects.filter(pk=scenario.pk)
        self.admin.duplicate_scenarios(request, queryset)

        # Check that duplicate was created
        self.assertEqual(Scenario.objects.count(), 2)
        duplicate = Scenario.objects.filter(name__startswith="Copy of Original Plan").first()
        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate.data, scenario.data)

    def test_admin_readonly_fields(self):
        """Test that timestamp fields are readonly."""
        self.assertIn('created_at', self.admin.readonly_fields)
        self.assertIn('updated_at', self.admin.readonly_fields)


class ScenarioComparisonTests(TestCase):
    """Test scenario comparison view."""

    def setUp(self):
        """Create test scenarios for comparison."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.scenario1 = Scenario.objects.create(
            user=self.user,
            name="Conservative Plan",
            data={
                "current_age": "30",
                "retirement_start_age": "65",
                "current_savings": "50000",
                "monthly_contribution": "500",
                "expected_return": "5"
            }
        )
        self.scenario2 = Scenario.objects.create(
            user=self.user,
            name="Aggressive Plan",
            data={
                "current_age": "30",
                "retirement_start_age": "65",
                "current_savings": "50000",
                "monthly_contribution": "1000",
                "expected_return": "8"
            }
        )

    def test_comparison_view_get(self):
        """Test GET request shows comparison form with dropdowns."""
        response = self.client.get(reverse('calculator:scenario_compare'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calculator/scenario_compare.html')
        self.assertContains(response, 'Conservative Plan')
        self.assertContains(response, 'Aggressive Plan')

    def test_comparison_view_post_valid(self):
        """Test POST with two scenarios shows comparison results."""
        response = self.client.post(
            reverse('calculator:scenario_compare'),
            {
                'scenario1': self.scenario1.pk,
                'scenario2': self.scenario2.pk
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Conservative Plan')
        self.assertContains(response, 'Aggressive Plan')
        # Should show comparison data (final balance, etc.)
        self.assertContains(response, 'Final Balance')

    def test_comparison_view_post_same_scenario(self):
        """Test selecting same scenario twice shows error."""
        response = self.client.post(
            reverse('calculator:scenario_compare'),
            {
                'scenario1': self.scenario1.pk,
                'scenario2': self.scenario1.pk
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'different scenarios')

    def test_comparison_highlights_better_performer(self):
        """Test that comparison highlights which scenario performs better."""
        response = self.client.post(
            reverse('calculator:scenario_compare'),
            {
                'scenario1': self.scenario1.pk,
                'scenario2': self.scenario2.pk
            }
        )
        # Should have some indicator of which is better
        # (We'll implement this with a 'better_scenario' context variable)
        self.assertIn('better_scenario', response.context)


class EmailScenarioTests(TestCase):
    """Test emailing scenario reports."""

    def setUp(self):
        """Set up test user and scenario."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.scenario = Scenario.objects.create(
            user=self.user,
            name="Test Retirement Plan",
            data={
                "current_age": "30",
                "retirement_start_age": "65",
                "current_savings": "50000",
                "monthly_contribution": "1000",
                "expected_return": "7"
            }
        )

    def test_email_scenario_report(self):
        """Test queuing scenario report email."""
        response = self.client.post(
            reverse('calculator:email_scenario', kwargs={'scenario_id': self.scenario.pk})
        )

        # Should return success message (queued, not sent immediately)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'queued')

    def test_email_scenario_requires_ownership(self):
        """Test that users can only email their own scenarios."""
        # Create another user and their scenario
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_scenario = Scenario.objects.create(
            user=other_user,
            name="Other's Plan",
            data={"current_age": "25"}
        )

        # Try to email other user's scenario
        response = self.client.post(
            reverse('calculator:email_scenario', kwargs={'scenario_id': other_scenario.pk})
        )

        # Should return 404 (not found, because of user filtering)
        self.assertEqual(response.status_code, 404)

    def test_email_scenario_requires_user_email(self):
        """Test that user must have an email address to send reports."""
        # Create user without email
        user_no_email = User.objects.create_user(
            username='noemail',
            password='testpass123'
        )
        # Explicitly set email to empty string
        user_no_email.email = ''
        user_no_email.save()

        self.client.login(username='noemail', password='testpass123')

        scenario = Scenario.objects.create(
            user=user_no_email,
            name="Test Plan",
            data={"current_age": "30"}
        )

        response = self.client.post(
            reverse('calculator:email_scenario', kwargs={'scenario_id': scenario.pk})
        )

        # Should show error message about missing email
        self.assertEqual(response.status_code, 200)
        self.assertIn('email address', response.content.decode().lower())


class RegistrationTests(TestCase):
    """Test user registration."""

    def test_registration_requires_email(self):
        """Test that registration form requires email address."""
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser',
                'password1': 'testpass123',
                'password2': 'testpass123',
                # No email provided
            }
        )

        # Should not create user without email
        self.assertFalse(User.objects.filter(username='newuser').exists())
        # Should show email field error
        self.assertIn('email', response.content.decode().lower())

    def test_registration_with_email_succeeds(self):
        """Test that registration with email creates user and sets email."""
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
            }
        )

        # Should create user
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # User should have email set
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')


class DjangoMessagesTests(TestCase):
    """Test Django messages framework integration."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_scenario_save_shows_success_message(self):
        """Test that saving a scenario shows a success message."""
        response = self.client.post(
            reverse('calculator:save_scenario'),
            {
                'name': 'Test Plan',
                'current_age': '30',
                'retirement_start_age': '65',
            }
        )

        # HTMX view returns HTML fragment with success message
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.content.decode().lower())
        self.assertIn('Test Plan', response.content.decode())

    def test_email_scenario_shows_success_message(self):
        """Test that emailing a scenario shows a success message."""
        scenario = Scenario.objects.create(
            user=self.user,
            name='Test Scenario',
            data={
                'current_age': '30',
                'retirement_start_age': '65',
                'current_savings': '50000',
                'monthly_contribution': '1000',
                'expected_return': '7',
                'employer_match_rate': '50'
            }
        )

        response = self.client.post(
            reverse('calculator:email_scenario', kwargs={'scenario_id': scenario.pk}),
            follow=True
        )

        # Check that response contains success indication
        self.assertIn('success', response.content.decode().lower())


class BackgroundEmailTests(TestCase):
    """Test background email sending with Django-Q."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_email_scenario_queues_background_task(self):
        """Test that emailing a scenario queues a background task."""
        from django_q.models import OrmQ

        scenario = Scenario.objects.create(
            user=self.user,
            name='Background Test',
            data={
                'current_age': '30',
                'retirement_start_age': '65',
                'current_savings': '50000',
                'monthly_contribution': '1000',
                'expected_return': '7',
                'employer_match_rate': '50'
            }
        )

        # Clear any existing queued tasks
        OrmQ.objects.all().delete()

        response = self.client.post(
            reverse('calculator:email_scenario', kwargs={'scenario_id': scenario.pk})
        )

        # Should return success immediately (not wait for email)
        self.assertEqual(response.status_code, 200)
        self.assertIn('queued', response.content.decode().lower())

        # Should have queued a task
        queued_tasks = OrmQ.objects.all()
        self.assertEqual(queued_tasks.count(), 1)
        self.assertEqual(queued_tasks.first().func(), 'calculator.tasks.send_scenario_email')
