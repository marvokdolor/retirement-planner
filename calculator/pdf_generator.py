"""
PDF Report Generation for Retirement Scenarios.

This module generates professional PDF reports using ReportLab.
"""
from io import BytesIO
from datetime import datetime
from decimal import Decimal

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Import calculation functions to recompute results
from calculator.phase_calculator import (
    calculate_accumulation_phase,
    calculate_phased_retirement_phase,
    calculate_active_retirement_phase,
    calculate_late_retirement_phase,
)


def currency_format(value):
    """Format value as currency string."""
    if value is None:
        return "$0"
    if isinstance(value, (int, float, Decimal)):
        return f"${value:,.0f}"
    return str(value)


def generate_retirement_pdf(scenario, include_charts=False):
    """
    Generate a comprehensive PDF report for a retirement scenario.

    Args:
        scenario: Scenario model instance with all phase data
        include_charts: Boolean - whether to include Monte Carlo charts

    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),  # blue-900
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=12,
        spaceBefore=24,
    )
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#3b82f6'),  # blue-600
        spaceAfter=10,
        spaceBefore=16,
    )
    body_style = styles['BodyText']
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b7280'),  # gray-500
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    # Title Page
    elements.append(Paragraph(scenario.name, title_style))
    elements.append(Paragraph("Comprehensive Retirement Plan Analysis", styles['Heading3']))
    elements.append(Spacer(1, 0.5*inch))

    # Generated date
    generated_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    elements.append(Paragraph(f"Generated: {generated_date}", body_style))
    elements.append(Spacer(1, 0.3*inch))

    # Executive Summary
    elements.append(Paragraph("Executive Summary", heading_style))

    # Calculate all phases to get results
    phase_results = {}
    scenario_data = scenario.data

    # Phase 1: Accumulation
    if 'phase1' in scenario_data:
        try:
            phase1_data = scenario_data['phase1']
            phase_results['phase1'] = calculate_accumulation_phase(
                current_age=int(phase1_data.get('current_age', 30)),
                retirement_start_age=int(phase1_data.get('retirement_start_age', 65)),
                current_savings=float(phase1_data.get('current_savings', 0)),
                monthly_contribution=float(phase1_data.get('monthly_contribution', 0)),
                employer_match_rate=float(phase1_data.get('employer_match_rate', 0)),
                expected_return=float(phase1_data.get('expected_return', 7)),
                annual_salary_increase=float(phase1_data.get('annual_salary_increase', 0)),
            )
        except (KeyError, ValueError, TypeError):
            pass

    # Create summary table
    summary_data = []
    summary_data.append(['Metric', 'Value'])

    if 'phase1' in phase_results:
        summary_data.append([
            'Future Value at Retirement',
            currency_format(phase_results['phase1'].get('future_value'))
        ])
        summary_data.append([
            'Years to Retirement',
            f"{phase_results['phase1'].get('years_to_retirement', 0)} years"
        ])

    summary_table = Table(summary_data, colWidths=[3.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)
    elements.append(PageBreak())

    # Detailed Phase Results
    elements.append(Paragraph("Detailed Phase Analysis", heading_style))
    elements.append(Spacer(1, 0.2*inch))

    # Phase 1: Accumulation
    if 'phase1' in phase_results:
        elements.append(Paragraph("Phase 1: Accumulation (Pre-Retirement)", subheading_style))
        result = phase_results['phase1']

        phase1_data = [
            ['Metric', 'Value'],
            ['Current Age', f"{scenario_data['phase1'].get('current_age', 'N/A')} years"],
            ['Planned Retirement Age', f"{scenario_data['phase1'].get('retirement_start_age', 'N/A')} years"],
            ['Years to Retirement', f"{result.get('years_to_retirement', 0)} years"],
            ['Current Savings', currency_format(scenario_data['phase1'].get('current_savings'))],
            ['Monthly Contribution', currency_format(scenario_data['phase1'].get('monthly_contribution'))],
            ['Expected Return', f"{scenario_data['phase1'].get('expected_return', 0)}%"],
            ['', ''],  # Spacer row
            ['Total Personal Contributions', currency_format(result.get('total_personal_contributions'))],
            ['Total Employer Match', currency_format(result.get('total_employer_contributions'))],
            ['Investment Gains', currency_format(result.get('investment_gains'))],
            ['Future Value', currency_format(result.get('future_value'))],
        ]

        phase1_table = Table(phase1_data, colWidths=[3.5*inch, 2.5*inch])
        phase1_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -4), (-1, -1), 'Helvetica-Bold'),  # Bold final results
            ('BACKGROUND', (0, -4), (-1, -1), colors.HexColor('#dbeafe')),  # Light blue for results
        ]))
        elements.append(phase1_table)
        elements.append(Spacer(1, 0.3*inch))

    # Assumptions Section
    elements.append(PageBreak())
    elements.append(Paragraph("Planning Assumptions", heading_style))
    elements.append(Spacer(1, 0.1*inch))

    assumptions_text = """
    This retirement plan is based on the following key assumptions and inputs provided by you:
    """
    elements.append(Paragraph(assumptions_text, body_style))
    elements.append(Spacer(1, 0.1*inch))

    # Create assumptions table
    if 'phase1' in scenario_data:
        assumptions_data = [
            ['Assumption', 'Value'],
            ['Expected Annual Return', f"{scenario_data['phase1'].get('expected_return', 0)}%"],
            ['Annual Salary Increase', f"{scenario_data['phase1'].get('annual_salary_increase', 0)}%"],
            ['Inflation Rate (assumed)', "3.0%"],
        ]

        assumptions_table = Table(assumptions_data, colWidths=[3.5*inch, 2.5*inch])
        assumptions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(assumptions_table)

    # Disclaimer
    elements.append(PageBreak())
    elements.append(Paragraph("Important Disclaimers", heading_style))
    elements.append(Spacer(1, 0.2*inch))

    disclaimer_text = """
    <b>This tool provides estimates only and is not financial advice.</b><br/>
    <br/>
    The projections and calculations in this report are based on the assumptions and inputs you provided.
    Actual results will vary based on market performance, inflation, tax rates, and other factors beyond
    our control. This analysis does not constitute financial, investment, tax, or legal advice.<br/>
    <br/>
    <b>Please consult a qualified financial advisor for personalized guidance on your retirement planning needs.</b><br/>
    <br/>
    Past performance does not guarantee future results. All investments involve risk, including the potential
    loss of principal. Market returns are unpredictable and can be negative in any given year.<br/>
    <br/>
    This report was generated by an automated system based on mathematical models. While we strive for accuracy,
    we make no warranties about the completeness or reliability of this information.
    """
    elements.append(Paragraph(disclaimer_text, body_style))

    # Methodology
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("Methodology", heading_style))
    elements.append(Spacer(1, 0.1*inch))

    methodology_text = """
    <b>Accumulation Phase Calculations:</b><br/>
    The accumulation phase uses compound interest calculations with monthly contributions.
    Investment gains are calculated using geometric compounding, and employer matches are added
    to your monthly contributions. Annual salary increases are applied to contributions each year.<br/>
    <br/>
    <b>Monte Carlo Simulations:</b><br/>
    If included, Monte Carlo simulations run 10,000 scenarios using randomly generated returns based on
    your expected return and volatility inputs. This provides a probabilistic range of outcomes rather
    than a single deterministic projection.
    """
    elements.append(Paragraph(methodology_text, body_style))

    # Footer on every page
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        f"Retirement Planner - {datetime.now().year} - Generated with Django & ReportLab",
        disclaimer_style
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
