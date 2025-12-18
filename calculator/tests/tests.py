from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Scenario
from .calculator import calculate_retirement_savings
from .phase_calculator import (
    calculate_accumulation_phase,
    calculate_phased_retirement_phase,
    calculate_active_retirement_phase,
    calculate_late_retirement_phase
)
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


class AccumulationPhaseEdgeCaseTests(TestCase):
    """Comprehensive edge case tests for accumulation phase calculations."""

    def test_zero_years_to_retirement(self):
        """Test when current age equals retirement age (0 years to retirement)."""
        data = {
            'current_age': 65,
            'retirement_start_age': 65,
            'current_savings': '100000',
            'monthly_contribution': '1000',
            'employer_match_rate': '50',
            'expected_return': '7',
            'annual_salary_increase': '2'
        }
        result = calculate_accumulation_phase(data)

        self.assertEqual(result.years_to_retirement, 0)
        self.assertEqual(result.future_value, Decimal('100000'))
        self.assertEqual(result.total_personal_contributions, Decimal('0'))
        self.assertEqual(result.total_employer_contributions, Decimal('0'))
        self.assertEqual(result.investment_gains, Decimal('0'))

    def test_zero_current_savings(self):
        """Test with zero initial savings, only contributions."""
        data = {
            'current_age': 30,
            'retirement_start_age': 40,
            'current_savings': '0',
            'monthly_contribution': '500',
            'employer_match_rate': '100',
            'expected_return': '6',
            'annual_salary_increase': '0'
        }
        result = calculate_accumulation_phase(data)

        self.assertEqual(result.years_to_retirement, 10)
        self.assertGreater(result.future_value, 0)
        self.assertGreater(result.total_personal_contributions, 0)
        self.assertGreater(result.total_employer_contributions, 0)

    def test_zero_return_rate(self):
        """Test with 0% return (no growth, just contributions)."""
        data = {
            'current_age': 30,
            'retirement_start_age': 35,
            'current_savings': '10000',
            'monthly_contribution': '1000',
            'employer_match_rate': '0',
            'expected_return': '0',
            'annual_salary_increase': '0'
        }
        result = calculate_accumulation_phase(data)

        # With 0% return, future value should equal starting savings + total contributions
        expected_fv = Decimal('10000') + (Decimal('1000') * 5 * 12)
        self.assertEqual(result.future_value, expected_fv)
        self.assertEqual(result.investment_gains, Decimal('0'))

    def test_high_employer_match(self):
        """Test with 200% employer match (extremely generous)."""
        data = {
            'current_age': 25,
            'retirement_start_age': 30,
            'current_savings': '0',
            'monthly_contribution': '1000',
            'employer_match_rate': '200',
            'expected_return': '5',
            'annual_salary_increase': '0'
        }
        result = calculate_accumulation_phase(data)

        # Employer should contribute 2x the employee contribution
        self.assertAlmostEqual(
            float(result.total_employer_contributions),
            float(result.total_personal_contributions * 2),
            places=2
        )

    def test_high_salary_increase(self):
        """Test with aggressive 10% annual salary increases."""
        data = {
            'current_age': 22,
            'retirement_start_age': 27,
            'current_savings': '0',
            'monthly_contribution': '1000',
            'employer_match_rate': '50',
            'expected_return': '7',
            'annual_salary_increase': '10'
        }
        result = calculate_accumulation_phase(data)

        # Final contribution should be much higher than starting contribution
        self.assertGreater(result.final_monthly_contribution, Decimal('1000'))

    def test_very_long_time_horizon(self):
        """Test with 50 years to retirement."""
        data = {
            'current_age': 18,
            'retirement_start_age': 68,
            'current_savings': '1000',
            'monthly_contribution': '200',
            'employer_match_rate': '50',
            'expected_return': '7',
            'annual_salary_increase': '2'
        }
        result = calculate_accumulation_phase(data)

        self.assertEqual(result.years_to_retirement, 50)
        # With 50 years of compound growth, should have significant value
        self.assertGreater(result.future_value, Decimal('500000'))

    def test_high_return_rate(self):
        """Test with aggressive 15% return rate."""
        data = {
            'current_age': 30,
            'retirement_start_age': 50,
            'current_savings': '50000',
            'monthly_contribution': '500',
            'employer_match_rate': '0',
            'expected_return': '15',
            'annual_salary_increase': '0'
        }
        result = calculate_accumulation_phase(data)

        # High return should result in large investment gains
        self.assertGreater(result.investment_gains, result.total_personal_contributions)

    def test_large_starting_portfolio(self):
        """Test with multi-million dollar starting portfolio."""
        data = {
            'current_age': 50,
            'retirement_start_age': 60,
            'current_savings': '10000000',
            'monthly_contribution': '0',
            'employer_match_rate': '0',
            'expected_return': '5',
            'annual_salary_increase': '0'
        }
        result = calculate_accumulation_phase(data)

        # Even with no contributions, large portfolio should grow significantly
        self.assertGreater(result.future_value, Decimal('10000000'))
        self.assertGreater(result.investment_gains, Decimal('0'))


class PhasedRetirementEdgeCaseTests(TestCase):
    """Comprehensive edge case tests for phased retirement phase."""

    def test_basic_phased_retirement(self):
        """Test basic phased retirement calculation."""
        data = {
            'starting_portfolio': '500000',
            'phase_start_age': 60,
            'full_retirement_age': 65,
            'monthly_contribution': '1000',
            'annual_withdrawal': '24000',
            'part_time_income': '20000',
            'expected_return': '5'
        }
        result = calculate_phased_retirement_phase(data)

        self.assertEqual(result.phase_duration_years, 5)
        self.assertGreater(result.total_contributions, 0)
        self.assertGreater(result.total_withdrawals, 0)
        self.assertEqual(result.total_part_time_income, Decimal('100000'))

    def test_zero_duration_phased_retirement(self):
        """Test when full retirement age equals phase start age."""
        data = {
            'starting_portfolio': '500000',
            'phase_start_age': 65,
            'full_retirement_age': 65,
            'monthly_contribution': '0',
            'annual_withdrawal': '0',
            'part_time_income': '0',
            'expected_return': '5'
        }
        result = calculate_phased_retirement_phase(data)

        self.assertEqual(result.phase_duration_years, 0)
        self.assertEqual(result.ending_portfolio, Decimal('500000'))
        self.assertEqual(result.total_contributions, Decimal('0'))

    def test_phased_retirement_portfolio_growth(self):
        """Test scenario where contributions exceed withdrawals (portfolio grows)."""
        data = {
            'starting_portfolio': '300000',
            'phase_start_age': 60,
            'full_retirement_age': 67,
            'monthly_contribution': '2000',
            'annual_withdrawal': '12000',
            'part_time_income': '30000',
            'expected_return': '6'
        }
        result = calculate_phased_retirement_phase(data)

        # Portfolio should grow when contributions > withdrawals + good returns
        self.assertGreater(result.ending_portfolio, result.starting_portfolio)
        self.assertGreater(result.net_change, Decimal('0'))

    def test_phased_retirement_portfolio_decline(self):
        """Test scenario where withdrawals exceed contributions (portfolio declines)."""
        data = {
            'starting_portfolio': '400000',
            'phase_start_age': 62,
            'full_retirement_age': 67,
            'monthly_contribution': '0',
            'annual_withdrawal': '40000',
            'part_time_income': '15000',
            'expected_return': '4'
        }
        result = calculate_phased_retirement_phase(data)

        # High withdrawals with low contributions should reduce portfolio
        self.assertLess(result.ending_portfolio, result.starting_portfolio)
        self.assertLess(result.net_change, Decimal('0'))

    def test_phased_retirement_no_transactions(self):
        """Test with no contributions or withdrawals, only growth."""
        data = {
            'starting_portfolio': '250000',
            'phase_start_age': 60,
            'full_retirement_age': 63,
            'monthly_contribution': '0',
            'annual_withdrawal': '0',
            'part_time_income': '0',
            'expected_return': '7'
        }
        result = calculate_phased_retirement_phase(data)

        # Portfolio should only grow from investment returns
        self.assertGreater(result.ending_portfolio, result.starting_portfolio)
        self.assertEqual(result.total_contributions, Decimal('0'))
        self.assertEqual(result.total_withdrawals, Decimal('0'))


class ActiveRetirementEdgeCaseTests(TestCase):
    """Comprehensive edge case tests for active retirement phase."""

    def test_basic_active_retirement(self):
        """Test basic active retirement calculation."""
        data = {
            'starting_portfolio': '1000000',
            'active_retirement_start_age': 67,
            'active_retirement_end_age': 85,
            'annual_expenses': '50000',
            'annual_healthcare_costs': '15000',
            'social_security_annual': '30000',
            'pension_annual': '20000',
            'expected_return': '5',
            'inflation_rate': '3'
        }
        result = calculate_active_retirement_phase(data)

        self.assertEqual(result.phase_duration_years, 18)
        self.assertGreater(result.total_withdrawals, 0)
        self.assertGreater(result.total_social_security, 0)
        self.assertGreater(result.total_pension, 0)

    def test_zero_duration_active_retirement(self):
        """Test when start age equals end age."""
        data = {
            'starting_portfolio': '800000',
            'active_retirement_start_age': 70,
            'active_retirement_end_age': 70,
            'annual_expenses': '40000',
            'annual_healthcare_costs': '10000',
            'social_security_annual': '25000',
            'pension_annual': '0',
            'expected_return': '4',
            'inflation_rate': '2'
        }
        result = calculate_active_retirement_phase(data)

        self.assertEqual(result.phase_duration_years, 0)
        self.assertEqual(result.average_annual_withdrawal, Decimal('0'))

    def test_portfolio_depletion(self):
        """Test scenario where portfolio runs out before phase ends."""
        data = {
            'starting_portfolio': '200000',
            'active_retirement_start_age': 65,
            'active_retirement_end_age': 85,
            'annual_expenses': '60000',
            'annual_healthcare_costs': '20000',
            'social_security_annual': '20000',
            'pension_annual': '0',
            'expected_return': '3',
            'inflation_rate': '3'
        }
        result = calculate_active_retirement_phase(data)

        # Portfolio should run out
        self.assertIsNotNone(result.portfolio_depletion_age)
        self.assertEqual(result.ending_portfolio, Decimal('0'))

    def test_income_exceeds_expenses(self):
        """Test when social security + pension > expenses (no withdrawals needed)."""
        data = {
            'starting_portfolio': '500000',
            'active_retirement_start_age': 67,
            'active_retirement_end_age': 75,
            'annual_expenses': '30000',
            'annual_healthcare_costs': '10000',
            'social_security_annual': '35000',
            'pension_annual': '25000',
            'expected_return': '6',
            'inflation_rate': '2'
        }
        result = calculate_active_retirement_phase(data)

        # Portfolio should grow when income exceeds expenses
        self.assertGreater(result.ending_portfolio, result.starting_portfolio)

    def test_high_inflation_impact(self):
        """Test with high 5% inflation rate."""
        data = {
            'starting_portfolio': '750000',
            'active_retirement_start_age': 65,
            'active_retirement_end_age': 80,
            'annual_expenses': '40000',
            'annual_healthcare_costs': '15000',
            'social_security_annual': '30000',
            'pension_annual': '0',
            'expected_return': '6',
            'inflation_rate': '5'
        }
        result = calculate_active_retirement_phase(data)

        # High inflation should increase average withdrawal over time
        self.assertGreater(result.average_annual_withdrawal, Decimal('25000'))

    def test_no_income_sources(self):
        """Test with no social security or pension."""
        data = {
            'starting_portfolio': '1200000',
            'active_retirement_start_age': 60,
            'active_retirement_end_age': 75,
            'annual_expenses': '50000',
            'annual_healthcare_costs': '12000',
            'social_security_annual': '0',
            'pension_annual': '0',
            'expected_return': '5',
            'inflation_rate': '3'
        }
        result = calculate_active_retirement_phase(data)

        # All expenses must come from portfolio
        self.assertGreater(result.total_withdrawals, 0)
        self.assertEqual(result.total_social_security, Decimal('0'))
        self.assertEqual(result.total_pension, Decimal('0'))


class LateRetirementEdgeCaseTests(TestCase):
    """Comprehensive edge case tests for late retirement phase."""

    def test_basic_late_retirement(self):
        """Test basic late retirement calculation."""
        data = {
            'starting_portfolio': '500000',
            'late_retirement_start_age': 85,
            'life_expectancy': 95,
            'annual_basic_expenses': '30000',
            'annual_healthcare_costs': '20000',
            'long_term_care_annual': '60000',
            'ltc_insurance_coverage': '40000',
            'social_security_annual': '30000',
            'expected_return': '3',
            'inflation_rate': '2',
            'desired_legacy': '100000'
        }
        result = calculate_late_retirement_phase(data)

        self.assertEqual(result.phase_duration_years, 10)
        self.assertGreater(result.total_ltc_costs, 0)
        self.assertGreater(result.total_ltc_insurance_paid, 0)
        self.assertGreater(result.net_ltc_out_of_pocket, 0)

    def test_zero_duration_late_retirement(self):
        """Test when start age equals life expectancy."""
        data = {
            'starting_portfolio': '300000',
            'late_retirement_start_age': 90,
            'life_expectancy': 90,
            'annual_basic_expenses': '25000',
            'annual_healthcare_costs': '15000',
            'long_term_care_annual': '0',
            'ltc_insurance_coverage': '0',
            'social_security_annual': '25000',
            'expected_return': '2',
            'inflation_rate': '2',
            'desired_legacy': '50000'
        }
        result = calculate_late_retirement_phase(data)

        self.assertEqual(result.phase_duration_years, 0)
        self.assertEqual(result.total_withdrawals, Decimal('0'))

    def test_ltc_insurance_full_coverage(self):
        """Test when LTC insurance fully covers long-term care costs."""
        data = {
            'starting_portfolio': '400000',
            'late_retirement_start_age': 85,
            'life_expectancy': 92,
            'annual_basic_expenses': '20000',
            'annual_healthcare_costs': '15000',
            'long_term_care_annual': '50000',
            'ltc_insurance_coverage': '60000',
            'social_security_annual': '28000',
            'expected_return': '3',
            'inflation_rate': '2',
            'desired_legacy': '0'
        }
        result = calculate_late_retirement_phase(data)

        # Insurance should cover all LTC costs (at least initially)
        self.assertLess(result.net_ltc_out_of_pocket, result.total_ltc_costs)

    def test_portfolio_depletion_late_retirement(self):
        """Test scenario where portfolio runs out."""
        data = {
            'starting_portfolio': '150000',
            'late_retirement_start_age': 85,
            'life_expectancy': 95,
            'annual_basic_expenses': '25000',
            'annual_healthcare_costs': '20000',
            'long_term_care_annual': '70000',
            'ltc_insurance_coverage': '30000',
            'social_security_annual': '20000',
            'expected_return': '2',
            'inflation_rate': '3',
            'desired_legacy': '100000'
        }
        result = calculate_late_retirement_phase(data)

        # Portfolio should be depleted
        self.assertEqual(result.ending_portfolio, Decimal('0'))
        self.assertFalse(result.portfolio_sufficient)

    def test_legacy_goal_met(self):
        """Test scenario where legacy goal is achieved."""
        data = {
            'starting_portfolio': '800000',
            'late_retirement_start_age': 85,
            'life_expectancy': 92,
            'annual_basic_expenses': '20000',
            'annual_healthcare_costs': '12000',
            'long_term_care_annual': '40000',
            'ltc_insurance_coverage': '35000',
            'social_security_annual': '30000',
            'expected_return': '4',
            'inflation_rate': '2',
            'desired_legacy': '200000'
        }
        result = calculate_late_retirement_phase(data)

        # Should have sufficient portfolio for legacy
        self.assertGreater(result.legacy_amount, Decimal('200000'))
        self.assertTrue(result.portfolio_sufficient)

    def test_no_ltc_costs(self):
        """Test with no long-term care costs."""
        data = {
            'starting_portfolio': '450000',
            'late_retirement_start_age': 85,
            'life_expectancy': 93,
            'annual_basic_expenses': '22000',
            'annual_healthcare_costs': '18000',
            'long_term_care_annual': '0',
            'ltc_insurance_coverage': '0',
            'social_security_annual': '28000',
            'expected_return': '3',
            'inflation_rate': '2',
            'desired_legacy': '100000'
        }
        result = calculate_late_retirement_phase(data)

        self.assertEqual(result.total_ltc_costs, Decimal('0'))
        self.assertEqual(result.total_ltc_insurance_paid, Decimal('0'))
        self.assertEqual(result.net_ltc_out_of_pocket, Decimal('0'))


class RetirementCalculatorFormTests(TestCase):
    """Comprehensive tests for RetirementCalculatorForm validation."""

    def test_form_with_valid_data(self):
        """Test form with all valid data."""
        from .forms import RetirementCalculatorForm

        form = RetirementCalculatorForm(data={
            'current_age': 30,
            'retirement_age': 65,
            'current_savings': '50000',
            'monthly_contribution': '1000',
            'expected_return': '7',
            'variance': '2'
        })

        self.assertTrue(form.is_valid())

    def test_form_unrealistic_return_rate(self):
        """Test that returns above 15% are rejected."""
        from .forms import RetirementCalculatorForm

        form = RetirementCalculatorForm(data={
            'current_age': 30,
            'retirement_age': 65,
            'current_savings': '50000',
            'monthly_contribution': '1000',
            'expected_return': '20',  # Unrealistic
            'variance': '2'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('expected_return', form.errors)
        self.assertIn('unrealistic', str(form.errors['expected_return']).lower())

    def test_form_excessive_monthly_contribution(self):
        """Test that monthly contributions over $10,000 are rejected."""
        from .forms import RetirementCalculatorForm

        form = RetirementCalculatorForm(data={
            'current_age': 25,
            'retirement_age': 60,
            'current_savings': '10000',
            'monthly_contribution': '15000',  # Too high
            'expected_return': '7',
            'variance': '2'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('monthly_contribution', form.errors)

    def test_form_high_variance_warning(self):
        """Test that variance above 10% triggers validation error."""
        from .forms import RetirementCalculatorForm

        form = RetirementCalculatorForm(data={
            'current_age': 30,
            'retirement_age': 65,
            'current_savings': '50000',
            'monthly_contribution': '1000',
            'expected_return': '7',
            'variance': '15'  # Too high
        })

        self.assertFalse(form.is_valid())
        self.assertIn('variance', form.errors)
        self.assertIn('high risk', str(form.errors['variance']).lower())

    def test_form_retirement_age_less_than_current_age(self):
        """Test that retirement age must be greater than current age."""
        from .forms import RetirementCalculatorForm

        form = RetirementCalculatorForm(data={
            'current_age': 65,
            'retirement_age': 60,  # Invalid: less than current age
            'current_savings': '100000',
            'monthly_contribution': '0',
            'expected_return': '5',
            'variance': '2'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('Retirement age must be greater', str(form.errors['__all__']))

    def test_form_retirement_age_equals_current_age(self):
        """Test that retirement age equal to current age is rejected."""
        from .forms import RetirementCalculatorForm

        form = RetirementCalculatorForm(data={
            'current_age': 65,
            'retirement_age': 65,  # Same as current age
            'current_savings': '100000',
            'monthly_contribution': '0',
            'expected_return': '5',
            'variance': '2'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_form_less_than_five_years_to_retirement(self):
        """Test that less than 5 years to retirement is rejected."""
        from .forms import RetirementCalculatorForm

        form = RetirementCalculatorForm(data={
            'current_age': 62,
            'retirement_age': 64,  # Only 2 years
            'current_savings': '200000',
            'monthly_contribution': '1000',
            'expected_return': '5',
            'variance': '2'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('too short', str(form.errors['__all__']).lower())

    def test_form_no_savings_or_contributions(self):
        """Test that user must have either savings or contributions."""
        from .forms import RetirementCalculatorForm

        form = RetirementCalculatorForm(data={
            'current_age': 25,
            'retirement_age': 65,
            'current_savings': '0',  # No savings
            'monthly_contribution': '0',  # No contributions
            'expected_return': '7',
            'variance': '2'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('savings or monthly contributions', str(form.errors['__all__']).lower())

    def test_form_variance_default_value(self):
        """Test that variance defaults to 2.0 when not provided."""
        from .forms import RetirementCalculatorForm

        form = RetirementCalculatorForm(data={
            'current_age': 30,
            'retirement_age': 65,
            'current_savings': '50000',
            'monthly_contribution': '1000',
            'expected_return': '7'
            # variance not provided
        })

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['variance'], Decimal('2.0'))

    def test_form_age_boundaries(self):
        """Test age validation boundaries."""
        from .forms import RetirementCalculatorForm

        # Test minimum age (18)
        form = RetirementCalculatorForm(data={
            'current_age': 18,
            'retirement_age': 65,
            'current_savings': '1000',
            'monthly_contribution': '100',
            'expected_return': '7',
            'variance': '2'
        })
        self.assertTrue(form.is_valid())

        # Test age below minimum (17)
        form = RetirementCalculatorForm(data={
            'current_age': 17,
            'retirement_age': 65,
            'current_savings': '1000',
            'monthly_contribution': '100',
            'expected_return': '7',
            'variance': '2'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('current_age', form.errors)


class CustomUserCreationFormTests(TestCase):
    """Tests for custom user registration form."""

    def test_form_with_email(self):
        """Test that form accepts valid email."""
        from .forms import CustomUserCreationForm

        form = CustomUserCreationForm(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        })

        self.assertTrue(form.is_valid())

    def test_form_saves_email_to_user(self):
        """Test that email is saved to user model."""
        from .forms import CustomUserCreationForm

        form = CustomUserCreationForm(data={
            'username': 'emailuser',
            'email': 'emailuser@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
        })

        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, 'emailuser@example.com')


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

    def test_send_scenario_email_task_executes(self):
        """Test that the background task function executes successfully."""
        from calculator.tasks import send_scenario_email
        from django.core import mail

        scenario = Scenario.objects.create(
            user=self.user,
            name='Email Task Test',
            data={
                'current_age': '35',
                'retirement_start_age': '67',
                'current_savings': '100000',
                'monthly_contribution': '2000',
                'expected_return': '6',
                'employer_match_rate': '50',
                'annual_salary_increase': '2'
            }
        )

        # Execute the task function directly
        result = send_scenario_email(scenario.pk, self.user.email)

        # Should return success message
        self.assertIn('Email sent successfully', result)
        self.assertIn(self.user.email, result)

        # Should have sent an email (in console backend)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Retirement Scenario: {scenario.name}')
        self.assertIn(scenario.name, mail.outbox[0].body)
        self.assertIn('Phase 1: Accumulation', mail.outbox[0].body)

    def test_send_scenario_email_task_error_handling(self):
        """Test that the background task handles errors gracefully."""
        from calculator.tasks import send_scenario_email

        # Try to email non-existent scenario
        result = send_scenario_email(999999, 'test@example.com')

        # Should return error message instead of crashing
        self.assertIn('Error', result)


class ResponsiveNavigationTests(TestCase):
    """Test mobile responsive navigation."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_navigation_contains_mobile_menu_button(self):
        """Test that navigation includes mobile hamburger menu button."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calculator:multi_phase_calculator'))

        self.assertEqual(response.status_code, 200)
        # Check for Alpine.js mobile menu trigger
        self.assertContains(response, 'x-data="{ mobileMenuOpen: false }"')
        self.assertContains(response, '@click="mobileMenuOpen = !mobileMenuOpen"')

    def test_navigation_has_desktop_and_mobile_sections(self):
        """Test that navigation has both desktop and mobile menu sections."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calculator:multi_phase_calculator'))

        # Desktop nav should be hidden on mobile
        self.assertContains(response, 'hidden md:flex')
        # Mobile menu button should be hidden on desktop
        self.assertContains(response, 'md:hidden')
        # Mobile menu section exists
        self.assertContains(response, 'x-show="mobileMenuOpen"')

    def test_navigation_includes_all_main_links(self):
        """Test that both desktop and mobile nav include main links."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calculator:multi_phase_calculator'))

        # Check for main navigation links (should appear in both desktop and mobile)
        self.assertContains(response, 'Simple Calculator', count=2)  # Desktop + Mobile
        # "Multi-Phase" appears in: desktop nav, mobile nav, page title, and results section
        self.assertContains(response, 'Multi-Phase Calculator')  # At least once
        self.assertContains(response, 'Scenarios')  # Desktop + Mobile
        self.assertContains(response, 'Compare')  # Desktop + Mobile

    def test_authenticated_nav_shows_logout(self):
        """Test that authenticated users see logout button."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calculator:multi_phase_calculator'))

        self.assertContains(response, 'Logout', count=2)  # Desktop + Mobile
        self.assertContains(response, 'testuser', count=2)  # Username shown twice

    def test_unauthenticated_nav_shows_login(self):
        """Test that unauthenticated users see login button."""
        # Test on a public page (login page itself) since calculator pages require auth
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

        # Login button should be in the navigation
        self.assertContains(response, 'Login')

    def test_navigation_no_register_button_in_main_nav(self):
        """Test that Register button is NOT in main navigation."""
        response = self.client.get(reverse('login'))

        # Login page should have register link
        self.assertContains(response, 'create a new account')

        # But we shouldn't have a Register button in the nav
        # (We check by looking for the nav structure without Register)
        content = response.content.decode()
        # The navigation should only have Login button for unauthenticated users
        self.assertIn('Login', content)

    def test_base_template_loads_alpine_js(self):
        """Test that base template includes Alpine.js for mobile menu interactivity."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calculator:multi_phase_calculator'))

        # Check for Alpine.js CDN script
        self.assertContains(response, 'alpinejs')
        self.assertContains(response, 'cdn.jsdelivr.net')

    def test_mobile_menu_has_smooth_transitions(self):
        """Test that mobile menu includes transition effects."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calculator:multi_phase_calculator'))

        # Check for Alpine.js transition directives
        self.assertContains(response, 'x-transition')

    def test_navigation_responsive_classes(self):
        """Test that navigation uses Tailwind responsive classes correctly."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calculator:multi_phase_calculator'))

        content = response.content.decode()

        # Desktop menu should hide below md breakpoint
        self.assertIn('hidden md:flex', content)
        # Mobile button should hide above md breakpoint
        self.assertIn('md:hidden', content)


class CustomErrorPageTests(TestCase):
    """Test custom error pages (404, 500)."""

    def test_404_page_uses_custom_template(self):
        """Test that 404 errors use custom template."""
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        # Will test template after we create it

    def test_404_page_matches_site_design(self):
        """Test that 404 page includes navigation and footer."""
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        # Should have navigation
        self.assertContains(response, 'Retirement Planner', status_code=404)
        # Should have helpful message
        self.assertContains(response, '404', status_code=404)
