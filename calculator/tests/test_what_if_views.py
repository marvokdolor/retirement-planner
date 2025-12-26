"""
Tests for what-if comparison views and HTMX endpoints.

TDD approach: Write these tests FIRST, then implement the views to make them pass.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from calculator.models import Scenario
import json


class WhatIfComparisonViewTests(TestCase):
    """Test the what-if comparison view that loads a base scenario."""

    def setUp(self):
        """Create test user and scenario."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create a base scenario with all phases
        self.scenario_data = {
            'phase1': {
                'current_age': 30,
                'retirement_start_age': 65,
                'current_savings': 50000,
                'monthly_contribution': 1000,
                'expected_return': 7.0,
                'inflation_rate': 3.0,
            },
            'phase2': {
                'starting_portfolio': 500000,
                'phase_start_age': 65,
                'phase_end_age': 70,
                'monthly_income': 3000,
                'annual_expenses': 40000,
                'expected_return': 6.0,
                'inflation_rate': 3.0,
            },
            'phase3': {
                'starting_portfolio': 600000,
                'active_retirement_start_age': 70,
                'active_retirement_end_age': 85,
                'annual_basic_expenses': 50000,
                'annual_healthcare_costs': 10000,
                'expected_return': 5.0,
                'inflation_rate': 3.0,
            },
            'phase4': {
                'starting_portfolio': 400000,
                'late_retirement_start_age': 85,
                'life_expectancy': 95,
                'annual_basic_expenses': 40000,
                'annual_healthcare_costs': 15000,
                'desired_legacy': 100000,
                'expected_return': 4.0,
                'inflation_rate': 3.0,
            }
        }

        self.scenario = Scenario.objects.create(
            user=self.user,
            name="Test Retirement Plan",
            data=self.scenario_data
        )

    def test_what_if_view_requires_login(self):
        """Test that what-if comparison requires authentication."""
        url = reverse('calculator:what_if_comparison', args=[self.scenario.id])
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_what_if_view_loads_base_scenario(self):
        """Test that what-if view loads the base scenario correctly."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:what_if_comparison', args=[self.scenario.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calculator/what_if_comparison.html')

        # Check that scenario is in context
        self.assertEqual(response.context['base_scenario'].id, self.scenario.id)
        self.assertEqual(response.context['base_scenario'].name, "Test Retirement Plan")

    def test_what_if_view_denies_access_to_other_users_scenarios(self):
        """Test that users can't access other users' scenarios."""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )

        # Login as other user
        self.client.login(username='otheruser', password='otherpass123')
        url = reverse('calculator:what_if_comparison', args=[self.scenario.id])
        response = self.client.get(url)

        # Should return 404 (scenario doesn't exist for this user)
        self.assertEqual(response.status_code, 404)

    def test_what_if_view_404_for_nonexistent_scenario(self):
        """Test that what-if view returns 404 for non-existent scenario."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:what_if_comparison', args=[99999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


class WhatIfCalculateHTMXTests(TestCase):
    """Test the HTMX endpoint for live what-if calculations."""

    def setUp(self):
        """Create test user and scenario."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create base scenario
        self.scenario_data = {
            'phase1': {
                'current_age': 30,
                'retirement_start_age': 65,
                'current_savings': 50000,
                'monthly_contribution': 1000,
                'expected_return': 7.0,
                'inflation_rate': 3.0,
            }
        }

        self.scenario = Scenario.objects.create(
            user=self.user,
            name="Test Plan",
            data=self.scenario_data
        )

    def test_what_if_calculate_requires_login(self):
        """Test that what-if calculation requires authentication."""
        url = reverse('calculator:what_if_calculate')
        response = self.client.post(url, {
            'base_scenario_id': self.scenario.id,
            'current_age': 30,
            'retirement_start_age': 67,  # Changed from 65
        })

        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_what_if_calculate_with_adjusted_retirement_age(self):
        """Test calculating what-if with adjusted retirement age."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:what_if_calculate')

        # Adjust retirement age from 65 to 67
        response = self.client.post(url, {
            'base_scenario_id': self.scenario.id,
            'phase': 'phase1',
            'current_age': 30,
            'retirement_start_age': 67,  # +2 years
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'expected_return': 7.0,
            'inflation_rate': 3.0,
        }, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)

        # Response should contain calculated results
        content = response.content.decode('utf-8')
        self.assertIn('future_value', content.lower())

    def test_what_if_calculate_with_increased_contribution(self):
        """Test calculating what-if with increased monthly contribution."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:what_if_calculate')

        # Increase monthly contribution from $1,000 to $1,500
        response = self.client.post(url, {
            'base_scenario_id': self.scenario.id,
            'phase': 'phase1',
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1500,  # +$500
            'expected_return': 7.0,
            'inflation_rate': 3.0,
        }, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)

    def test_what_if_calculate_shows_delta_from_base(self):
        """Test that what-if results include delta comparison to base."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:what_if_calculate')

        response = self.client.post(url, {
            'base_scenario_id': self.scenario.id,
            'phase': 'phase1',
            'current_age': 30,
            'retirement_start_age': 67,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'expected_return': 7.0,
            'inflation_rate': 3.0,
        }, HTTP_HX_REQUEST='true')

        content = response.content.decode('utf-8')

        # Should show delta/difference
        self.assertIn('delta', content.lower())

    def test_what_if_calculate_handles_invalid_data(self):
        """Test that what-if calculation handles invalid input gracefully."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:what_if_calculate')

        # Send invalid data (retirement age before current age)
        response = self.client.post(url, {
            'base_scenario_id': self.scenario.id,
            'phase': 'phase1',
            'current_age': 30,
            'retirement_start_age': 25,  # Invalid: before current age
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'expected_return': 7.0,
            'inflation_rate': 3.0,
        }, HTTP_HX_REQUEST='true')

        # Should return error message
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('error', content.lower())


class WhatIfComparisonIntegrationTests(TestCase):
    """Integration tests for complete what-if workflow."""

    def setUp(self):
        """Create test user and scenario."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.scenario = Scenario.objects.create(
            user=self.user,
            name="Retirement Plan",
            data={
                'phase1': {
                    'current_age': 30,
                    'retirement_start_age': 65,
                    'current_savings': 100000,
                    'monthly_contribution': 2000,
                    'expected_return': 7.0,
                    'inflation_rate': 3.0,
                }
            }
        )

    def test_complete_what_if_workflow(self):
        """Test complete workflow: load scenario → adjust → calculate → compare."""
        self.client.login(username='testuser', password='testpass123')

        # Step 1: Load what-if comparison page
        view_url = reverse('calculator:what_if_comparison', args=[self.scenario.id])
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 200)

        # Step 2: Make what-if calculation (retire 3 years earlier)
        calc_url = reverse('calculator:what_if_calculate')
        response = self.client.post(calc_url, {
            'base_scenario_id': self.scenario.id,
            'phase': 'phase1',
            'current_age': 30,
            'retirement_start_age': 62,  # Changed from 65 to 62
            'current_savings': 100000,
            'monthly_contribution': 2000,
            'expected_return': 7.0,
            'inflation_rate': 3.0,
        }, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)

        # Should show results with comparison
        content = response.content.decode('utf-8')
        self.assertIn('62', content)  # New retirement age
