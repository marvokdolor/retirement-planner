"""
PDF Report Generation for Retirement Scenarios.

This module generates professional PDF reports using ReportLab.
Monte Carlo charts are automatically included when phase data is available.
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

# Import Monte Carlo simulation
from calculator.monte_carlo import run_accumulation_monte_carlo, run_withdrawal_monte_carlo

# Import plotly for chart generation
import plotly.graph_objects as go


def currency_format(value):
    """Format value as currency string."""
    if value is None or value == '':
        return "$0"

    # Handle string values (from saved scenarios)
    if isinstance(value, str):
        try:
            value = float(value)
        except (ValueError, TypeError):
            return "$0"

    # Format numeric values
    if isinstance(value, (int, float, Decimal)):
        return f"${value:,.0f}"

    return "$0"


def _generate_monte_carlo_chart_image(phase_data, phase_name="Accumulation"):
    """
    Generate Monte Carlo chart as an image for PDF inclusion.

    Args:
        phase_data: Dictionary with phase input data
        phase_name: Name of the phase for chart title

    Returns:
        Image object for ReportLab, or None if chart cannot be generated
    """
    try:
        # Extract required parameters
        current_savings = float(phase_data.get('current_savings', 0))
        monthly_contribution = float(phase_data.get('monthly_contribution', 0))
        employer_match_rate = float(phase_data.get('employer_match_rate', 0))
        annual_salary_increase = float(phase_data.get('annual_salary_increase', 0))

        current_age = int(phase_data.get('current_age', 0))
        retirement_start_age = int(phase_data.get('retirement_start_age', 0))
        years_to_retirement = max(0, retirement_start_age - current_age)

        expected_return = float(phase_data.get('expected_return', 7))
        variance = float(phase_data.get('return_volatility', 10))

        # Can't generate chart without sufficient data
        if years_to_retirement <= 0:
            return None

        # Apply employer match to monthly contribution
        employer_match = monthly_contribution * (employer_match_rate / 100)
        total_monthly_contribution = monthly_contribution + employer_match

        # Run Monte Carlo simulation
        results = run_accumulation_monte_carlo(
            current_savings=current_savings,
            monthly_contribution=total_monthly_contribution,
            years=years_to_retirement,
            expected_return=expected_return,
            variance=variance,
            runs=10000,
            annual_contribution_increase=annual_salary_increase
        )

        # Create Plotly figure
        fig = go.Figure()

        # Create x-axis labels with ages
        x_labels = [current_age + year for year in results.years]

        # Add 90th percentile line (optimistic)
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=results.yearly_90th,
            mode='lines',
            name='Optimistic (90th percentile)',
            line=dict(color='#10b981', width=2),
        ))

        # Add 50th percentile line (median)
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=results.yearly_50th,
            mode='lines',
            name='Median (50th percentile)',
            line=dict(color='#3b82f6', width=3),
        ))

        # Add 10th percentile line (pessimistic)
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=results.yearly_10th,
            mode='lines',
            name='Pessimistic (10th percentile)',
            line=dict(color='#ef4444', width=2),
        ))

        # Update layout
        fig.update_layout(
            title=dict(text=f"Monte Carlo Projections - {phase_name}", x=0.5, xanchor='center'),
            xaxis_title="Age",
            yaxis_title="Portfolio Value",
            template='plotly_white',
            width=700,
            height=400,
            margin=dict(l=60, r=30, t=60, b=50),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5
            )
        )

        # Format y-axis as currency
        fig.update_yaxes(tickformat='$,.0f')

        # Convert to image
        img_bytes = fig.to_image(format="png")

        # Create ReportLab Image
        from PIL import Image as PILImage
        from io import BytesIO as ImgBuffer

        img_buffer = ImgBuffer(img_bytes)
        img = Image(img_buffer, width=6*inch, height=3.5*inch)

        return img

    except Exception as e:
        # If anything goes wrong, just skip the chart
        import sys
        print(f"Could not generate Monte Carlo chart: {e}", file=sys.stderr)
        return None


def _generate_withdrawal_monte_carlo_chart(phase_data, phase_name="Retirement", start_age=65):
    """
    Generate Monte Carlo chart for withdrawal phases (2, 3, 4).

    Args:
        phase_data: Dictionary with phase input data
        phase_name: Name of the phase for chart title
        start_age: Starting age for this phase

    Returns:
        Image object for ReportLab, or None if chart cannot be generated
    """
    try:
        # Extract parameters
        starting_portfolio = float(phase_data.get('starting_portfolio', 0))
        annual_withdrawal = float(phase_data.get('annual_withdrawal', 0))
        expected_return = float(phase_data.get('expected_return', 7))
        variance = float(phase_data.get('return_volatility', 10))
        inflation_rate = float(phase_data.get('inflation_rate', 3))

        # Determine phase duration based on which phase this is
        if 'phase_start_age' in phase_data and 'full_retirement_age' in phase_data:
            # Phase 2
            years = int(phase_data['full_retirement_age']) - int(phase_data['phase_start_age'])
        elif 'active_retirement_start_age' in phase_data and 'active_retirement_end_age' in phase_data:
            # Phase 3
            years = int(phase_data['active_retirement_end_age']) - int(phase_data['active_retirement_start_age'])
        elif 'late_retirement_start_age' in phase_data and 'life_expectancy' in phase_data:
            # Phase 4
            years = int(phase_data['life_expectancy']) - int(phase_data['late_retirement_start_age'])
        else:
            return None

        if years <= 0 or starting_portfolio <= 0:
            return None

        # Run withdrawal Monte Carlo simulation
        results = run_withdrawal_monte_carlo(
            starting_portfolio=starting_portfolio,
            annual_withdrawal=annual_withdrawal,
            years=years,
            expected_return=expected_return,
            variance=variance,
            inflation_rate=inflation_rate,
            runs=10000
        )

        # Create Plotly figure
        fig = go.Figure()

        # Create x-axis labels with ages
        x_labels = [start_age + year for year in results.years]

        # Add 90th percentile line (optimistic)
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=results.yearly_90th,
            mode='lines',
            name='Optimistic (90th percentile)',
            line=dict(color='#10b981', width=2),
        ))

        # Add 50th percentile line (median)
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=results.yearly_50th,
            mode='lines',
            name='Median (50th percentile)',
            line=dict(color='#3b82f6', width=3),
        ))

        # Add 10th percentile line (pessimistic)
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=results.yearly_10th,
            mode='lines',
            name='Pessimistic (10th percentile)',
            line=dict(color='#ef4444', width=2),
        ))

        # Update layout
        fig.update_layout(
            title=dict(text=f"Monte Carlo Projections - {phase_name}", x=0.5, xanchor='center'),
            xaxis_title="Age",
            yaxis_title="Portfolio Value",
            template='plotly_white',
            width=700,
            height=400,
            margin=dict(l=60, r=30, t=60, b=50),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5
            )
        )

        # Format y-axis as currency
        fig.update_yaxes(tickformat='$,.0f')

        # Convert to image
        img_bytes = fig.to_image(format="png")

        # Create ReportLab Image
        from PIL import Image as PILImage
        from io import BytesIO as ImgBuffer

        img_buffer = ImgBuffer(img_bytes)
        img = Image(img_buffer, width=6*inch, height=3.5*inch)

        return img

    except Exception as e:
        # If anything goes wrong, just skip the chart
        import sys
        print(f"Could not generate withdrawal Monte Carlo chart for {phase_name}: {e}", file=sys.stderr)
        return None


def generate_retirement_pdf(scenario):
    """
    Generate a comprehensive PDF report for a retirement scenario.

    Automatically includes Monte Carlo simulation charts if the scenario
    has sufficient phase data.

    Args:
        scenario: Scenario model instance with all phase data

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

    # Calculate all phases to get results
    phase_results = {}
    scenario_data = scenario.data

    # Phase 1: Accumulation
    # Handle both nested (phase1: {...}) and flat data structures
    phase1_data = scenario_data.get('phase1', scenario_data)
    if 'current_age' in phase1_data and 'retirement_start_age' in phase1_data:
        try:
            # The phase calculator expects a dictionary, not individual arguments
            phase_results['phase1'] = calculate_accumulation_phase(phase1_data)
        except (KeyError, ValueError, TypeError) as e:
            # Log error for debugging but continue
            import sys
            print(f"Error calculating Phase 1: {e}", file=sys.stderr)
            pass

    # Detailed Phase Results
    elements.append(Paragraph("Retirement Plan Details", heading_style))
    elements.append(Spacer(1, 0.2*inch))

    # Phase 1: Accumulation
    if 'phase1' in phase_results:
        elements.append(Paragraph("Phase 1: Accumulation (Pre-Retirement)", subheading_style))
        result = phase_results['phase1']

        # Use the same phase1_data variable we created earlier (handles both nested and flat)
        input_data = scenario_data.get('phase1', scenario_data)

        phase1_table_data = [
            ['Metric', 'Value'],
            ['Current Age', f"{input_data.get('current_age', 'N/A')} years"],
            ['Planned Retirement Age', f"{input_data.get('retirement_start_age', 'N/A')} years"],
            ['Years to Retirement', f"{result.years_to_retirement} years"],
            ['Current Savings', currency_format(input_data.get('current_savings'))],
            ['Monthly Contribution', currency_format(input_data.get('monthly_contribution'))],
            ['Expected Return', f"{input_data.get('expected_return', 0)}%"],
            ['', ''],  # Spacer row
            ['Total Personal Contributions', currency_format(result.total_personal_contributions)],
            ['Total Employer Match', currency_format(result.total_employer_contributions)],
            ['Investment Gains', currency_format(result.investment_gains)],
            ['Future Value', currency_format(result.future_value)],
        ]

        phase1_table = Table(phase1_table_data, colWidths=[3.5*inch, 2.5*inch])
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

        # Try to add Monte Carlo chart for Phase 1
        monte_carlo_chart = _generate_monte_carlo_chart_image(input_data, "Accumulation Phase")
        if monte_carlo_chart:
            elements.append(PageBreak())
            elements.append(Paragraph("Monte Carlo Simulation - Accumulation Phase", subheading_style))
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph(
                "This chart shows the range of possible outcomes based on 10,000 simulated scenarios. "
                "The blue line represents the median outcome, while the green and red lines show "
                "optimistic (90th percentile) and pessimistic (10th percentile) scenarios.",
                body_style
            ))
            elements.append(Spacer(1, 0.2*inch))
            elements.append(monte_carlo_chart)
            elements.append(Spacer(1, 0.3*inch))

    # Phase 2: Phased Retirement
    # Handle both nested (phase2: {...}) and flat data structures
    phase2_data = scenario_data.get('phase2', scenario_data)
    if 'phase_start_age' in phase2_data:
        try:
            # Convert string values to appropriate types for calculation
            phase2_calc_data = {
                'phase_start_age': int(phase2_data['phase_start_age']),
                'full_retirement_age': int(phase2_data['full_retirement_age']),
                'starting_portfolio': phase2_data.get('starting_portfolio', 0),
                'monthly_contribution': phase2_data.get('monthly_contribution', 0),
                'annual_withdrawal': phase2_data.get('annual_withdrawal', 0),
                'part_time_income': phase2_data.get('part_time_income', 0),
                'expected_return': phase2_data.get('expected_return', 7),
            }
            phase_results['phase2'] = calculate_phased_retirement_phase(phase2_calc_data)
            elements.append(PageBreak())
            elements.append(Paragraph("Phase 2: Phased Retirement (Semi-Retirement)", subheading_style))
            result = phase_results['phase2']

            phase2_table_data = [
                ['Metric', 'Value'],
                ['Phase Start Age', f"{phase2_data.get('phase_start_age', 'N/A')} years"],
                ['Full Retirement Age', f"{phase2_data.get('full_retirement_age', 'N/A')} years"],
                ['Phase Duration', f"{result.phase_duration_years} years"],
                ['Starting Portfolio', currency_format(phase2_data.get('starting_portfolio'))],
                ['Annual Withdrawal', currency_format(phase2_data.get('annual_withdrawal'))],
                ['Part-Time Income', currency_format(phase2_data.get('part_time_income', 0))],
                ['', ''],  # Spacer row
                ['Ending Portfolio Value', currency_format(result.ending_portfolio)],
            ]

            phase2_table = Table(phase2_table_data, colWidths=[3.5*inch, 2.5*inch])
            phase2_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
            ]))
            elements.append(phase2_table)
            elements.append(Spacer(1, 0.3*inch))

            # Try to add Monte Carlo chart for Phase 2
            monte_carlo_chart = _generate_withdrawal_monte_carlo_chart(
                phase2_data,
                "Phased Retirement",
                start_age=int(phase2_data['phase_start_age'])
            )
            if monte_carlo_chart:
                elements.append(Paragraph("Monte Carlo Simulation - Phased Retirement", subheading_style))
                elements.append(Spacer(1, 0.2*inch))
                elements.append(Paragraph(
                    "This chart shows the range of possible outcomes during your semi-retirement phase. "
                    "The simulation accounts for market volatility and inflation-adjusted withdrawals.",
                    body_style
                ))
                elements.append(Spacer(1, 0.2*inch))
                elements.append(monte_carlo_chart)
                elements.append(Spacer(1, 0.3*inch))

        except (KeyError, ValueError, TypeError) as e:
            import sys
            print(f"Error calculating Phase 2: {e}", file=sys.stderr)

    # Phase 3: Active Retirement
    # Handle both nested (phase3: {...}) and flat data structures
    phase3_data = scenario_data.get('phase3', scenario_data)
    if 'active_retirement_start_age' in phase3_data:
        try:
            # Convert string values to appropriate types for calculation
            phase3_calc_data = {
                'active_retirement_start_age': int(phase3_data['active_retirement_start_age']),
                'active_retirement_end_age': int(phase3_data['active_retirement_end_age']),
                'starting_portfolio': phase3_data.get('starting_portfolio', 0),
                'annual_expenses': phase3_data.get('annual_expenses', 0),
                'annual_healthcare_costs': phase3_data.get('annual_healthcare_costs', 0),
                'expected_return': phase3_data.get('expected_return', 7),
                'inflation_rate': phase3_data.get('inflation_rate', 3),
            }
            phase_results['phase3'] = calculate_active_retirement_phase(phase3_calc_data)
            elements.append(PageBreak())
            elements.append(Paragraph("Phase 3: Active Retirement (Early Retirement Years)", subheading_style))
            result = phase_results['phase3']

            phase3_table_data = [
                ['Metric', 'Value'],
                ['Phase Start Age', f"{phase3_data.get('active_retirement_start_age', 'N/A')} years"],
                ['Phase End Age', f"{phase3_data.get('active_retirement_end_age', 'N/A')} years"],
                ['Phase Duration', f"{result.phase_duration_years} years"],
                ['Starting Portfolio', currency_format(phase3_data.get('starting_portfolio'))],
                ['Annual Expenses', currency_format(phase3_data.get('annual_expenses'))],
                ['Annual Healthcare Costs', currency_format(phase3_data.get('annual_healthcare_costs'))],
                ['', ''],  # Spacer row
                ['Ending Portfolio Value', currency_format(result.ending_portfolio)],
            ]

            phase3_table = Table(phase3_table_data, colWidths=[3.5*inch, 2.5*inch])
            phase3_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
            ]))
            elements.append(phase3_table)
            elements.append(Spacer(1, 0.3*inch))

            # Try to add Monte Carlo chart for Phase 3
            monte_carlo_chart = _generate_withdrawal_monte_carlo_chart(
                phase3_data,
                "Active Retirement",
                start_age=int(phase3_data['active_retirement_start_age'])
            )
            if monte_carlo_chart:
                elements.append(Paragraph("Monte Carlo Simulation - Active Retirement", subheading_style))
                elements.append(Spacer(1, 0.2*inch))
                elements.append(Paragraph(
                    "This chart shows portfolio projections during your active retirement years. "
                    "The simulation models market volatility and inflation-adjusted expense needs.",
                    body_style
                ))
                elements.append(Spacer(1, 0.2*inch))
                elements.append(monte_carlo_chart)
                elements.append(Spacer(1, 0.3*inch))

        except (KeyError, ValueError, TypeError) as e:
            import sys
            print(f"Error calculating Phase 3: {e}", file=sys.stderr)

    # Phase 4: Late Retirement
    # Handle both nested (phase4: {...}) and flat data structures
    phase4_data = scenario_data.get('phase4', scenario_data)
    if 'late_retirement_start_age' in phase4_data:
        try:
            # Convert string values to appropriate types for calculation
            phase4_calc_data = {
                'late_retirement_start_age': int(phase4_data['late_retirement_start_age']),
                'life_expectancy': int(phase4_data['life_expectancy']),
                'starting_portfolio': phase4_data.get('starting_portfolio', 0),
                'annual_basic_expenses': phase4_data.get('annual_basic_expenses', 0),
                'annual_healthcare_costs': phase4_data.get('annual_healthcare_costs', 0),
                'expected_return': phase4_data.get('expected_return', 7),
                'inflation_rate': phase4_data.get('inflation_rate', 3),
            }
            phase_results['phase4'] = calculate_late_retirement_phase(phase4_calc_data)
            elements.append(PageBreak())
            elements.append(Paragraph("Phase 4: Late Retirement (Legacy & Healthcare)", subheading_style))
            result = phase_results['phase4']

            phase4_table_data = [
                ['Metric', 'Value'],
                ['Phase Start Age', f"{phase4_data.get('late_retirement_start_age', 'N/A')} years"],
                ['Life Expectancy', f"{phase4_data.get('life_expectancy', 'N/A')} years"],
                ['Phase Duration', f"{result.phase_duration_years} years"],
                ['Starting Portfolio', currency_format(phase4_data.get('starting_portfolio'))],
                ['Annual Basic Expenses', currency_format(phase4_data.get('annual_basic_expenses'))],
                ['Annual Healthcare Costs', currency_format(phase4_data.get('annual_healthcare_costs'))],
                ['', ''],  # Spacer row
                ['Ending Portfolio Value', currency_format(result.ending_portfolio)],
                ['Estate/Legacy', currency_format(result.ending_portfolio)],
            ]

            phase4_table = Table(phase4_table_data, colWidths=[3.5*inch, 2.5*inch])
            phase4_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#dbeafe')),
            ]))
            elements.append(phase4_table)
            elements.append(Spacer(1, 0.3*inch))

            # Try to add Monte Carlo chart for Phase 4
            monte_carlo_chart = _generate_withdrawal_monte_carlo_chart(
                phase4_data,
                "Late Retirement",
                start_age=int(phase4_data['late_retirement_start_age'])
            )
            if monte_carlo_chart:
                elements.append(Paragraph("Monte Carlo Simulation - Late Retirement", subheading_style))
                elements.append(Spacer(1, 0.2*inch))
                elements.append(Paragraph(
                    "This chart projects your portfolio through your final retirement years. "
                    "The simulation includes healthcare costs, inflation, and market variability to help plan for legacy goals.",
                    body_style
                ))
                elements.append(Spacer(1, 0.2*inch))
                elements.append(monte_carlo_chart)
                elements.append(Spacer(1, 0.3*inch))

        except (KeyError, ValueError, TypeError) as e:
            import sys
            print(f"Error calculating Phase 4: {e}", file=sys.stderr)

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
    Monte Carlo simulations run 10,000 scenarios using randomly generated returns based on
    your expected return and volatility inputs. This provides a probabilistic range of outcomes rather
    than a single deterministic projection. The simulations account for market volatility and help
    visualize the range of possible outcomes for your retirement plan.
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
