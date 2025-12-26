"""
Tests for PDF report generation functionality.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from calculator.models import Scenario
import io
from PyPDF2 import PdfReader

User = get_user_model()


class PDFReportGenerationTests(TestCase):
    """Test PDF report generation functionality."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')

        # Create a test scenario with complete data
        self.scenario = Scenario.objects.create(
            user=self.user,
            name="Test Retirement Plan",
            data={
                'phase1': {
                    'current_age': 30,
                    'retirement_start_age': 60,
                    'current_savings': 50000,
                    'monthly_contribution': 1500,
                    'expected_return': 7.5,
                },
                'phase2': {
                    'phase_start_age': 60,
                    'full_retirement_age': 67,
                    'annual_withdrawal': 20000,
                },
                'phase3': {
                    'active_retirement_start_age': 67,
                    'active_retirement_end_age': 80,
                    'annual_withdrawal': 50000,
                },
                'phase4': {
                    'late_retirement_start_age': 80,
                    'life_expectancy': 90,
                    'annual_withdrawal': 40000,
                }
            }
        )

    def test_pdf_generation_url_exists(self):
        """Test that PDF generation URL is accessible."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:generate_pdf_report', kwargs={'scenario_id': self.scenario.id})
        response = self.client.get(url)
        # Should return PDF or redirect (not 404)
        self.assertIn(response.status_code, [200, 302])

    def test_pdf_generation_requires_authentication(self):
        """Test that PDF generation requires user to be logged in."""
        url = reverse('calculator:generate_pdf_report', kwargs={'scenario_id': self.scenario.id})
        response = self.client.get(url)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_pdf_generation_creates_valid_pdf(self):
        """Test that generated PDF is valid and can be read."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:generate_pdf_report', kwargs={'scenario_id': self.scenario.id})
        response = self.client.get(url)

        # Should return PDF
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        # Should have proper filename
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.pdf', response['Content-Disposition'])

        # PDF should be valid and readable
        pdf_content = io.BytesIO(response.content)
        pdf_reader = PdfReader(pdf_content)
        self.assertGreater(len(pdf_reader.pages), 0, "PDF should have at least one page")

    def test_pdf_contains_scenario_name(self):
        """Test that PDF contains the scenario name."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:generate_pdf_report', kwargs={'scenario_id': self.scenario.id})
        response = self.client.get(url)

        # Extract text from first page
        pdf_content = io.BytesIO(response.content)
        pdf_reader = PdfReader(pdf_content)
        first_page_text = pdf_reader.pages[0].extract_text()

        # Should contain scenario name
        self.assertIn("Test Retirement Plan", first_page_text)

    def test_pdf_contains_disclaimer(self):
        """Test that PDF includes disclaimer text."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:generate_pdf_report', kwargs={'scenario_id': self.scenario.id})
        response = self.client.get(url)

        # Extract all text from PDF
        pdf_content = io.BytesIO(response.content)
        pdf_reader = PdfReader(pdf_content)
        all_text = ""
        for page in pdf_reader.pages:
            all_text += page.extract_text()

        # Should contain disclaimer
        self.assertIn("not financial advice", all_text.lower())

    def test_pdf_contains_phase_results(self):
        """Test that PDF contains results for all phases."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:generate_pdf_report', kwargs={'scenario_id': self.scenario.id})
        response = self.client.get(url)

        # Extract all text from PDF
        pdf_content = io.BytesIO(response.content)
        pdf_reader = PdfReader(pdf_content)
        all_text = ""
        for page in pdf_reader.pages:
            all_text += page.extract_text()

        # Should contain phase names or indicators
        self.assertIn("Phase 1", all_text) or self.assertIn("Accumulation", all_text)

    def test_pdf_generation_from_calculator_page(self):
        """Test that PDF can be generated directly from calculator page."""
        self.client.login(username='testuser', password='testpass123')
        # POST to generate PDF with current calculator state
        url = reverse('calculator:generate_pdf_from_current')
        response = self.client.post(url, {
            'current_age': 30,
            'retirement_start_age': 60,
            'current_savings': 50000,
        })

        # Should return PDF or success response
        self.assertIn(response.status_code, [200, 302])

    def test_pdf_with_monte_carlo_checkbox_enabled(self):
        """Test PDF generation automatically includes Monte Carlo charts."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('calculator:generate_pdf_report', kwargs={'scenario_id': self.scenario.id})
        response = self.client.get(url)

        # Should return PDF
        self.assertEqual(response.status_code, 200)
        # PDF with charts should be of reasonable size
        self.assertGreater(len(response.content), 5000)  # Reasonable minimum size

    def test_pdf_user_can_only_access_own_scenarios(self):
        """Test that users can only generate PDFs for their own scenarios."""
        # Create another user and their scenario
        other_user = User.objects.create_user(username='otheruser', password='testpass123')
        other_scenario = Scenario.objects.create(
            user=other_user,
            name="Other User's Plan",
            data={'phase1': {'current_age': 25}}
        )

        # Login as first user
        self.client.login(username='testuser', password='testpass123')

        # Try to access other user's scenario
        url = reverse('calculator:generate_pdf_report', kwargs={'scenario_id': other_scenario.id})
        response = self.client.get(url)

        # Should be forbidden or not found
        self.assertIn(response.status_code, [403, 404])
