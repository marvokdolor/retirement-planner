"""
Tests for HTMX view endpoints.

These views are the primary user interface for the calculator app.
Tests cover all four phase calculations, scenario saving, and Monte Carlo simulations.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from calculator.models import Scenario
import json


class CalculateAccumulationTests(TestCase):
    """Test Phase 1 - Accumulation calculation endpoint."""

    def setUp(self):
        self.client = Client()

    def test_valid_accumulation_calculation(self):
        """Test accumulation phase with valid data returns results."""
        response = self.client.post('/calculator/calculate/accumulation/', {
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Future Value')
        # Should show dollar amounts in results
        self.assertContains(response, '$')

    def test_accumulation_with_zero_savings(self):
        """Test accumulation works with zero initial savings."""
        response = self.client.post('/calculator/calculate/accumulation/', {
            'current_age': 25,
            'retirement_start_age': 65,
            'current_savings': 0,
            'monthly_contribution': 500,
            'employer_match_rate': 0,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 0,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Future Value')

    def test_accumulation_invalid_age_range(self):
        """Test accumulation rejects retirement age <= current age."""
        response = self.client.post('/calculator/calculate/accumulation/', {
            'current_age': 65,
            'retirement_start_age': 60,  # Invalid: earlier than current age
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        # Should return form errors
        self.assertContains(response, 'error', status_code=200)

    def test_accumulation_invalid_method(self):
        """Test accumulation endpoint rejects GET requests."""
        response = self.client.get('/calculator/calculate/accumulation/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid request method')


class CalculatePhasedRetirementTests(TestCase):
    """Test Phase 2 - Phased Retirement calculation endpoint."""

    def setUp(self):
        self.client = Client()

    def test_valid_phased_retirement_calculation(self):
        """Test phased retirement with valid data returns results."""
        response = self.client.post('/calculator/calculate/phased-retirement/', {
            'starting_portfolio': 500000,
            'phase_start_age': 65,
            'full_retirement_age': 70,
            'annual_part_time_income': 30000,
            'annual_withdrawal': 20000,
            'annual_contribution': 5000,
            'stock_allocation': 60,
            'expected_return': 6,
            'return_volatility': 10,
            'inflation_rate': 3,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ending Portfolio')
        self.assertContains(response, '$')

    def test_phased_retirement_with_zero_income(self):
        """Test phased retirement works with no part-time income."""
        response = self.client.post('/calculator/calculate/phased-retirement/', {
            'starting_portfolio': 500000,
            'phase_start_age': 65,
            'full_retirement_age': 70,
            'annual_part_time_income': 0,
            'annual_withdrawal': 20000,
            'annual_contribution': 0,
            'stock_allocation': 60,
            'expected_return': 6,
            'return_volatility': 10,
            'inflation_rate': 3,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ending Portfolio')


class CalculateActiveRetirementTests(TestCase):
    """Test Phase 3 - Active Retirement calculation endpoint."""

    def setUp(self):
        self.client = Client()

    def test_valid_active_retirement_calculation(self):
        """Test active retirement with valid data returns results."""
        response = self.client.post('/calculator/calculate/active-retirement/', {
            'starting_portfolio': 800000,
            'active_retirement_start_age': 70,
            'active_retirement_end_age': 80,
            'annual_expenses': 50000,
            'annual_healthcare_costs': 10000,
            'expected_return': 5,
            'return_volatility': 8,
            'inflation_rate': 3,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ending Portfolio')
        self.assertContains(response, '$')

    def test_active_retirement_high_expenses(self):
        """Test active retirement with high expenses that deplete portfolio."""
        response = self.client.post('/calculator/calculate/active-retirement/', {
            'starting_portfolio': 100000,
            'active_retirement_start_age': 70,
            'active_retirement_end_age': 80,
            'annual_expenses': 80000,  # High expenses
            'annual_healthcare_costs': 20000,
            'expected_return': 5,
            'return_volatility': 8,
            'inflation_rate': 3,
        })

        self.assertEqual(response.status_code, 200)
        # Should still return results, potentially showing portfolio depletion


class CalculateLateRetirementTests(TestCase):
    """Test Phase 4 - Late Retirement calculation endpoint."""

    def setUp(self):
        self.client = Client()

    def test_valid_late_retirement_calculation(self):
        """Test late retirement with valid data returns results."""
        response = self.client.post('/calculator/calculate/late-retirement/', {
            'starting_portfolio': 600000,
            'late_retirement_start_age': 80,
            'life_expectancy': 90,
            'annual_basic_expenses': 30000,
            'annual_healthcare_costs': 15000,
            'long_term_care_annual': 50000,
            'expected_return': 4,
            'return_volatility': 5,
            'inflation_rate': 3,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ending Portfolio')
        self.assertContains(response, '$')

    def test_late_retirement_with_long_term_care(self):
        """Test late retirement includes long-term care costs."""
        response = self.client.post('/calculator/calculate/late-retirement/', {
            'starting_portfolio': 600000,
            'late_retirement_start_age': 80,
            'life_expectancy': 90,
            'annual_basic_expenses': 30000,
            'annual_healthcare_costs': 15000,
            'long_term_care_annual': 100000,  # Expensive long-term care
            'expected_return': 4,
            'return_volatility': 5,
            'inflation_rate': 3,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ending Portfolio')


class SaveScenarioTests(TestCase):
    """Test scenario saving endpoint (requires authentication)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_save_scenario_requires_login(self):
        """Test saving scenario requires authentication."""
        response = self.client.post('/calculator/scenarios/save/', {
            'name': 'Test Scenario',
            'current_age': 30,
        })

        # Should redirect to login or return error
        self.assertIn(response.status_code, [302, 403])

    def test_save_scenario_creates_new(self):
        """Test saving scenario creates new scenario."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/calculator/scenarios/save/', {
            'name': 'My Retirement Plan',
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'saved successfully')

        # Verify scenario was created
        scenario = Scenario.objects.get(name='My Retirement Plan', user=self.user)
        self.assertEqual(scenario.data['current_age'], '30')

    def test_save_scenario_updates_existing(self):
        """Test saving scenario with same name updates existing."""
        self.client.login(username='testuser', password='testpass123')

        # Create initial scenario
        Scenario.objects.create(
            user=self.user,
            name='Test Plan',
            data={'current_age': '25'}
        )

        # Save with same name but different data
        response = self.client.post('/calculator/scenarios/save/', {
            'name': 'Test Plan',
            'current_age': 30,  # Different age
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'updated successfully')

        # Verify only one scenario exists with updated data
        scenarios = Scenario.objects.filter(name='Test Plan', user=self.user)
        self.assertEqual(scenarios.count(), 1)
        self.assertEqual(scenarios.first().data['current_age'], '30')

    def test_save_scenario_missing_name(self):
        """Test saving scenario without name returns error."""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/calculator/scenarios/save/', {
            'name': '',  # Empty name
            'current_age': 30,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'error')


class MonteCarloAccumulationTests(TestCase):
    """Test Monte Carlo simulation for accumulation phase."""

    def setUp(self):
        self.client = Client()

    def test_monte_carlo_accumulation_returns_chart(self):
        """Test Monte Carlo accumulation returns chart HTML."""
        response = self.client.post('/calculator/monte-carlo/accumulation/', {
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'annual_salary_increase': 2,
            'current_age': 30,
            'retirement_start_age': 65,
            'expected_return': 7,
            'return_volatility': 10,
        })

        self.assertEqual(response.status_code, 200)
        # Should contain Plotly chart
        self.assertContains(response, 'monte-carlo-chart-phase1')
        # Should contain percentile results
        self.assertContains(response, 'Median')
        self.assertContains(response, 'Optimistic')
        self.assertContains(response, 'Pessimistic')

    def test_monte_carlo_accumulation_invalid_data(self):
        """Test Monte Carlo accumulation handles invalid input."""
        response = self.client.post('/calculator/monte-carlo/accumulation/', {
            'current_savings': 'invalid',  # Invalid data type
            'monthly_contribution': 1000,
        })

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Invalid input', status_code=400)


class MonteCarloWithdrawalTests(TestCase):
    """Test Monte Carlo simulation for withdrawal phases."""

    def setUp(self):
        self.client = Client()

    def test_monte_carlo_withdrawal_phase2(self):
        """Test Monte Carlo withdrawal for Phase 2 (phased retirement)."""
        response = self.client.post('/calculator/monte-carlo/withdrawal/', {
            'starting_portfolio': 500000,
            'annual_withdrawal': 20000,
            'phase_start_age': 65,
            'full_retirement_age': 70,
            'expected_return': 6,
            'return_volatility': 10,
            'inflation_rate': 3,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'monte-carlo-chart')
        self.assertContains(response, 'Success Rate')

    def test_monte_carlo_withdrawal_phase3(self):
        """Test Monte Carlo withdrawal for Phase 3 (active retirement)."""
        response = self.client.post('/calculator/monte-carlo/withdrawal/', {
            'starting_portfolio': 800000,
            'annual_expenses': 50000,
            'annual_healthcare_costs': 10000,
            'active_retirement_start_age': 70,
            'active_retirement_end_age': 80,
            'expected_return': 5,
            'return_volatility': 8,
            'inflation_rate': 3,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'monte-carlo-chart')

    def test_monte_carlo_withdrawal_phase4(self):
        """Test Monte Carlo withdrawal for Phase 4 (late retirement)."""
        response = self.client.post('/calculator/monte-carlo/withdrawal/', {
            'starting_portfolio': 600000,
            'annual_basic_expenses': 30000,
            'annual_healthcare_costs': 15000,
            'long_term_care_annual': 50000,
            'late_retirement_start_age': 80,
            'life_expectancy': 90,
            'expected_return': 4,
            'return_volatility': 5,
            'inflation_rate': 3,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'monte-carlo-chart')
        self.assertContains(response, 'Success Rate')
