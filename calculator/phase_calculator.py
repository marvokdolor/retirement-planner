"""
Calculator functions for the four retirement phases.

Each phase has specific calculation logic tailored to its unique characteristics.
"""

from decimal import Decimal
from dataclasses import dataclass
from typing import Optional
from django.core.cache import cache
from functools import wraps
import hashlib
import json


# ===== CACHING UTILITY =====

def cache_calculation(timeout=3600):
    """
    Decorator to cache calculation results using MD5 hashing of sorted input data.

    Args:
        timeout (int): Cache timeout in seconds. Default is 3600 (1 hour).

    Returns:
        function: Decorated function with caching enabled.

    Example:
        @cache_calculation(timeout=1800)
        def calculate_retirement(data):
            return expensive_calculation(data)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(data: dict):
            # Create a cache key from the function name and input data
            # Sort keys for consistent hashing
            data_str = json.dumps(data, sort_keys=True, default=str)
            cache_key = f"calc_{func.__name__}_{hashlib.md5(data_str.encode()).hexdigest()}"

            # Try to get cached result
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Calculate and cache result
            result = func(data)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


# ===== RESULT DATACLASSES =====

@dataclass
class AccumulationResults:
    """
    Results from accumulation phase calculation.

    Attributes:
        years_to_retirement (int): Number of years until retirement
        retirement_start_age (int): Age at retirement (for cascading to next phases)
        total_personal_contributions (Decimal): Sum of all personal contributions
        total_employer_contributions (Decimal): Sum of employer matching contributions
        future_value (Decimal): Projected portfolio value at retirement
        investment_gains (Decimal): Total gains from compound interest
        final_monthly_contribution (Decimal): Monthly contribution at retirement (after salary increases)
    """
    years_to_retirement: int
    retirement_start_age: int
    total_personal_contributions: Decimal
    total_employer_contributions: Decimal
    future_value: Decimal
    investment_gains: Decimal
    final_monthly_contribution: Decimal  # After salary increases


@dataclass
class PhasedRetirementResults:
    """Results from phased retirement phase calculation"""
    phase_duration_years: int
    full_retirement_age: int  # For cascading to Phase 3 and Phase 4
    starting_portfolio: Decimal
    ending_portfolio: Decimal
    total_contributions: Decimal
    total_withdrawals: Decimal
    total_part_time_income: Decimal
    investment_gains: Decimal
    net_change: Decimal


@dataclass
class ActiveRetirementResults:
    """Results from active retirement phase calculation"""
    phase_duration_years: int
    active_retirement_end_age: int  # For cascading to Phase 4
    starting_portfolio: Decimal
    ending_portfolio: Decimal
    total_withdrawals: Decimal
    total_social_security: Decimal
    total_pension: Decimal
    total_investment_gains: Decimal
    average_annual_withdrawal: Decimal
    portfolio_depletion_age: Optional[int]  # Age when money runs out, if applicable


@dataclass
class LateRetirementResults:
    """Results from late retirement phase calculation"""
    phase_duration_years: int
    starting_portfolio: Decimal
    ending_portfolio: Decimal
    total_withdrawals: Decimal
    total_ltc_costs: Decimal
    total_ltc_insurance_paid: Decimal
    total_social_security: Decimal
    total_investment_gains: Decimal
    net_ltc_out_of_pocket: Decimal
    legacy_amount: Decimal
    portfolio_sufficient: bool


# ===== PHASE 1: ACCUMULATION =====

@cache_calculation(timeout=3600)  # Cache for 1 hour
def calculate_accumulation_phase(data: dict) -> AccumulationResults:
    """
    Calculate accumulation phase: Building wealth through contributions.

    This phase models the working years where you build retirement savings through:
    - Compound interest on existing savings
    - Regular monthly contributions
    - Optional employer matching (50% up to 6% of salary)
    - Optional annual salary increases

    Args:
        data (dict): Input parameters containing:
            - current_age (int): Current age in years
            - retirement_start_age (int): Target retirement age
            - current_savings (float/Decimal): Current retirement savings
            - monthly_contribution (float/Decimal): Monthly contribution amount
            - employer_match_rate (float/Decimal, optional): Employer match rate (0-100)
            - expected_return (float/Decimal): Expected annual return rate (0-100)
            - annual_salary_increase (float/Decimal, optional): Annual salary increase (0-100)

    Returns:
        AccumulationResults: Dataclass containing:
            - years_to_retirement: Duration of accumulation phase
            - total_personal_contributions: Sum of personal contributions
            - total_employer_contributions: Sum of employer matching
            - future_value: Final portfolio value
            - investment_gains: Total compound interest earned
            - final_monthly_contribution: Monthly contribution at retirement

    Example:
        >>> data = {
        ...     'current_age': 30,
        ...     'retirement_start_age': 65,
        ...     'current_savings': 50000,
        ...     'monthly_contribution': 1000,
        ...     'employer_match_rate': 3,
        ...     'expected_return': 7,
        ...     'annual_salary_increase': 2
        ... }
        >>> results = calculate_accumulation_phase(data)
        >>> print(f"Portfolio at retirement: ${results.future_value:,.2f}")
    """
    current_age = int(data['current_age'])
    retirement_start_age = int(data['retirement_start_age'])
    current_savings = Decimal(str(data['current_savings']))
    monthly_contribution = Decimal(str(data['monthly_contribution']))
    employer_match_rate = Decimal(str(data.get('employer_match_rate') or 0))
    expected_return = Decimal(str(data['expected_return']))
    annual_salary_increase = Decimal(str(data.get('annual_salary_increase') or 0))

    years_to_retirement = retirement_start_age - current_age
    monthly_rate = (expected_return / Decimal('100')) / Decimal('12')
    salary_increase_rate = annual_salary_increase / Decimal('100')

    # Future value of current savings (lump sum)
    months = years_to_retirement * 12
    fv_current_savings = current_savings * ((1 + monthly_rate) ** months)

    # Calculate contributions with salary increases and employer match
    total_personal_contributions = Decimal('0')
    total_employer_contributions = Decimal('0')
    fv_contributions = Decimal('0')

    current_contribution = monthly_contribution
    current_employer_match = monthly_contribution * (employer_match_rate / Decimal('100'))

    for month in range(months):
        # Add contribution for this month
        total_personal_contributions += current_contribution
        total_employer_contributions += current_employer_match

        # Future value of this contribution (compounded from month it was made to retirement)
        # Number of months this specific contribution will compound
        months_to_compound = months - month - 1  # -1 because contribution at end of month
        contribution_fv = (current_contribution + current_employer_match) * ((1 + monthly_rate) ** months_to_compound)
        fv_contributions += contribution_fv

        # Increase contribution annually based on salary increases
        if (month + 1) % 12 == 0 and salary_increase_rate > 0:
            current_contribution = current_contribution * (1 + salary_increase_rate)
            current_employer_match = current_contribution * (employer_match_rate / Decimal('100'))

    future_value = fv_current_savings + fv_contributions
    investment_gains = future_value - (current_savings + total_personal_contributions + total_employer_contributions)

    return AccumulationResults(
        years_to_retirement=years_to_retirement,
        retirement_start_age=retirement_start_age,
        total_personal_contributions=total_personal_contributions,
        total_employer_contributions=total_employer_contributions,
        future_value=future_value,
        investment_gains=investment_gains,
        final_monthly_contribution=current_contribution
    )


# ===== PHASE 2: PHASED RETIREMENT =====

@cache_calculation(timeout=3600)  # Cache for 1 hour
def calculate_phased_retirement_phase(data: dict) -> PhasedRetirementResults:
    """
    Calculate phased retirement: Semi-retired with optional income and withdrawals.

    Includes:
    - Starting portfolio balance
    - Optional part-time income and continued contributions
    - Optional withdrawals to supplement income
    - Portfolio growth during transition period
    """
    starting_portfolio = Decimal(str(data['starting_portfolio']))
    phase_start_age = int(data['phase_start_age'])
    full_retirement_age = int(data['full_retirement_age'])
    monthly_contribution = Decimal(str(data.get('monthly_contribution') or 0))
    annual_withdrawal = Decimal(str(data.get('annual_withdrawal') or 0))
    part_time_income = Decimal(str(data.get('part_time_income') or 0))
    expected_return = Decimal(str(data['expected_return']))

    phase_duration_years = full_retirement_age - phase_start_age
    monthly_rate = (expected_return / Decimal('100')) / Decimal('12')
    monthly_withdrawal = annual_withdrawal / Decimal('12')

    # Simulate year by year
    portfolio = starting_portfolio
    total_contributions = Decimal('0')
    total_withdrawals = Decimal('0')
    total_investment_gains = Decimal('0')

    for month in range(phase_duration_years * 12):
        # Investment growth
        monthly_gain = portfolio * monthly_rate
        total_investment_gains += monthly_gain
        portfolio += monthly_gain

        # Contributions
        portfolio += monthly_contribution
        total_contributions += monthly_contribution

        # Withdrawals
        portfolio -= monthly_withdrawal
        total_withdrawals += monthly_withdrawal

    ending_portfolio = portfolio
    net_change = ending_portfolio - starting_portfolio
    total_part_time_income = part_time_income * phase_duration_years

    return PhasedRetirementResults(
        phase_duration_years=phase_duration_years,
        full_retirement_age=full_retirement_age,
        starting_portfolio=starting_portfolio,
        ending_portfolio=ending_portfolio,
        total_contributions=total_contributions,
        total_withdrawals=total_withdrawals,
        total_part_time_income=total_part_time_income,
        investment_gains=total_investment_gains,
        net_change=net_change
    )


# ===== PHASE 3: ACTIVE RETIREMENT =====

@cache_calculation(timeout=3600)  # Cache for 1 hour
def calculate_active_retirement_phase(data: dict) -> ActiveRetirementResults:
    """
    Calculate active retirement: Living off portfolio with inflation-adjusted expenses.

    Includes:
    - Annual expenses and healthcare costs
    - Social Security and pension income
    - Inflation-adjusted spending
    - Portfolio sustainability check
    """
    starting_portfolio = Decimal(str(data['starting_portfolio']))
    start_age = int(data['active_retirement_start_age'])
    end_age = int(data['active_retirement_end_age'])
    annual_expenses = Decimal(str(data['annual_expenses']))
    annual_healthcare = Decimal(str(data['annual_healthcare_costs']))
    social_security = Decimal(str(data.get('social_security_annual') or 0))
    pension = Decimal(str(data.get('pension_annual') or 0))
    expected_return = Decimal(str(data['expected_return']))
    inflation_rate = Decimal(str(data['inflation_rate']))

    phase_duration_years = end_age - start_age
    phase_duration_months = phase_duration_years * 12
    annual_return_rate = expected_return / Decimal('100')
    annual_inflation_rate = inflation_rate / Decimal('100')

    # Convert to monthly rates
    monthly_return_rate = annual_return_rate / Decimal('12')
    monthly_inflation_rate = annual_inflation_rate / Decimal('12')

    # Convert annual amounts to monthly
    monthly_expenses = annual_expenses / Decimal('12')
    monthly_healthcare = annual_healthcare / Decimal('12')
    monthly_social_security = social_security / Decimal('12')
    monthly_pension = pension / Decimal('12')

    # Simulate month by month
    portfolio = starting_portfolio
    total_withdrawals = Decimal('0')
    total_social_security = Decimal('0')
    total_pension = Decimal('0')
    total_investment_gains = Decimal('0')
    current_monthly_expenses = monthly_expenses
    current_monthly_healthcare = monthly_healthcare
    portfolio_depletion_age = None

    for month in range(phase_duration_months):
        current_age = start_age + (month // 12)

        # Investment growth (monthly compounding)
        monthly_gain = portfolio * monthly_return_rate
        total_investment_gains += monthly_gain
        portfolio += monthly_gain

        # Income
        total_social_security += monthly_social_security
        total_pension += monthly_pension

        # Calculate withdrawal needed
        total_monthly_costs = current_monthly_expenses + current_monthly_healthcare
        monthly_income = monthly_social_security + monthly_pension
        withdrawal_needed = max(Decimal('0'), total_monthly_costs - monthly_income)

        # Make withdrawal
        if withdrawal_needed > portfolio:
            # Portfolio depleted
            portfolio_depletion_age = current_age
            withdrawal_needed = portfolio
            portfolio = Decimal('0')
        else:
            portfolio -= withdrawal_needed

        total_withdrawals += withdrawal_needed

        # Inflation adjustment monthly
        current_monthly_expenses = current_monthly_expenses * (1 + monthly_inflation_rate)
        current_monthly_healthcare = current_monthly_healthcare * (1 + monthly_inflation_rate)

        if portfolio <= 0:
            break

    ending_portfolio = portfolio
    average_annual_withdrawal = total_withdrawals / phase_duration_years if phase_duration_years > 0 else Decimal('0')

    return ActiveRetirementResults(
        phase_duration_years=phase_duration_years,
        active_retirement_end_age=end_age,
        starting_portfolio=starting_portfolio,
        ending_portfolio=ending_portfolio,
        total_withdrawals=total_withdrawals,
        total_social_security=total_social_security,
        total_pension=total_pension,
        total_investment_gains=total_investment_gains,
        average_annual_withdrawal=average_annual_withdrawal,
        portfolio_depletion_age=portfolio_depletion_age
    )


# ===== PHASE 4: LATE RETIREMENT =====

@cache_calculation(timeout=3600)  # Cache for 1 hour
def calculate_late_retirement_phase(data: dict) -> LateRetirementResults:
    """
    Calculate late retirement: High healthcare costs and long-term care planning.

    Includes:
    - Long-term care costs and insurance
    - Higher medical expenses
    - Legacy planning
    - Portfolio sufficiency check
    """
    starting_portfolio = Decimal(str(data['starting_portfolio']))
    start_age = int(data['late_retirement_start_age'])
    life_expectancy = int(data['life_expectancy'])
    annual_basic_expenses = Decimal(str(data['annual_basic_expenses']))
    annual_healthcare = Decimal(str(data['annual_healthcare_costs']))
    ltc_annual = Decimal(str(data.get('long_term_care_annual') or 0))
    ltc_insurance = Decimal(str(data.get('ltc_insurance_coverage') or 0))
    social_security = Decimal(str(data.get('social_security_annual') or 0))
    expected_return = Decimal(str(data['expected_return']))
    inflation_rate = Decimal(str(data['inflation_rate']))
    desired_legacy = Decimal(str(data.get('desired_legacy') or 0))

    phase_duration_years = life_expectancy - start_age
    phase_duration_months = phase_duration_years * 12
    annual_return_rate = expected_return / Decimal('100')
    annual_inflation_rate = inflation_rate / Decimal('100')

    # Convert to monthly rates
    monthly_return_rate = annual_return_rate / Decimal('12')
    monthly_inflation_rate = annual_inflation_rate / Decimal('12')

    # Convert annual amounts to monthly
    monthly_basic_expenses = annual_basic_expenses / Decimal('12')
    monthly_healthcare = annual_healthcare / Decimal('12')
    monthly_ltc = ltc_annual / Decimal('12')
    monthly_ltc_insurance = ltc_insurance / Decimal('12')
    monthly_social_security = social_security / Decimal('12')

    # Simulate month by month
    portfolio = starting_portfolio
    total_withdrawals = Decimal('0')
    total_ltc_costs = Decimal('0')
    total_ltc_insurance_paid = Decimal('0')
    total_social_security = Decimal('0')
    total_investment_gains = Decimal('0')
    current_monthly_basic_expenses = monthly_basic_expenses
    current_monthly_healthcare = monthly_healthcare
    current_monthly_ltc = monthly_ltc

    portfolio_depleted_early = False  # Track if portfolio ran out before phase end

    for month in range(phase_duration_months):
        # Investment growth (monthly compounding)
        monthly_gain = portfolio * monthly_return_rate
        total_investment_gains += monthly_gain
        portfolio += monthly_gain

        # Income
        total_social_security += monthly_social_security

        # Costs
        total_monthly_costs = current_monthly_basic_expenses + current_monthly_healthcare + current_monthly_ltc
        total_ltc_costs += current_monthly_ltc

        # LTC insurance coverage
        ltc_coverage_this_month = min(monthly_ltc_insurance, current_monthly_ltc)
        total_ltc_insurance_paid += ltc_coverage_this_month

        # Net withdrawal needed
        net_costs = total_monthly_costs - ltc_coverage_this_month
        withdrawal_needed = max(Decimal('0'), net_costs - monthly_social_security)

        # Make withdrawal
        withdrawal_needed = min(withdrawal_needed, portfolio)
        portfolio -= withdrawal_needed
        total_withdrawals += withdrawal_needed

        # Inflation adjustment monthly
        current_monthly_basic_expenses = current_monthly_basic_expenses * (1 + monthly_inflation_rate)
        current_monthly_healthcare = current_monthly_healthcare * (1 + monthly_inflation_rate)
        current_monthly_ltc = current_monthly_ltc * (1 + monthly_inflation_rate)

        if portfolio <= 0:
            portfolio_depleted_early = True  # Mark that we ran out of money
            break

    ending_portfolio = max(Decimal('0'), portfolio)
    net_ltc_out_of_pocket = total_ltc_costs - total_ltc_insurance_paid
    legacy_amount = ending_portfolio

    # Portfolio is sufficient ONLY if:
    # 1. We made it through the entire phase without running out of money
    # 2. AND the ending portfolio meets or exceeds the desired legacy goal
    portfolio_sufficient = (not portfolio_depleted_early) and (ending_portfolio >= desired_legacy)

    return LateRetirementResults(
        phase_duration_years=phase_duration_years,
        starting_portfolio=starting_portfolio,
        ending_portfolio=ending_portfolio,
        total_withdrawals=total_withdrawals,
        total_ltc_costs=total_ltc_costs,
        total_ltc_insurance_paid=total_ltc_insurance_paid,
        total_social_security=total_social_security,
        total_investment_gains=total_investment_gains,
        net_ltc_out_of_pocket=net_ltc_out_of_pocket,
        legacy_amount=legacy_amount,
        portfolio_sufficient=portfolio_sufficient
    )
