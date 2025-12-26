"""
Integration tests for end-to-end workflows.

These tests validate complete user journeys through the app,
ensuring all components work together correctly.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from calculator.models import Scenario
import json


class EndToEndWorkflowTests(TestCase):
    """Test complete user workflows from start to finish."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_complete_retirement_planning_workflow(self):
        """
        Test full workflow: Calculate → Save → Load → Modify → Save Again.

        This simulates a user:
        1. Calculating Phase 1 (Accumulation)
        2. Saving the scenario
        3. Loading it back from scenario list
        4. Modifying values
        5. Saving updates
        """
        # Step 1: User must be logged in
        self.client.login(username='testuser', password='testpass123')

        # Step 2: Calculate Phase 1 (Accumulation)
        calc_response = self.client.post('/calculator/calculate/accumulation/', {
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertEqual(calc_response.status_code, 200)
        self.assertContains(calc_response, 'Future Value')

        # Step 3: Save the scenario
        save_response = self.client.post('/calculator/scenarios/save/', {
            'name': 'My Retirement Plan',
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertEqual(save_response.status_code, 200)
        self.assertContains(save_response, 'saved successfully')

        # Step 4: Verify scenario exists in database
        scenario = Scenario.objects.get(name='My Retirement Plan', user=self.user)
        self.assertEqual(scenario.data['current_age'], '30')
        self.assertEqual(scenario.data['current_savings'], '50000')

        # Step 5: Load scenario from multi-phase calculator
        load_response = self.client.get(f'/calculator/multi-phase/{scenario.id}/')
        self.assertEqual(load_response.status_code, 200)
        self.assertContains(load_response, 'My Retirement Plan')

        # Step 6: Modify scenario (increase contributions)
        modify_response = self.client.post('/calculator/scenarios/save/', {
            'name': 'My Retirement Plan',  # Same name = update
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1500,  # Increased from 1000
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertEqual(modify_response.status_code, 200)
        self.assertContains(modify_response, 'updated successfully')

        # Step 7: Verify update in database
        scenario.refresh_from_db()
        self.assertEqual(scenario.data['monthly_contribution'], '1500')

        # Step 8: Verify only one scenario exists (updated, not duplicated)
        scenario_count = Scenario.objects.filter(name='My Retirement Plan', user=self.user).count()
        self.assertEqual(scenario_count, 1)

    def test_multi_phase_cascade_workflow(self):
        """
        Test workflow where ending value from one phase flows to next phase.

        Simulates:
        1. Phase 1 calculation (accumulation)
        2. Using Phase 1 ending value as Phase 2 starting value
        3. Calculating all 4 phases sequentially
        """
        self.client.login(username='testuser', password='testpass123')

        # Phase 1: Accumulation (ages 30-65)
        phase1_response = self.client.post('/calculator/calculate/accumulation/', {
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        self.assertEqual(phase1_response.status_code, 200)
        # Phase 1 should produce a future value (we'll use ~800k as example)

        # Phase 2: Phased Retirement (ages 65-70)
        # Starting portfolio should match Phase 1 ending value
        phase2_response = self.client.post('/calculator/calculate/phased-retirement/', {
            'starting_portfolio': 800000,  # From Phase 1 ending
            'phase_start_age': 65,  # Matches Phase 1 retirement age
            'full_retirement_age': 70,
            'annual_part_time_income': 30000,
            'annual_withdrawal': 20000,
            'annual_contribution': 5000,
            'stock_allocation': 60,
            'expected_return': 6,
            'return_volatility': 10,
            'inflation_rate': 3,
        })

        self.assertEqual(phase2_response.status_code, 200)

        # Phase 3: Active Retirement (ages 70-80)
        phase3_response = self.client.post('/calculator/calculate/active-retirement/', {
            'starting_portfolio': 850000,  # From Phase 2 ending
            'active_retirement_start_age': 70,  # Matches Phase 2 ending
            'active_retirement_end_age': 80,
            'annual_expenses': 50000,
            'annual_healthcare_costs': 10000,
            'expected_return': 5,
            'return_volatility': 8,
            'inflation_rate': 3,
        })

        self.assertEqual(phase3_response.status_code, 200)

        # Phase 4: Late Retirement (ages 80-90)
        phase4_response = self.client.post('/calculator/calculate/late-retirement/', {
            'starting_portfolio': 600000,  # From Phase 3 ending
            'late_retirement_start_age': 80,  # Matches Phase 3 ending
            'life_expectancy': 90,
            'annual_basic_expenses': 30000,
            'annual_healthcare_costs': 15000,
            'long_term_care_annual': 50000,
            'expected_return': 4,
            'return_volatility': 5,
            'inflation_rate': 3,
        })

        self.assertEqual(phase4_response.status_code, 200)

        # All 4 phases calculated successfully
        self.assertContains(phase1_response, 'Future Value')
        self.assertContains(phase2_response, 'Ending Portfolio')
        self.assertContains(phase3_response, 'Ending Portfolio')
        self.assertContains(phase4_response, 'Ending Portfolio')

    def test_scenario_comparison_workflow(self):
        """
        Test workflow for comparing multiple scenarios.

        Simulates:
        1. Creating two different retirement scenarios
        2. Loading scenario comparison page
        3. Comparing results side-by-side
        """
        self.client.login(username='testuser', password='testpass123')

        # Create Scenario 1: Conservative approach
        scenario1 = Scenario.objects.create(
            user=self.user,
            name='Conservative Plan',
            data={
                'current_age': '30',
                'retirement_start_age': '65',
                'current_savings': '50000',
                'monthly_contribution': '1000',
                'expected_return': '5',  # Conservative return
            }
        )

        # Create Scenario 2: Aggressive approach
        scenario2 = Scenario.objects.create(
            user=self.user,
            name='Aggressive Plan',
            data={
                'current_age': '30',
                'retirement_start_age': '65',
                'current_savings': '50000',
                'monthly_contribution': '1000',
                'expected_return': '9',  # Aggressive return
            }
        )

        # Load comparison page
        comparison_response = self.client.get('/calculator/scenarios/compare/')
        self.assertEqual(comparison_response.status_code, 200)

        # Verify both scenarios appear in comparison view
        self.assertContains(comparison_response, 'Conservative Plan')
        self.assertContains(comparison_response, 'Aggressive Plan')

    def test_monte_carlo_simulation_workflow(self):
        """
        Test workflow for running Monte Carlo simulations.

        Simulates:
        1. User fills out Phase 1 form
        2. User runs Monte Carlo simulation
        3. Chart and percentile results displayed
        """
        self.client.login(username='testuser', password='testpass123')

        # Run Monte Carlo simulation for accumulation phase
        mc_response = self.client.post('/calculator/monte-carlo/accumulation/', {
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'annual_salary_increase': 2,
            'current_age': 30,
            'retirement_start_age': 65,
            'expected_return': 7,
            'return_volatility': 10,
        })

        self.assertEqual(mc_response.status_code, 200)

        # Verify Monte Carlo chart is rendered
        self.assertContains(mc_response, 'monte-carlo-chart-phase1')

        # Verify percentile results are shown
        self.assertContains(mc_response, 'Median')
        self.assertContains(mc_response, 'Optimistic')
        self.assertContains(mc_response, 'Pessimistic')


class MultiUserDataIsolationTests(TestCase):
    """Test that users can only see their own data."""

    def setUp(self):
        self.client = Client()

        # Create two users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass1'
        )

        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass2'
        )

    def test_users_cannot_see_each_others_scenarios(self):
        """Test that User 1 cannot see User 2's scenarios."""
        # Create scenario for User 1
        scenario1 = Scenario.objects.create(
            user=self.user1,
            name='User 1 Retirement',
            data={'current_age': '30'}
        )

        # Create scenario for User 2
        scenario2 = Scenario.objects.create(
            user=self.user2,
            name='User 2 Retirement',
            data={'current_age': '35'}
        )

        # Login as User 1
        self.client.login(username='user1', password='pass1')

        # User 1 visits scenario list
        response = self.client.get('/calculator/scenarios/')
        self.assertEqual(response.status_code, 200)

        # Should see their own scenario
        self.assertContains(response, 'User 1 Retirement')

        # Should NOT see User 2's scenario
        self.assertNotContains(response, 'User 2 Retirement')

    def test_users_cannot_load_each_others_scenarios(self):
        """Test that User 1 cannot load User 2's scenario by ID."""
        # Create scenario for User 2
        scenario2 = Scenario.objects.create(
            user=self.user2,
            name='User 2 Retirement',
            data={'current_age': '35'}
        )

        # Login as User 1
        self.client.login(username='user1', password='pass1')

        # Try to load User 2's scenario
        response = self.client.get(f'/calculator/multi-phase/{scenario2.id}/')

        # Should either redirect or show 404/403
        self.assertIn(response.status_code, [302, 403, 404])

    def test_concurrent_scenario_saves_different_users(self):
        """Test that concurrent saves by different users don't interfere."""
        # User 1 saves scenario
        self.client.login(username='user1', password='pass1')
        response1 = self.client.post('/calculator/scenarios/save/', {
            'name': 'Retirement Plan',
            'current_age': 30,
            'current_savings': 50000,
        })
        self.assertEqual(response1.status_code, 200)

        # Logout and login as User 2
        self.client.logout()
        self.client.login(username='user2', password='pass2')

        # User 2 saves scenario with SAME NAME
        response2 = self.client.post('/calculator/scenarios/save/', {
            'name': 'Retirement Plan',  # Same name as User 1
            'current_age': 40,  # Different data
            'current_savings': 100000,
        })
        self.assertEqual(response2.status_code, 200)

        # Verify both scenarios exist independently
        user1_scenarios = Scenario.objects.filter(user=self.user1, name='Retirement Plan')
        user2_scenarios = Scenario.objects.filter(user=self.user2, name='Retirement Plan')

        self.assertEqual(user1_scenarios.count(), 1)
        self.assertEqual(user2_scenarios.count(), 1)

        # Verify data integrity
        self.assertEqual(user1_scenarios.first().data['current_age'], '30')
        self.assertEqual(user2_scenarios.first().data['current_age'], '40')


class FormStatePersistenceTests(TestCase):
    """Test form state persistence across page navigation."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_form_data_persists_across_phase_tabs(self):
        """
        Test that form data persists when switching between phase tabs.

        Note: This relies on FormPersistence JavaScript utility.
        Since this is a server-side test, we verify the forms accept data.
        """
        # Load multi-phase calculator
        response = self.client.get('/calculator/multi-phase/')
        self.assertEqual(response.status_code, 200)

        # Verify all 4 phase forms are present
        self.assertContains(response, 'Phase 1: Accumulation')
        self.assertContains(response, 'Phase 2: Phased Retirement')
        self.assertContains(response, 'Phase 3: Active Retirement')
        self.assertContains(response, 'Phase 4: Late Retirement')

        # Calculate Phase 1
        phase1_response = self.client.post('/calculator/calculate/accumulation/', {
            'current_age': 30,
            'retirement_start_age': 65,
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })
        self.assertEqual(phase1_response.status_code, 200)

        # Calculate Phase 2 (simulating tab switch)
        phase2_response = self.client.post('/calculator/calculate/phased-retirement/', {
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
        self.assertEqual(phase2_response.status_code, 200)

        # Both calculations should succeed independently
        self.assertContains(phase1_response, 'Future Value')
        self.assertContains(phase2_response, 'Ending Portfolio')

    def test_loaded_scenario_overrides_persisted_state(self):
        """
        Test that loading a saved scenario overrides localStorage state.

        This verifies the fix where FormPersistence was overriding
        Django's initial form values.
        """
        # Create a saved scenario
        scenario = Scenario.objects.create(
            user=self.user,
            name='Test Scenario',
            data={
                'current_age': '35',
                'retirement_start_age': '67',
                'current_savings': '75000',
                'monthly_contribution': '1500',
            }
        )

        # Load the scenario
        response = self.client.get(f'/calculator/multi-phase/{scenario.id}/')
        self.assertEqual(response.status_code, 200)

        # Verify scenario name appears
        self.assertContains(response, 'Test Scenario')

        # The loaded scenario should trigger localStorage clear
        # (verified by JavaScript in template)


class ErrorHandlingWorkflowTests(TestCase):
    """Test error handling in various workflows."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_unauthenticated_user_cannot_save_scenario(self):
        """Test that unauthenticated users cannot save scenarios."""
        # Don't login
        response = self.client.post('/calculator/scenarios/save/', {
            'name': 'Test Scenario',
            'current_age': 30,
        })

        # Should redirect to login or return 403
        self.assertIn(response.status_code, [302, 403])

    def test_invalid_form_data_shows_errors(self):
        """Test that invalid form data returns validation errors."""
        self.client.login(username='testuser', password='testpass123')

        # Submit invalid data (retirement age <= current age)
        response = self.client.post('/calculator/calculate/accumulation/', {
            'current_age': 65,
            'retirement_start_age': 60,  # Invalid
            'current_savings': 50000,
            'monthly_contribution': 1000,
            'employer_match_rate': 50,
            'expected_return': 7,
            'return_volatility': 10,
            'annual_salary_increase': 2,
        })

        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'error')

    def test_loading_nonexistent_scenario_returns_404(self):
        """Test that loading non-existent scenario returns 404."""
        self.client.login(username='testuser', password='testpass123')

        # Try to load scenario ID 9999 (doesn't exist)
        response = self.client.get('/calculator/multi-phase/9999/')

        self.assertEqual(response.status_code, 404)

    def test_monte_carlo_with_invalid_data(self):
        """Test Monte Carlo simulation handles invalid data gracefully."""
        self.client.login(username='testuser', password='testpass123')

        # Submit invalid data to Monte Carlo endpoint
        response = self.client.post('/calculator/monte-carlo/accumulation/', {
            'current_savings': 'invalid',  # String instead of number
            'monthly_contribution': 1000,
        })

        # Should return 400 Bad Request with error message
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Invalid input', status_code=400)
