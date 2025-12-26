"""
Tests for phase form validation.

These forms control data entry for all 4 retirement phases.
Tests cover field validation, cross-field validation, and edge cases.
"""

from django.test import TestCase
from calculator.phase_forms import (
    AccumulationPhaseForm,
    PhasedRetirementForm,
    ActiveRetirementForm,
    LateRetirementForm
)


class AccumulationPhaseFormTests(TestCase):
    """Test Phase 1 - Accumulation form validation."""

    def test_valid_accumulation_form(self):
        """Test form accepts valid accumulation data."""
        form = AccumulationPhaseForm(data={
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertTrue(form.is_valid())

    def test_retirement_age_greater_than_current_age(self):
        """Test form rejects retirement age <= current age."""
        form = AccumulationPhaseForm(data={
            'current_age': 65,
            'retirement_start_age': 60,  # Invalid: earlier than current age
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertFalse(form.is_valid())
        # Cross-field validation errors appear in form.errors['__all__']
        self.assertIn('__all__', form.errors)

    def test_retirement_age_equal_to_current_age(self):
        """Test form rejects retirement age equal to current age."""
        form = AccumulationPhaseForm(data={
            'current_age': 65,
            'retirement_start_age': 65,  # Invalid: equal to current age
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertFalse(form.is_valid())
        # Cross-field validation errors appear in form.errors['__all__']
        self.assertIn('__all__', form.errors)

    def test_negative_current_age(self):
        """Test form rejects negative current age."""
        form = AccumulationPhaseForm(data={
            'current_age': -5,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('current_age', form.errors)

    def test_negative_savings(self):
        """Test form rejects negative current savings."""
        form = AccumulationPhaseForm(data={
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': -10000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('current_savings', form.errors)

    def test_zero_values_accepted(self):
        """Test form accepts zero for optional fields."""
        form = AccumulationPhaseForm(data={
            'current_age': 25,
            'retirement_start_age': 65,
            'current_savings': 50000,  # Need at least one funding source
            'monthly_contribution': 0,  # Zero is valid
            'employer_match_rate': 0,  # Zero is valid
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 0,  # Zero is valid
        })

        self.assertTrue(form.is_valid())

    def test_employer_match_rate_percentage_range(self):
        """Test form validates employer match rate is within 0-100%."""
        # Valid: 100%
        form = AccumulationPhaseForm(data={
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 100,  # 100% - maximum allowed
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertTrue(form.is_valid())

    def test_negative_expected_return(self):
        """Test form rejects negative expected return."""
        form = AccumulationPhaseForm(data={
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': -5,  # Negative return
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('expected_return', form.errors)


class PhasedRetirementFormTests(TestCase):
    """Test Phase 2 - Phased Retirement form validation."""

    def test_valid_phased_retirement_form(self):
        """Test form accepts valid phased retirement data."""
        form = PhasedRetirementForm(data={
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

        self.assertTrue(form.is_valid())

    def test_full_retirement_age_greater_than_phase_start(self):
        """Test form rejects full retirement age <= phase start age."""
        form = PhasedRetirementForm(data={
            'starting_portfolio': 500000,
            'phase_start_age': 70,
            'full_retirement_age': 65,  # Invalid: earlier than phase start
            'annual_part_time_income': 30000,
            'annual_withdrawal': 20000,
            'annual_contribution': 5000,
            'stock_allocation': 60,
            'expected_return': 6,
            'return_volatility': 10,
            'inflation_rate': 3,
        })

        self.assertFalse(form.is_valid())
        # Cross-field validation errors appear in form.errors['__all__']
        self.assertIn('__all__', form.errors)

    def test_stock_allocation_within_range(self):
        """Test form validates stock allocation is 0-100%."""
        # Test 0%
        form_zero = PhasedRetirementForm(data={
            'starting_portfolio': 500000,
            'phase_start_age': 65,
            'full_retirement_age': 70,
            'annual_part_time_income': 30000,
            'annual_withdrawal': 20000,
            'annual_contribution': 5000,
            'stock_allocation': 0,
            'expected_return': 6,
            'return_volatility': 10,
            'inflation_rate': 3,
        })
        self.assertTrue(form_zero.is_valid())

        # Test 100%
        form_hundred = PhasedRetirementForm(data={
            'starting_portfolio': 500000,
            'phase_start_age': 65,
            'full_retirement_age': 70,
            'annual_part_time_income': 30000,
            'annual_withdrawal': 20000,
            'annual_contribution': 5000,
            'stock_allocation': 100,
            'expected_return': 6,
            'return_volatility': 10,
            'inflation_rate': 3,
        })
        self.assertTrue(form_hundred.is_valid())

    def test_stock_allocation_above_100_rejected(self):
        """Test form rejects stock allocation > 100%."""
        form = PhasedRetirementForm(data={
            'starting_portfolio': 500000,
            'phase_start_age': 65,
            'full_retirement_age': 70,
            'annual_part_time_income': 30000,
            'annual_withdrawal': 20000,
            'annual_contribution': 5000,
            'stock_allocation': 150,  # Invalid: > 100%
            'expected_return': 6,
            'return_volatility': 10,
            'inflation_rate': 3,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('stock_allocation', form.errors)

    def test_negative_portfolio_rejected(self):
        """Test form rejects negative starting portfolio."""
        form = PhasedRetirementForm(data={
            'starting_portfolio': -100000,
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

        self.assertFalse(form.is_valid())
        self.assertIn('starting_portfolio', form.errors)

    def test_zero_income_and_contributions_accepted(self):
        """Test form accepts zero for income and contributions."""
        form = PhasedRetirementForm(data={
            'starting_portfolio': 500000,
            'phase_start_age': 65,
            'full_retirement_age': 70,
            'annual_part_time_income': 0,  # No income - valid
            'annual_withdrawal': 20000,
            'annual_contribution': 0,  # No contributions - valid
            'stock_allocation': 60,
            'expected_return': 6,
            'return_volatility': 10,
            'inflation_rate': 3,
        })

        self.assertTrue(form.is_valid())


class ActiveRetirementFormTests(TestCase):
    """Test Phase 3 - Active Retirement form validation."""

    def test_valid_active_retirement_form(self):
        """Test form accepts valid active retirement data."""
        form = ActiveRetirementForm(data={
            'starting_portfolio': 800000,
            'active_retirement_start_age': 70,
            'active_retirement_end_age': 80,
            'annual_expenses': 50000,
            'annual_healthcare_costs': 10000,
            'expected_return': 5,
            'return_volatility': 8,
            'inflation_rate': 3,
        })

        self.assertTrue(form.is_valid())

    def test_end_age_greater_than_start_age(self):
        """Test form rejects end age <= start age."""
        form = ActiveRetirementForm(data={
            'starting_portfolio': 800000,
            'active_retirement_start_age': 80,
            'active_retirement_end_age': 75,  # Invalid: earlier than start
            'annual_expenses': 50000,
            'annual_healthcare_costs': 10000,
            'expected_return': 5,
            'return_volatility': 8,
            'inflation_rate': 3,
        })

        self.assertFalse(form.is_valid())
        # Cross-field validation errors appear in form.errors['__all__']
        self.assertIn('__all__', form.errors)

    def test_high_expenses_accepted(self):
        """Test form accepts high expenses that may deplete portfolio."""
        form = ActiveRetirementForm(data={
            'starting_portfolio': 100000,
            'active_retirement_start_age': 70,
            'active_retirement_end_age': 80,
            'annual_expenses': 80000,  # Very high
            'annual_healthcare_costs': 20000,  # Very high
            'expected_return': 5,
            'return_volatility': 8,
            'inflation_rate': 3,
        })

        # Form should validate even with unsustainable spending
        # (calculator will show depletion)
        self.assertTrue(form.is_valid())

    def test_negative_expenses_rejected(self):
        """Test form rejects negative expenses."""
        form = ActiveRetirementForm(data={
            'starting_portfolio': 800000,
            'active_retirement_start_age': 70,
            'active_retirement_end_age': 80,
            'annual_expenses': -10000,  # Negative
            'annual_healthcare_costs': 10000,
            'expected_return': 5,
            'return_volatility': 8,
            'inflation_rate': 3,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('annual_expenses', form.errors)

    def test_zero_healthcare_costs_accepted(self):
        """Test form accepts zero healthcare costs."""
        form = ActiveRetirementForm(data={
            'starting_portfolio': 800000,
            'active_retirement_start_age': 70,
            'active_retirement_end_age': 80,
            'annual_expenses': 50000,
            'annual_healthcare_costs': 0,  # Zero - valid
            'expected_return': 5,
            'return_volatility': 8,
            'inflation_rate': 3,
        })

        self.assertTrue(form.is_valid())


class LateRetirementFormTests(TestCase):
    """Test Phase 4 - Late Retirement form validation."""

    def test_valid_late_retirement_form(self):
        """Test form accepts valid late retirement data."""
        form = LateRetirementForm(data={
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

        self.assertTrue(form.is_valid())

    def test_life_expectancy_greater_than_start_age(self):
        """Test form rejects life expectancy <= start age."""
        form = LateRetirementForm(data={
            'starting_portfolio': 600000,
            'late_retirement_start_age': 85,
            'life_expectancy': 80,  # Invalid: earlier than start age
            'annual_basic_expenses': 30000,
            'annual_healthcare_costs': 15000,
            'long_term_care_annual': 50000,
            'expected_return': 4,
            'return_volatility': 5,
            'inflation_rate': 3,
        })

        self.assertFalse(form.is_valid())
        # Cross-field validation errors appear in form.errors['__all__']
        self.assertIn('__all__', form.errors)

    def test_high_long_term_care_costs_accepted(self):
        """Test form accepts very high long-term care costs."""
        form = LateRetirementForm(data={
            'starting_portfolio': 600000,
            'late_retirement_start_age': 80,
            'life_expectancy': 90,
            'annual_basic_expenses': 30000,
            'annual_healthcare_costs': 15000,
            'long_term_care_annual': 150000,  # Very expensive
            'expected_return': 4,
            'return_volatility': 5,
            'inflation_rate': 3,
        })

        self.assertTrue(form.is_valid())

    def test_zero_long_term_care_accepted(self):
        """Test form accepts zero long-term care costs."""
        form = LateRetirementForm(data={
            'starting_portfolio': 600000,
            'late_retirement_start_age': 80,
            'life_expectancy': 90,
            'annual_basic_expenses': 30000,
            'annual_healthcare_costs': 15000,
            'long_term_care_annual': 0,  # No LTC - valid
            'expected_return': 4,
            'return_volatility': 5,
            'inflation_rate': 3,
        })

        self.assertTrue(form.is_valid())

    def test_negative_healthcare_costs_rejected(self):
        """Test form rejects negative healthcare costs."""
        form = LateRetirementForm(data={
            'starting_portfolio': 600000,
            'late_retirement_start_age': 80,
            'life_expectancy': 90,
            'annual_basic_expenses': 30000,
            'annual_healthcare_costs': -5000,  # Negative
            'long_term_care_annual': 50000,
            'expected_return': 4,
            'return_volatility': 5,
            'inflation_rate': 3,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('annual_healthcare_costs', form.errors)

    def test_very_old_life_expectancy_accepted(self):
        """Test form accepts very old life expectancy (e.g., 120)."""
        form = LateRetirementForm(data={
            'starting_portfolio': 600000,
            'late_retirement_start_age': 80,
            'life_expectancy': 120,  # Very optimistic
            'annual_basic_expenses': 30000,
            'annual_healthcare_costs': 15000,
            'long_term_care_annual': 50000,
            'expected_return': 4,
            'return_volatility': 5,
            'inflation_rate': 3,
        })

        self.assertTrue(form.is_valid())


class CrossPhaseValidationTests(TestCase):
    """Test validation logic that spans multiple phases."""

    def test_phase2_start_matches_phase1_retirement_age(self):
        """Test Phase 2 start age should match Phase 1 retirement age."""
        # This is more of a UX test - forms don't enforce this,
        # but the calculator template should auto-populate

        accumulation_form = AccumulationPhaseForm(data={
            'current_age': 30,
            'retirement_start_age': 65,  # Phase 1 ends at 65
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        phased_form = PhasedRetirementForm(data={
            'starting_portfolio': 500000,
            'phase_start_age': 65,  # Should match Phase 1 retirement age
            'full_retirement_age': 70,
            'annual_part_time_income': 30000,
            'annual_withdrawal': 20000,
            'annual_contribution': 5000,
            'stock_allocation': 60,
            'expected_return': 6,
            'return_volatility': 10,
            'inflation_rate': 3,
        })

        self.assertTrue(accumulation_form.is_valid())
        self.assertTrue(phased_form.is_valid())
        # Note: Actual cascade validation happens in the view/template

    def test_sequential_age_ranges(self):
        """Test that age ranges make sense across phases."""
        # Phase 1: 30 -> 65
        # Phase 2: 65 -> 70
        # Phase 3: 70 -> 80
        # Phase 4: 80 -> 90

        phase1 = AccumulationPhaseForm(data={
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        phase2 = PhasedRetirementForm(data={
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

        phase3 = ActiveRetirementForm(data={
            'starting_portfolio': 800000,
            'active_retirement_start_age': 70,
            'active_retirement_end_age': 80,
            'annual_expenses': 50000,
            'annual_healthcare_costs': 10000,
            'expected_return': 5,
            'return_volatility': 8,
            'inflation_rate': 3,
        })

        phase4 = LateRetirementForm(data={
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

        # All forms should be valid with sequential ages
        self.assertTrue(phase1.is_valid())
        self.assertTrue(phase2.is_valid())
        self.assertTrue(phase3.is_valid())
        self.assertTrue(phase4.is_valid())
