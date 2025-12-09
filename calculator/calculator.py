"""
Retirement calculation engine.

This module provides functions for calculating retirement savings projections
using compound interest formulas.
"""

from decimal import Decimal
from dataclasses import dataclass
from typing import Optional


@dataclass
class RetirementProjection:
    """
    Structured results from retirement calculation.

    Using a dataclass makes the code more readable and type-safe.
    """
    years_to_retirement: int
    total_contributions: Decimal
    future_value: Decimal
    investment_gains: Decimal
    monthly_income_estimate: Decimal
    variance: Optional[Decimal] = None

    @property
    def return_on_investment_percent(self) -> Decimal:
        """Calculate ROI as a percentage"""
        if self.total_contributions == 0:
            return Decimal('0')
        return (self.investment_gains / self.total_contributions) * Decimal('100')


def calculate_future_value_lump_sum(
    principal: Decimal,
    annual_rate: Decimal,
    years: int
) -> Decimal:
    """
    Calculate future value of a lump sum investment.

    Formula: FV = PV × (1 + r)^n

    Args:
        principal: Initial investment amount
        annual_rate: Annual interest rate as percentage (e.g., 7.5 for 7.5%)
        years: Number of years to compound

    Returns:
        Future value of the investment

    Example:
        >>> calculate_future_value_lump_sum(Decimal('10000'), Decimal('7.5'), 30)
        Decimal('87549.98')
    """
    months = years * 12
    monthly_rate = (annual_rate / Decimal('100')) / Decimal('12')

    future_value = principal * ((1 + monthly_rate) ** months)
    return future_value


def calculate_future_value_annuity(
    monthly_payment: Decimal,
    annual_rate: Decimal,
    years: int
) -> Decimal:
    """
    Calculate future value of regular monthly contributions (annuity).

    Formula: FV = PMT × [((1 + r)^n - 1) / r]

    Args:
        monthly_payment: Regular monthly contribution
        annual_rate: Annual interest rate as percentage (e.g., 7.5 for 7.5%)
        years: Number of years of contributions

    Returns:
        Future value of all contributions with compound interest

    Example:
        >>> calculate_future_value_annuity(Decimal('1000'), Decimal('7.5'), 30)
        Decimal('1265362.63')
    """
    months = years * 12
    monthly_rate = (annual_rate / Decimal('100')) / Decimal('12')

    if monthly_rate > 0:
        future_value = monthly_payment * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        )
    else:
        # If rate is 0, just multiply contributions by months
        future_value = monthly_payment * months

    return future_value


def calculate_retirement_savings(
    current_age: int,
    retirement_age: int,
    current_savings: Decimal,
    monthly_contribution: Decimal,
    annual_return_rate: Decimal,
    variance: Optional[Decimal] = None
) -> RetirementProjection:
    """
    Calculate comprehensive retirement savings projection.

    This is the main function that combines lump sum and annuity calculations
    to project total retirement savings.

    Args:
        current_age: Current age in years
        retirement_age: Target retirement age
        current_savings: Current savings balance
        monthly_contribution: Monthly contribution amount
        annual_return_rate: Expected annual return as percentage
        variance: Optional return variance/volatility

    Returns:
        RetirementProjection dataclass with complete results

    Example:
        >>> result = calculate_retirement_savings(
        ...     current_age=30,
        ...     retirement_age=65,
        ...     current_savings=Decimal('50000'),
        ...     monthly_contribution=Decimal('1000'),
        ...     annual_return_rate=Decimal('7.5')
        ... )
        >>> print(f"You'll have ${result.future_value:,.2f} at retirement")
    """
    years_to_retirement = retirement_age - current_age

    # Calculate future value of current savings
    fv_current_savings = calculate_future_value_lump_sum(
        principal=current_savings,
        annual_rate=annual_return_rate,
        years=years_to_retirement
    )

    # Calculate future value of monthly contributions
    fv_contributions = calculate_future_value_annuity(
        monthly_payment=monthly_contribution,
        annual_rate=annual_return_rate,
        years=years_to_retirement
    )

    # Total future value
    future_value = fv_current_savings + fv_contributions

    # Total amount contributed
    total_contributions = current_savings + (
        monthly_contribution * years_to_retirement * 12
    )

    # Investment gains (profit)
    investment_gains = future_value - total_contributions

    # Estimate monthly income during retirement (assuming 20-year retirement)
    retirement_duration_months = 20 * 12  # 240 months
    monthly_income_estimate = future_value / Decimal(retirement_duration_months)

    return RetirementProjection(
        years_to_retirement=years_to_retirement,
        total_contributions=total_contributions,
        future_value=future_value,
        investment_gains=investment_gains,
        monthly_income_estimate=monthly_income_estimate,
        variance=variance
    )


def calculate_safe_withdrawal_rate(
    total_savings: Decimal,
    withdrawal_rate: Decimal = Decimal('4.0')
) -> Decimal:
    """
    Calculate annual safe withdrawal amount using the 4% rule.

    The 4% rule suggests withdrawing 4% of retirement savings annually
    to maintain the portfolio for 30 years.

    Args:
        total_savings: Total retirement savings
        withdrawal_rate: Annual withdrawal rate as percentage (default 4%)

    Returns:
        Annual safe withdrawal amount

    Example:
        >>> calculate_safe_withdrawal_rate(Decimal('1000000'))
        Decimal('40000.00')  # $40,000 per year
    """
    return total_savings * (withdrawal_rate / Decimal('100'))
