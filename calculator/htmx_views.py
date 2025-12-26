"""
HTMX-specific views for dynamic, partial page updates.

These views return HTML fragments instead of full pages.
Includes views for all four retirement phases.

Uses django-htmx's request.htmx to detect HTMX requests and return
appropriate templates (partials for HTMX, full pages for direct access).
"""

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
import plotly.graph_objects as go
from .forms import RetirementCalculatorForm, ScenarioNameForm
from .calculator import calculate_retirement_savings
from .phase_forms import (
    AccumulationPhaseForm,
    PhasedRetirementForm,
    ActiveRetirementForm,
    LateRetirementForm
)
from .phase_calculator import (
    calculate_accumulation_phase,
    calculate_phased_retirement_phase,
    calculate_active_retirement_phase,
    calculate_late_retirement_phase
)
from .monte_carlo import (
    run_accumulation_monte_carlo,
    run_withdrawal_monte_carlo
)
from .models import Scenario


# ===== SHARED HELPER =====

def _process_phase_calculation(request, form_class, calculator_func, results_template):
    """
    Shared helper for processing phase calculations.

    This reduces code duplication across all phase views.

    Args:
        request: Django request object
        form_class: Form class to use for validation
        calculator_func: Calculator function to call with cleaned data
        results_template: Template path for results partial

    Returns:
        HttpResponse with results or errors HTML fragment
    """
    if request.method != 'POST':
        return HttpResponse('<div class="text-gray-500">Invalid request method</div>')

    form = form_class(request.POST)

    if form.is_valid():
        # Calculate results using the provided calculator function
        results = calculator_func(form.cleaned_data)

        # Return results partial
        return render(request, results_template, {'results': results})
    else:
        # Return validation errors
        return render(request, 'calculator/partials/form_errors.html', {'form': form})


# ===== ORIGINAL SIMPLE CALCULATOR (BACKWARDS COMPATIBILITY) =====

def calculate_htmx(request):
    """
    HTMX endpoint: Original simple retirement calculator.

    Detects HTMX requests using request.htmx and returns appropriate template:
    - HTMX request: Returns partial HTML fragment
    - Regular request: Returns full page (fallback for direct access)
    """
    if request.method == 'POST':
        form = RetirementCalculatorForm(request.POST)

        if form.is_valid():
            results = calculate_retirement_savings(
                current_age=form.cleaned_data['current_age'],
                retirement_age=form.cleaned_data['retirement_age'],
                current_savings=form.cleaned_data['current_savings'],
                monthly_contribution=form.cleaned_data['monthly_contribution'],
                annual_return_rate=form.cleaned_data['expected_return'],
                variance=form.cleaned_data.get('variance')
            )

            # Use request.htmx to detect HTMX requests
            if request.htmx:
                # Return partial for HTMX request
                return render(request, 'calculator/partials/results.html', {'results': results})
            else:
                # Return full page for regular POST (fallback)
                return render(request, 'calculator/retirement_calculator.html', {
                    'form': form,
                    'results': results
                })
        else:
            # Return validation errors
            if request.htmx:
                return render(request, 'calculator/partials/form_errors.html', {'form': form})
            else:
                return render(request, 'calculator/retirement_calculator.html', {'form': form})

    return HttpResponse('<div class="text-gray-500">Invalid request</div>')


# ===== PHASE 1: ACCUMULATION =====

def calculate_accumulation(request):
    """
    HTMX endpoint: Calculate Phase 1 - Accumulation.

    Building wealth during working years with contributions and employer match.
    """
    return _process_phase_calculation(
        request,
        AccumulationPhaseForm,
        calculate_accumulation_phase,
        'calculator/partials/accumulation_results.html'
    )


# ===== PHASE 2: PHASED RETIREMENT =====

def calculate_phased_retirement(request):
    """
    HTMX endpoint: Calculate Phase 2 - Phased Retirement.

    Semi-retired with optional part-time income and contributions.
    """
    return _process_phase_calculation(
        request,
        PhasedRetirementForm,
        calculate_phased_retirement_phase,
        'calculator/partials/phased_retirement_results.html'
    )


# ===== PHASE 3: ACTIVE RETIREMENT =====

def calculate_active_retirement(request):
    """
    HTMX endpoint: Calculate Phase 3 - Active Retirement.

    Early retirement years with active lifestyle and moderate healthcare costs.
    """
    return _process_phase_calculation(
        request,
        ActiveRetirementForm,
        calculate_active_retirement_phase,
        'calculator/partials/active_retirement_results.html'
    )


# ===== PHASE 4: LATE RETIREMENT =====

def calculate_late_retirement(request):
    """
    HTMX endpoint: Calculate Phase 4 - Late Retirement.

    Final years with high healthcare and long-term care costs.
    """
    return _process_phase_calculation(
        request,
        LateRetirementForm,
        calculate_late_retirement_phase,
        'calculator/partials/late_retirement_results.html'
    )


# ===== SCENARIO MANAGEMENT =====

@login_required
def save_scenario(request):
    """
    HTMX endpoint: Save current calculator state as a scenario.

    Captures all form data from the multi-phase calculator and saves as JSON.
    """
    if request.method != 'POST':
        return HttpResponse('<div class="text-red-500">Invalid request method</div>')

    form = ScenarioNameForm(request.POST)

    if form.is_valid():
        scenario_name = form.cleaned_data['name']

        # Check if a scenario with this name already exists for this user
        existing_scenario = Scenario.objects.filter(user=request.user, name=scenario_name).first()

        if existing_scenario:
            # Update existing scenario instead of creating a new one
            scenario = existing_scenario
            action = "updated"
        else:
            # Create new scenario
            scenario = form.save(commit=False)
            scenario.user = request.user
            action = "saved"

        # Capture all form data organized by phase
        data = {
            'phase1': {},
            'phase2': {},
            'phase3': {},
            'phase4': {}
        }

        # Parse phase-prefixed parameters from JavaScript
        for key, value in request.POST.items():
            if key not in ['csrfmiddlewaretoken', 'name']:
                # Check if key has phase prefix
                if key.startswith('phase1_'):
                    field_name = key[7:]  # Remove 'phase1_' prefix
                    data['phase1'][field_name] = value
                elif key.startswith('phase2_'):
                    field_name = key[7:]  # Remove 'phase2_' prefix
                    data['phase2'][field_name] = value
                elif key.startswith('phase3_'):
                    field_name = key[7:]  # Remove 'phase3_' prefix
                    data['phase3'][field_name] = value
                elif key.startswith('phase4_'):
                    field_name = key[7:]  # Remove 'phase4_' prefix
                    data['phase4'][field_name] = value

        scenario.data = data
        scenario.save()

        # Return success message
        return HttpResponse(f'''
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                ✓ Scenario "{scenario.name}" {action} successfully!
                <a href="/calculator/scenarios/" class="underline ml-2">View all scenarios</a>
            </div>
        ''')
    else:
        # Return error message
        errors = '<br>'.join([f'{field}: {error}' for field, error in form.errors.items()])
        return HttpResponse(f'<div class="text-red-500">{errors}</div>')


# ===== MONTE CARLO SIMULATIONS =====

def _create_trajectory_chart(years, yearly_10th, yearly_50th, yearly_90th, title="Portfolio Growth Projections", starting_age=None, chart_id="monte-carlo-chart"):
    """
    Create a Plotly line chart showing 3 trajectory lines (10th, 50th, 90th percentiles).

    Args:
        years: List of year indices (0, 1, 2, ...)
        yearly_10th: 10th percentile values by year
        yearly_50th: 50th percentile (median) values by year
        yearly_90th: 90th percentile values by year
        title: Chart title
        starting_age: Optional starting age to display ages on x-axis instead of years
        chart_id: Unique ID for the chart div (important when multiple charts on same page)

    Returns HTML div containing the interactive chart.
    """
    fig = go.Figure()

    # Create x-axis labels (ages if provided, otherwise years)
    if starting_age is not None:
        x_labels = [starting_age + year for year in years]
        x_axis_title = "Age"
        hover_label = "Age"
    else:
        x_labels = years
        x_axis_title = "Years from Now"
        hover_label = "Year"

    # Add 90th percentile line (optimistic)
    fig.add_trace(go.Scatter(
        x=x_labels,
        y=yearly_90th,
        mode='lines',
        name='Optimistic (90th percentile)',
        line=dict(color='#10b981', width=2),  # green
        hovertemplate=f'{hover_label} %{{x}}<br>$%{{y:,.0f}}<extra></extra>'
    ))

    # Add 50th percentile line (median)
    fig.add_trace(go.Scatter(
        x=x_labels,
        y=yearly_50th,
        mode='lines',
        name='Median (50th percentile)',
        line=dict(color='#3b82f6', width=3),  # blue, thicker
        hovertemplate=f'{hover_label} %{{x}}<br>$%{{y:,.0f}}<extra></extra>'
    ))

    # Add 10th percentile line (pessimistic)
    fig.add_trace(go.Scatter(
        x=x_labels,
        y=yearly_10th,
        mode='lines',
        name='Pessimistic (10th percentile)',
        line=dict(color='#ef4444', width=2),  # red
        hovertemplate=f'{hover_label} %{{x}}<br>$%{{y:,.0f}}<extra></extra>'
    ))

    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=16)),
        xaxis_title=x_axis_title,
        yaxis_title="Portfolio Value",
        hovermode='x unified',
        template='plotly_white',
        height=450,
        margin=dict(l=60, r=30, t=80, b=50),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1
        ),
        font=dict(size=12)
    )

    # Format y-axis as currency
    fig.update_yaxes(tickformat='$,.0f')

    # Return HTML div - Plotly is already loaded in base template, so don't include it again
    return fig.to_html(include_plotlyjs=False, div_id=chart_id, config={'displayModeBar': False})


@require_POST
def monte_carlo_accumulation(request):
    """
    HTMX endpoint: Run Monte Carlo simulation for accumulation phase.

    Returns probabilistic projections showing range of possible outcomes.
    """
    try:
        # Extract and validate parameters
        current_savings = float(request.POST.get('current_savings', 0))
        monthly_contribution = float(request.POST.get('monthly_contribution', 0))
        employer_match_rate = float(request.POST.get('employer_match_rate', 0))
        annual_salary_increase = float(request.POST.get('annual_salary_increase', 0))

        # Calculate years from ages (form uses current_age and retirement_start_age)
        current_age = int(request.POST.get('current_age', 0))
        retirement_start_age = int(request.POST.get('retirement_start_age', 0))
        years_to_retirement = max(0, retirement_start_age - current_age)

        expected_return = float(request.POST.get('expected_return', 0))
        # Use user-specified volatility, default to 10% (moderate)
        variance = float(request.POST.get('return_volatility', 10.0))

        # Apply employer match to monthly contribution for simulation
        # This gives us the total monthly inflow
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

        # Generate trajectory chart
        chart_html = _create_trajectory_chart(
            years=results.years,
            yearly_10th=results.yearly_10th,
            yearly_50th=results.yearly_50th,
            yearly_90th=results.yearly_90th,
            title="Portfolio Growth Projections",
            starting_age=current_age,
            chart_id="monte-carlo-chart-phase1"
        )

        # Return results partial
        return render(request, 'calculator/partials/monte_carlo_accumulation.html', {
            'results': results,
            'chart_html': chart_html
        })

    except (ValueError, TypeError, KeyError) as e:
        return HttpResponse(
            '<div class="text-red-500">Invalid input data. Please check your values.</div>',
            status=400
        )


@require_POST
def monte_carlo_withdrawal(request):
    """
    HTMX endpoint: Run Monte Carlo simulation for withdrawal phase.

    Returns success rate and range of ending portfolio values.
    """
    try:
        # Extract and validate parameters
        starting_portfolio = float(request.POST.get('starting_portfolio', 0))

        # Calculate annual withdrawal from different possible field combinations
        annual_withdrawal = 0
        if request.POST.get('annual_withdrawal'):
            # Simple withdrawal form (Phase 2, simple calculator)
            annual_withdrawal = float(request.POST.get('annual_withdrawal', 0))
        else:
            # Phase 3/4: Sum of expenses + healthcare (+ LTC if present)
            annual_expenses = float(request.POST.get('annual_expenses', 0))
            annual_healthcare = float(request.POST.get('annual_healthcare_costs', 0))
            annual_basic_expenses = float(request.POST.get('annual_basic_expenses', 0))
            long_term_care = float(request.POST.get('long_term_care_annual', 0))

            # Phase 3 uses annual_expenses + annual_healthcare_costs
            # Phase 4 uses annual_basic_expenses + annual_healthcare_costs + long_term_care_annual
            annual_withdrawal = annual_expenses + annual_healthcare + annual_basic_expenses + long_term_care

        # Calculate years from age fields (different forms have different field names)
        years = 0
        start_age = None
        chart_id = "monte-carlo-chart-withdrawal"  # Default

        if request.POST.get('years'):
            years = int(request.POST.get('years'))
        elif request.POST.get('active_retirement_start_age') and request.POST.get('active_retirement_end_age'):
            # Phase 3: Active Retirement
            start_age = int(request.POST.get('active_retirement_start_age', 0))
            end_age = int(request.POST.get('active_retirement_end_age', 0))
            years = max(0, end_age - start_age)
            chart_id = "monte-carlo-chart-phase3"
        elif request.POST.get('late_retirement_start_age') and request.POST.get('life_expectancy'):
            # Phase 4: Late Retirement
            start_age = int(request.POST.get('late_retirement_start_age', 0))
            life_expectancy = int(request.POST.get('life_expectancy', 0))
            years = max(0, life_expectancy - start_age)
            chart_id = "monte-carlo-chart-phase4"
        elif request.POST.get('phase_start_age') and request.POST.get('full_retirement_age'):
            # Phase 2: Phased Retirement
            start_age = int(request.POST.get('phase_start_age', 0))
            end_age = int(request.POST.get('full_retirement_age', 0))
            years = max(0, end_age - start_age)
            chart_id = "monte-carlo-chart-phase2"

        expected_return = float(request.POST.get('expected_return', 0))
        # Use user-specified volatility, default to 10% (moderate)
        variance = float(request.POST.get('return_volatility', 10.0))
        inflation_rate = float(request.POST.get('inflation_rate', 3.0))

        # Run Monte Carlo simulation
        results = run_withdrawal_monte_carlo(
            starting_portfolio=starting_portfolio,
            annual_withdrawal=annual_withdrawal,
            years=years,
            expected_return=expected_return,
            variance=variance,
            inflation_rate=inflation_rate,
            runs=10000
        )

        # Generate trajectory chart
        chart_html = _create_trajectory_chart(
            years=results.years,
            yearly_10th=results.yearly_10th,
            yearly_50th=results.yearly_50th,
            yearly_90th=results.yearly_90th,
            title="Portfolio Withdrawal Projections",
            starting_age=start_age,
            chart_id=chart_id
        )

        # Return results partial
        return render(request, 'calculator/partials/monte_carlo_withdrawal.html', {
            'results': results,
            'chart_html': chart_html
        })

    except (ValueError, TypeError, KeyError) as e:
        return HttpResponse(
            '<div class="text-red-500">Invalid input data. Please check your values.</div>',
            status=400
        )

# ===== WHAT-IF SCENARIO ANALYSIS =====

@login_required
def what_if_calculate(request):
    """
    HTMX endpoint for live what-if scenario calculations.

    Compares adjusted inputs against base scenario and shows delta/difference.
    Used by what-if comparison page for real-time updates as user adjusts values.

    POST parameters:
        base_scenario_id: ID of the base scenario
        phase: Which phase to calculate ('phase1', 'phase2', etc.)
        ...all phase-specific input fields...

    Returns:
        HTML partial with calculated results and delta comparison
    """
    from .models import Scenario
    from .phase_calculator import (
        calculate_accumulation_phase,
        calculate_phased_retirement_phase,
        calculate_active_retirement_phase,
        calculate_late_retirement_phase
    )

    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)

    # Get base scenario
    base_scenario_id = request.POST.get('base_scenario_id')
    if not base_scenario_id:
        return HttpResponse('<div class="text-red-500 p-4 bg-red-50 border border-red-200 rounded">Error: No base scenario specified</div>')

    try:
        base_scenario = Scenario.objects.get(id=base_scenario_id, user=request.user)
    except Scenario.DoesNotExist:
        return HttpResponse('<div class="text-red-500 p-4 bg-red-50 border border-red-200 rounded">Error: Scenario not found</div>')

    # Get which phase to calculate
    phase = request.POST.get('phase', 'phase1')

    # Map phase to calculation function and form
    phase_calculators = {
        'phase1': (calculate_accumulation_phase, AccumulationPhaseForm),
        'phase2': (calculate_phased_retirement_phase, PhasedRetirementForm),
        'phase3': (calculate_active_retirement_phase, ActiveRetirementForm),
        'phase4': (calculate_late_retirement_phase, LateRetirementForm),
    }

    if phase not in phase_calculators:
        return HttpResponse('<div class="text-red-500 p-4 bg-red-50 border border-red-200 rounded">Error: Invalid phase</div>')

    calculator_func, form_class = phase_calculators[phase]

    # Validate form data
    form = form_class(request.POST)
    if not form.is_valid():
        errors = '<br>'.join([f'{field}: {", ".join(errs)}' for field, errs in form.errors.items()])
        return HttpResponse(f'<div class="text-red-500 p-4 bg-red-50 border border-red-200 rounded"><strong>Validation errors:</strong><br>{errors}</div>')

    try:
        # Calculate what-if results
        what_if_results = calculator_func(form.cleaned_data)

        # Calculate base scenario results for comparison
        # Handle both nested (phase1, phase2) and flat data structures
        scenario_data = base_scenario.data
        base_data = {}

        if phase in scenario_data:
            # Nested format
            base_data = scenario_data[phase]
        else:
            # Flat format - extract relevant fields for this phase
            if phase == 'phase1':
                phase1_fields = ['current_age', 'retirement_start_age', 'current_savings', 'monthly_contribution',
                                'employer_match_rate', 'annual_salary_increase', 'stock_allocation',
                                'expected_return', 'inflation_rate', 'return_volatility']
                base_data = {k: scenario_data[k] for k in phase1_fields if k in scenario_data}
            elif phase == 'phase2':
                phase2_fields = ['starting_portfolio', 'phase_start_age', 'full_retirement_age',
                                'part_time_income', 'monthly_contribution', 'annual_withdrawal', 'expected_return',
                                'inflation_rate', 'stock_allocation', 'return_volatility']
                base_data = {k: scenario_data[k] for k in phase2_fields if k in scenario_data}
            elif phase == 'phase3':
                phase3_fields = ['starting_portfolio', 'active_retirement_start_age', 'active_retirement_end_age',
                                'annual_expenses', 'annual_healthcare_costs', 'expected_return', 'inflation_rate',
                                'stock_allocation', 'return_volatility']
                base_data = {k: scenario_data[k] for k in phase3_fields if k in scenario_data}
            elif phase == 'phase4':
                phase4_fields = ['starting_portfolio', 'late_retirement_start_age', 'life_expectancy',
                                'annual_basic_expenses', 'annual_healthcare_costs', 'desired_legacy',
                                'expected_return', 'inflation_rate']
                base_data = {k: scenario_data[k] for k in phase4_fields if k in scenario_data}

        base_results = calculator_func(base_data) if base_data else None

        # Calculate deltas if we have base results
        deltas = {}
        if base_results:
            # Compare key metrics depending on phase
            if phase == 'phase1':
                deltas['future_value'] = what_if_results.future_value - base_results.future_value
                # For accumulation phase, combine personal and employer contributions
                what_if_total = what_if_results.total_personal_contributions + what_if_results.total_employer_contributions
                base_total = base_results.total_personal_contributions + base_results.total_employer_contributions
                deltas['total_contributions'] = what_if_total - base_total
                deltas['total_gains'] = what_if_results.investment_gains - base_results.investment_gains
            elif phase in ['phase2', 'phase3', 'phase4']:
                deltas['ending_portfolio'] = what_if_results.ending_portfolio - base_results.ending_portfolio
                deltas['total_withdrawals'] = what_if_results.total_withdrawals - base_results.total_withdrawals

        # Render results partial with comparison
        context = {
            'what_if_results': what_if_results,
            'base_results': base_results,
            'deltas': deltas,
            'phase': phase,
        }

        return render(request, 'calculator/partials/what_if_results.html', context)

    except (ValueError, TypeError, KeyError) as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in what_if_calculate: {error_trace}")
        return HttpResponse(
            f'<div class="text-red-500 p-4 bg-red-50 border border-red-200 rounded"><strong>Calculation error:</strong> {str(e)}</div>'
        )
