"""
Tests for Monte Carlo simulation functions.
"""

from decimal import Decimal
from django.test import TestCase
from calculator.monte_carlo import (
    run_accumulation_monte_carlo,
    run_withdrawal_monte_carlo,
    MonteCarloResults
)


class AccumulationMonteCarloTests(TestCase):
    """Tests for accumulation phase Monte Carlo simulation."""

    def test_basic_accumulation_returns_results(self):
        """Test that basic accumulation simulation returns MonteCarloResults."""
        results = run_accumulation_monte_carlo(
            current_savings=50000,
            monthly_contribution=1000,
            years=10,
            expected_return=7.0,
            variance=2.0,
            runs=100  # Small runs for fast testing
        )

        self.assertIsInstance(results, MonteCarloResults)
        self.assertIsInstance(results.mean, Decimal)
        self.assertIsInstance(results.median, Decimal)
        self.assertIsInstance(results.success_rate, Decimal)

    def test_percentile_ordering(self):
        """Test that percentiles are in correct order (10th < 25th < 50th < 75th < 90th)."""
        results = run_accumulation_monte_carlo(
            current_savings=50000,
            monthly_contribution=1000,
            years=10,
            expected_return=7.0,
            variance=2.0,
            runs=1000
        )

        self.assertLess(results.percentile_10, results.percentile_25)
        self.assertLess(results.percentile_25, results.percentile_50)
        self.assertLess(results.percentile_50, results.percentile_75)
        self.assertLess(results.percentile_75, results.percentile_90)

    def test_median_equals_50th_percentile(self):
        """Test that median equals 50th percentile."""
        results = run_accumulation_monte_carlo(
            current_savings=50000,
            monthly_contribution=1000,
            years=10,
            expected_return=7.0,
            variance=2.0,
            runs=1000
        )

        self.assertEqual(results.median, results.percentile_50)

    def test_accumulation_success_rate_is_100_percent(self):
        """Test that accumulation phase always has 100% success rate."""
        results = run_accumulation_monte_carlo(
            current_savings=10000,
            monthly_contribution=500,
            years=5,
            expected_return=6.0,
            variance=3.0,
            runs=100
        )

        self.assertEqual(results.success_rate, Decimal('100.0'))

    def test_zero_contribution_with_savings(self):
        """Test simulation with zero monthly contribution but existing savings."""
        results = run_accumulation_monte_carlo(
            current_savings=100000,
            monthly_contribution=0,
            years=10,
            expected_return=5.0,
            variance=2.0,
            runs=100
        )

        # Should still have positive outcomes from growth
        self.assertGreater(results.median, Decimal('100000'))

    def test_zero_savings_with_contributions(self):
        """Test simulation with zero starting savings but monthly contributions."""
        results = run_accumulation_monte_carlo(
            current_savings=0,
            monthly_contribution=1000,
            years=10,
            expected_return=7.0,
            variance=2.0,
            runs=100
        )

        # Should accumulate value from contributions
        self.assertGreater(results.median, Decimal('0'))

    def test_higher_variance_increases_spread(self):
        """Test that higher variance leads to wider spread in outcomes."""
        low_variance_results = run_accumulation_monte_carlo(
            current_savings=50000,
            monthly_contribution=1000,
            years=10,
            expected_return=7.0,
            variance=1.0,
            runs=1000
        )

        high_variance_results = run_accumulation_monte_carlo(
            current_savings=50000,
            monthly_contribution=1000,
            years=10,
            expected_return=7.0,
            variance=5.0,
            runs=1000
        )

        # Higher variance should have larger standard deviation
        self.assertGreater(high_variance_results.std_deviation, low_variance_results.std_deviation)

    def test_all_outcomes_count_matches_runs(self):
        """Test that all_outcomes list has correct number of entries."""
        runs = 500
        results = run_accumulation_monte_carlo(
            current_savings=50000,
            monthly_contribution=1000,
            years=10,
            expected_return=7.0,
            variance=2.0,
            runs=runs
        )

        self.assertEqual(len(results.all_outcomes), runs)

    def test_longer_time_period_increases_outcomes(self):
        """Test that longer time periods generally result in higher outcomes."""
        short_period_results = run_accumulation_monte_carlo(
            current_savings=50000,
            monthly_contribution=1000,
            years=5,
            expected_return=7.0,
            variance=2.0,
            runs=500
        )

        long_period_results = run_accumulation_monte_carlo(
            current_savings=50000,
            monthly_contribution=1000,
            years=20,
            expected_return=7.0,
            variance=2.0,
            runs=500
        )

        self.assertGreater(long_period_results.median, short_period_results.median)


class WithdrawalMonteCarloTests(TestCase):
    """Tests for withdrawal/retirement phase Monte Carlo simulation."""

    def test_basic_withdrawal_returns_results(self):
        """Test that basic withdrawal simulation returns MonteCarloResults."""
        results = run_withdrawal_monte_carlo(
            starting_portfolio=1000000,
            annual_withdrawal=40000,
            years=30,
            expected_return=5.0,
            variance=2.0,
            inflation_rate=3.0,
            runs=100
        )

        self.assertIsInstance(results, MonteCarloResults)
        self.assertIsInstance(results.mean, Decimal)
        self.assertIsInstance(results.median, Decimal)
        self.assertIsInstance(results.success_rate, Decimal)

    def test_withdrawal_percentile_ordering(self):
        """Test that percentiles are in correct order."""
        results = run_withdrawal_monte_carlo(
            starting_portfolio=1000000,
            annual_withdrawal=40000,
            years=30,
            expected_return=5.0,
            variance=2.0,
            runs=1000
        )

        self.assertLessEqual(results.percentile_10, results.percentile_25)
        self.assertLessEqual(results.percentile_25, results.percentile_50)
        self.assertLessEqual(results.percentile_50, results.percentile_75)
        self.assertLessEqual(results.percentile_75, results.percentile_90)

    def test_success_rate_between_0_and_100(self):
        """Test that success rate is between 0 and 100 percent."""
        results = run_withdrawal_monte_carlo(
            starting_portfolio=500000,
            annual_withdrawal=50000,
            years=30,
            expected_return=5.0,
            variance=3.0,
            runs=500
        )

        self.assertGreaterEqual(results.success_rate, Decimal('0'))
        self.assertLessEqual(results.success_rate, Decimal('100'))

    def test_low_withdrawal_high_success_rate(self):
        """Test that low withdrawal rates result in high success rates."""
        results = run_withdrawal_monte_carlo(
            starting_portfolio=1000000,
            annual_withdrawal=20000,  # 2% withdrawal rate
            years=30,
            expected_return=7.0,
            variance=2.0,
            runs=500
        )

        # Should have very high success rate (>95%)
        self.assertGreater(results.success_rate, Decimal('95'))

    def test_high_withdrawal_low_success_rate(self):
        """Test that high withdrawal rates result in lower success rates."""
        results = run_withdrawal_monte_carlo(
            starting_portfolio=500000,
            annual_withdrawal=80000,  # 16% withdrawal rate (very high)
            years=30,
            expected_return=5.0,
            variance=2.0,
            runs=500
        )

        # Should have lower success rate
        self.assertLess(results.success_rate, Decimal('50'))

    def test_inflation_adjustment_affects_outcomes(self):
        """Test that inflation rate affects withdrawal outcomes."""
        no_inflation_results = run_withdrawal_monte_carlo(
            starting_portfolio=1000000,
            annual_withdrawal=40000,
            years=30,
            expected_return=5.0,
            variance=2.0,
            inflation_rate=0.0,
            runs=500
        )

        high_inflation_results = run_withdrawal_monte_carlo(
            starting_portfolio=1000000,
            annual_withdrawal=40000,
            years=30,
            expected_return=5.0,
            variance=2.0,
            inflation_rate=5.0,
            runs=500
        )

        # Higher inflation should result in lower success rate
        self.assertGreater(no_inflation_results.success_rate, high_inflation_results.success_rate)

    def test_all_outcomes_count_matches_runs(self):
        """Test that all_outcomes list has correct number of entries."""
        runs = 300
        results = run_withdrawal_monte_carlo(
            starting_portfolio=1000000,
            annual_withdrawal=40000,
            years=30,
            expected_return=5.0,
            variance=2.0,
            runs=runs
        )

        self.assertEqual(len(results.all_outcomes), runs)

    def test_zero_withdrawal_preserves_portfolio(self):
        """Test that zero withdrawal results in portfolio growth."""
        results = run_withdrawal_monte_carlo(
            starting_portfolio=1000000,
            annual_withdrawal=0,
            years=10,
            expected_return=5.0,
            variance=2.0,
            runs=100
        )

        # Should have 100% success rate and portfolio should grow
        self.assertEqual(results.success_rate, Decimal('100'))
        self.assertGreater(results.median, Decimal('1000000'))

    def test_depleted_portfolios_show_zero_balance(self):
        """Test that depleted scenarios are counted as zero in outcomes."""
        results = run_withdrawal_monte_carlo(
            starting_portfolio=100000,
            annual_withdrawal=50000,  # Very high withdrawal rate
            years=30,
            expected_return=3.0,
            variance=2.0,
            runs=500
        )

        # Should have many zeros in outcomes (depleted portfolios)
        zero_count = sum(1 for outcome in results.all_outcomes if outcome == 0)
        self.assertGreater(zero_count, 0)

    def test_higher_returns_increase_success_rate(self):
        """Test that higher expected returns lead to higher success rates."""
        low_return_results = run_withdrawal_monte_carlo(
            starting_portfolio=1000000,
            annual_withdrawal=50000,
            years=30,
            expected_return=3.0,
            variance=2.0,
            runs=500
        )

        high_return_results = run_withdrawal_monte_carlo(
            starting_portfolio=1000000,
            annual_withdrawal=50000,
            years=30,
            expected_return=8.0,
            variance=2.0,
            runs=500
        )

        self.assertGreater(high_return_results.success_rate, low_return_results.success_rate)
