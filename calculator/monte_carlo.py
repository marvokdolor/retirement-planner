"""
Monte Carlo simulation for retirement planning.

Provides probabilistic projections using numpy for randomized market returns.
"""

import numpy as np
from decimal import Decimal
from dataclasses import dataclass
from typing import Dict


@dataclass
class MonteCarloResults:
    """Results from Monte Carlo simulation."""
    mean: Decimal
    median: Decimal
    percentile_10: Decimal  # Pessimistic scenario
    percentile_25: Decimal
    percentile_50: Decimal  # Median (same as median field)
    percentile_75: Decimal
    percentile_90: Decimal  # Optimistic scenario
    std_deviation: Decimal
    success_rate: Decimal  # % of simulations that don't run out of money
    all_outcomes: list  # For charting (optional, can be large)
    # Year-by-year percentile trajectories for charting
    yearly_10th: list = None  # 10th percentile by year
    yearly_50th: list = None  # Median by year
    yearly_90th: list = None  # 90th percentile by year
    years: list = None  # Year labels for x-axis


def run_accumulation_monte_carlo(
    current_savings: float,
    monthly_contribution: float,
    years: int,
    expected_return: float,  # Annual return as percentage (e.g., 7.0 for 7%)
    variance: float,  # Annual standard deviation as percentage (e.g., 2.0 for 2%)
    runs: int = 10000,
    annual_contribution_increase: float = 0.0  # Annual percentage increase in contributions
) -> MonteCarloResults:
    """
    Run Monte Carlo simulation for accumulation phase.

    Args:
        current_savings: Starting balance
        monthly_contribution: Amount added each month (including employer match)
        years: Number of years to simulate
        expected_return: Expected annual return (%)
        variance: Annual volatility/standard deviation (%)
        runs: Number of simulation runs
        annual_contribution_increase: Annual % increase in contributions (for salary growth)

    Returns:
        MonteCarloResults with statistical outcomes
    """
    months = years * 12

    # Convert percentages to decimals
    annual_rate = expected_return / 100
    annual_std = variance / 100
    contribution_growth_rate = annual_contribution_increase / 100

    # Convert to monthly (assuming geometric Brownian motion)
    # Both Monte Carlo and deterministic calculations use monthly compounding
    monthly_rate = annual_rate / 12
    monthly_std = annual_std / np.sqrt(12)

    results = []
    # Track year-by-year values for all simulations
    yearly_balances = [[] for _ in range(years + 1)]  # +1 to include starting year

    for _ in range(runs):
        balance = current_savings
        current_monthly_contribution = monthly_contribution

        # Record starting balance
        yearly_balances[0].append(balance)

        for month in range(months):
            # Generate random monthly return from normal distribution
            random_return = np.random.normal(monthly_rate, monthly_std)

            # Apply return and add contribution
            balance = balance * (1 + random_return) + current_monthly_contribution

            # Increase contribution annually and record yearly balance
            if (month + 1) % 12 == 0:
                year_index = (month + 1) // 12
                yearly_balances[year_index].append(balance)

                if contribution_growth_rate > 0:
                    current_monthly_contribution *= (1 + contribution_growth_rate)

        results.append(balance)

    # Convert to numpy array for statistical calculations
    outcomes = np.array(results)

    # Calculate year-by-year percentiles for charting
    yearly_10th = []
    yearly_50th = []
    yearly_90th = []
    year_labels = list(range(years + 1))  # 0, 1, 2, ..., years

    for year_balances in yearly_balances:
        year_array = np.array(year_balances)
        yearly_10th.append(float(np.percentile(year_array, 10)))
        yearly_50th.append(float(np.percentile(year_array, 50)))
        yearly_90th.append(float(np.percentile(year_array, 90)))

    return MonteCarloResults(
        mean=Decimal(str(np.mean(outcomes))),
        median=Decimal(str(np.median(outcomes))),
        percentile_10=Decimal(str(np.percentile(outcomes, 10))),
        percentile_25=Decimal(str(np.percentile(outcomes, 25))),
        percentile_50=Decimal(str(np.percentile(outcomes, 50))),
        percentile_75=Decimal(str(np.percentile(outcomes, 75))),
        percentile_90=Decimal(str(np.percentile(outcomes, 90))),
        std_deviation=Decimal(str(np.std(outcomes))),
        success_rate=Decimal('100.0'),  # All outcomes succeed in accumulation
        all_outcomes=[float(x) for x in outcomes],  # For charting
        yearly_10th=yearly_10th,
        yearly_50th=yearly_50th,
        yearly_90th=yearly_90th,
        years=year_labels
    )


def run_withdrawal_monte_carlo(
    starting_portfolio: float,
    annual_withdrawal: float,
    years: int,
    expected_return: float,  # Annual return as percentage
    variance: float,  # Annual standard deviation as percentage
    inflation_rate: float = 3.0,  # Annual inflation as percentage
    runs: int = 10000
) -> MonteCarloResults:
    """
    Run Monte Carlo simulation for withdrawal/retirement phase.

    Uses MONTHLY compounding to match the deterministic calculation approach.

    Args:
        starting_portfolio: Initial portfolio value
        annual_withdrawal: Annual withdrawal amount (inflation-adjusted)
        years: Number of years to simulate
        expected_return: Expected annual return (%)
        variance: Annual volatility/standard deviation (%)
        inflation_rate: Annual inflation rate (%)
        runs: Number of simulation runs

    Returns:
        MonteCarloResults with success rate (% not depleted)
    """
    months = years * 12

    # Convert percentages to decimals
    annual_rate = expected_return / 100
    annual_std = variance / 100
    annual_inflation = inflation_rate / 100

    # Convert to monthly
    monthly_rate = annual_rate / 12
    monthly_std = annual_std / np.sqrt(12)
    monthly_inflation = annual_inflation / 12
    monthly_withdrawal = annual_withdrawal / 12

    results = []
    successes = 0  # Count simulations where portfolio doesn't deplete
    # Track year-by-year values for all simulations
    yearly_balances = [[] for _ in range(years + 1)]  # +1 to include starting year

    for _ in range(runs):
        balance = starting_portfolio
        current_withdrawal = monthly_withdrawal
        depleted = False

        # Record starting balance
        yearly_balances[0].append(balance)

        for month in range(months):
            # Adjust withdrawal for inflation annually
            if month > 0 and month % 12 == 0:
                current_withdrawal *= (1 + annual_inflation)

            # Generate random monthly return
            random_return = np.random.normal(monthly_rate, monthly_std)

            # Apply return FIRST (matching deterministic approach)
            balance = balance * (1 + random_return)

            # THEN subtract withdrawal
            balance = balance - current_withdrawal

            # Check if depleted
            if balance <= 0:
                depleted = True
                balance = 0

            # Record yearly balance
            if (month + 1) % 12 == 0:
                year_index = (month + 1) // 12
                yearly_balances[year_index].append(balance)

            # Break early if depleted
            if depleted and (month + 1) % 12 == 0:
                # Fill remaining years with 0 for this simulation
                for remaining_year in range(year_index + 1, years + 1):
                    yearly_balances[remaining_year].append(0)
                break

        results.append(balance)
        if not depleted:
            successes += 1

    # Convert to numpy array for statistical calculations
    outcomes = np.array(results)
    success_rate = (successes / runs) * 100

    # Calculate year-by-year percentiles for charting
    yearly_10th = []
    yearly_50th = []
    yearly_90th = []
    year_labels = list(range(years + 1))  # 0, 1, 2, ..., years

    for year_balances in yearly_balances:
        year_array = np.array(year_balances)
        yearly_10th.append(float(np.percentile(year_array, 10)))
        yearly_50th.append(float(np.percentile(year_array, 50)))
        yearly_90th.append(float(np.percentile(year_array, 90)))

    return MonteCarloResults(
        mean=Decimal(str(np.mean(outcomes))),
        median=Decimal(str(np.median(outcomes))),
        percentile_10=Decimal(str(np.percentile(outcomes, 10))),
        percentile_25=Decimal(str(np.percentile(outcomes, 25))),
        percentile_50=Decimal(str(np.percentile(outcomes, 50))),
        percentile_75=Decimal(str(np.percentile(outcomes, 75))),
        percentile_90=Decimal(str(np.percentile(outcomes, 90))),
        std_deviation=Decimal(str(np.std(outcomes))),
        success_rate=Decimal(str(success_rate)),
        all_outcomes=[float(x) for x in outcomes],
        yearly_10th=yearly_10th,
        yearly_50th=yearly_50th,
        yearly_90th=yearly_90th,
        years=year_labels
    )
