"""
Tests for phase_calculator.py calculation logic
"""
from decimal import Decimal
from django.test import TestCase
from calculator.phase_calculator import calculate_late_retirement_phase


class LateRetirementCalculationTests(TestCase):
    """Test Late Retirement (Phase 4) calculation logic"""

    def test_portfolio_insufficient_when_depleted_before_legacy_goal(self):
        """
        Test that portfolio_sufficient is False when portfolio depletes,
        even if desired_legacy is $0.

        This is the bug we found: spending more than you have should show
        "Legacy Goal Not Met", not "Legacy Goal Achieved".
        """
        # Scenario: Start with $100,000, but spend way more than portfolio can handle
        data = {
            'starting_portfolio': 100000,
            'late_retirement_start_age': 85,
            'life_expectancy': 95,  # 10 years
            'annual_basic_expenses': 50000,  # $50k/year for 10 years = $500k needed
            'annual_healthcare_costs': 20000,  # $20k/year for 10 years = $200k needed
            # Total needed: $700k, but only have $100k → will deplete
            'long_term_care_annual': 0,
            'ltc_insurance_coverage': 0,
            'social_security_annual': 0,
            'expected_return': 5.0,  # 5% return won't save us
            'inflation_rate': 3.0,
            'desired_legacy': 50000,  # Want to leave $50k, but won't be able to
        }

        results = calculate_late_retirement_phase(data)

        # EXPECTED BEHAVIOR:
        # Portfolio will deplete before age 95
        # ending_portfolio should be $0 (or close to it)
        # portfolio_sufficient should be FALSE (can't meet $50k legacy goal)

        self.assertEqual(results.ending_portfolio, Decimal('0'))
        self.assertFalse(
            results.portfolio_sufficient,
            "portfolio_sufficient should be False when portfolio depletes before meeting legacy goal"
        )

    def test_portfolio_sufficient_when_legacy_goal_met(self):
        """
        Test that portfolio_sufficient is True when ending portfolio
        meets or exceeds the desired legacy amount.
        """
        data = {
            'starting_portfolio': 500000,  # Start with $500k
            'late_retirement_start_age': 85,
            'life_expectancy': 95,  # 10 years
            'annual_basic_expenses': 20000,  # Modest expenses
            'annual_healthcare_costs': 10000,
            'long_term_care_annual': 0,
            'ltc_insurance_coverage': 0,
            'social_security_annual': 0,
            'expected_return': 6.0,  # 6% return
            'inflation_rate': 2.0,
            'desired_legacy': 100000,  # Want to leave $100k
        }

        results = calculate_late_retirement_phase(data)

        # EXPECTED BEHAVIOR:
        # Portfolio should survive with money left over
        # ending_portfolio should be > $0
        # portfolio_sufficient should be TRUE

        self.assertGreater(results.ending_portfolio, Decimal('0'))
        self.assertTrue(
            results.portfolio_sufficient,
            "portfolio_sufficient should be True when legacy goal is met"
        )
        self.assertGreaterEqual(
            results.ending_portfolio,
            Decimal(str(data['desired_legacy'])),
            "Ending portfolio should meet or exceed desired legacy"
        )

    def test_portfolio_depletes_with_zero_legacy_goal(self):
        """
        Edge case: Portfolio depletes, but desired_legacy is $0.
        Should still show portfolio_sufficient = False because money ran out.
        """
        data = {
            'starting_portfolio': 50000,
            'late_retirement_start_age': 85,
            'life_expectancy': 95,  # 10 years
            'annual_basic_expenses': 30000,  # Will deplete portfolio
            'annual_healthcare_costs': 20000,
            'long_term_care_annual': 0,
            'ltc_insurance_coverage': 0,
            'social_security_annual': 0,
            'expected_return': 4.0,
            'inflation_rate': 3.0,
            'desired_legacy': 0,  # Don't care about legacy, just want money to last
        }

        results = calculate_late_retirement_phase(data)

        # EXPECTED BEHAVIOR:
        # Portfolio depletes to $0
        # Even though desired_legacy is $0, portfolio_sufficient should be False
        # because we ran out of money before the end of the phase

        self.assertEqual(results.ending_portfolio, Decimal('0'))
        self.assertFalse(
            results.portfolio_sufficient,
            "portfolio_sufficient should be False when portfolio depletes, even with $0 legacy goal"
        )
