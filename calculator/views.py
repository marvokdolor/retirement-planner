from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import (
    RetirementCalculatorForm,
    CustomUserCreationForm,
    ProfileUpdateForm,
    CustomPasswordChangeForm
)
from .calculator import calculate_retirement_savings
from .phase_forms import (
    AccumulationPhaseForm,
    PhasedRetirementForm,
    ActiveRetirementForm,
    LateRetirementForm
)
from .models import Scenario


# =============================================================================
# SIMPLE CALCULATOR (Original Single-Phase)
# =============================================================================
# Legacy calculator for basic retirement projections.
# Uses calculator.py for calculations.
# Consider using multi-phase calculator for new features.

def retirement_calculator(request):
    """
    Handle retirement calculator form (original simple calculator).
    GET: Display empty form
    POST: Process form, calculate results, and display
    """
    results = None

    if request.method == 'POST':
        form = RetirementCalculatorForm(request.POST)
        if form.is_valid():
            # Calculate retirement savings using our clean calculator module
            results = calculate_retirement_savings(
                current_age=form.cleaned_data['current_age'],
                retirement_age=form.cleaned_data['retirement_age'],
                current_savings=form.cleaned_data['current_savings'],
                monthly_contribution=form.cleaned_data['monthly_contribution'],
                annual_return_rate=form.cleaned_data['expected_return'],
                variance=form.cleaned_data.get('variance')
            )
    else:
        # GET request - display empty form
        form = RetirementCalculatorForm()

    return render(request, 'calculator/retirement_calculator.html', {
        'form': form,
        'results': results
    })


def about(request):
    """
    Display the About page with information about the tool and creator.
    """
    return render(request, 'calculator/about.html')


# =============================================================================
# MULTI-PHASE CALCULATOR (Primary Feature)
# =============================================================================
# Advanced calculator with 4 retirement phases.
# Uses phase_calculator.py for calculations.
# Supports scenario loading and saving.

def multi_phase_calculator(request, scenario_id=None):
    """
    Multi-phase retirement calculator with tabbed interface.

    Displays all 4 retirement phases in separate tabs:
    - Phase 1: Accumulation (building wealth)
    - Phase 2: Phased Retirement (semi-retirement transition)
    - Phase 3: Active Retirement (early retirement years)
    - Phase 4: Late Retirement (legacy & healthcare)

    Optionally loads a saved scenario if scenario_id is provided.

    Args:
        request (HttpRequest): Django HTTP request object
        scenario_id (int, optional): Primary key of saved scenario to load

    Returns:
        HttpResponse: Rendered template with phase forms and loaded scenario data

    Template:
        calculator/multi_phase_calculator.html
    """
    # If scenario_id is provided, load the scenario data
    # Initialize phase-specific data dictionaries
    phase1_initial = {}
    phase2_initial = {}
    phase3_initial = {}
    phase4_initial = {}
    scenario = None

    if scenario_id:
        # Only authenticated users can load scenarios
        if request.user.is_authenticated:
            scenario = get_object_or_404(Scenario, pk=scenario_id, user=request.user)
            scenario_data = scenario.data

            # Extract phase data from nested structure (scenarios saved after Dec 23, 2025)
            # Old flat-format scenarios will result in empty forms - user must re-save
            phase1_initial = scenario_data.get('phase1', {})
            phase2_initial = scenario_data.get('phase2', {})
            phase3_initial = scenario_data.get('phase3', {})
            phase4_initial = scenario_data.get('phase4', {})

    # Initialize all forms with phase-specific data
    accumulation_form = AccumulationPhaseForm(initial=phase1_initial)
    phased_retirement_form = PhasedRetirementForm(initial=phase2_initial)
    active_retirement_form = ActiveRetirementForm(initial=phase3_initial)
    late_retirement_form = LateRetirementForm(initial=phase4_initial)

    return render(request, 'calculator/multi_phase_calculator.html', {
        'accumulation_form': accumulation_form,
        'phased_retirement_form': phased_retirement_form,
        'active_retirement_form': active_retirement_form,
        'late_retirement_form': late_retirement_form,
        'loaded_scenario': scenario,
    })


# =============================================================================
# SCENARIO CRUD VIEWS
# =============================================================================
# Manage saved retirement scenarios (create, read, update, delete).
# Uses class-based views for standard CRUD operations.

class ScenarioListView(LoginRequiredMixin, ListView):
    """Display list of all saved scenarios for the logged-in user."""
    model = Scenario
    template_name = 'calculator/scenario_list.html'
    context_object_name = 'scenarios'

    def get_queryset(self):
        """Filter scenarios to only show the current user's scenarios."""
        return Scenario.objects.filter(user=self.request.user)


class ScenarioCreateView(LoginRequiredMixin, CreateView):
    """Create a new scenario."""
    model = Scenario
    fields = ['name', 'data']
    template_name = 'calculator/scenario_form.html'
    success_url = reverse_lazy('calculator:scenario_list')

    def form_valid(self, form):
        """Set the user before saving."""
        form.instance.user = self.request.user
        return super().form_valid(form)


class ScenarioUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing scenario."""
    model = Scenario
    fields = ['name', 'data']
    template_name = 'calculator/scenario_form.html'
    success_url = reverse_lazy('calculator:scenario_list')

    def get_queryset(self):
        """Only allow users to edit their own scenarios."""
        return Scenario.objects.filter(user=self.request.user)


class ScenarioDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a scenario."""
    model = Scenario
    template_name = 'calculator/scenario_confirm_delete.html'
    success_url = reverse_lazy('calculator:scenario_list')

    def get_queryset(self):
        """Only allow users to delete their own scenarios."""
        return Scenario.objects.filter(user=self.request.user)


# =============================================================================
# SCENARIO COMPARISON
# =============================================================================
# Compare two scenarios side-by-side and highlight better performer.

@login_required
def compare_scenarios(request):
    """
    Compare two scenarios side-by-side.
    GET: Display dropdown form to select scenarios
    POST: Calculate and display comparison results
    """
    from .phase_calculator import calculate_accumulation_phase

    scenarios = Scenario.objects.filter(user=request.user)
    comparison_data = None
    error_message = None
    better_scenario = None

    if request.method == 'POST':
        scenario1_id = request.POST.get('scenario1')
        scenario2_id = request.POST.get('scenario2')

        # Validate selection
        if scenario1_id == scenario2_id:
            error_message = "Please select two different scenarios to compare."
        elif scenario1_id and scenario2_id:
            scenario1 = get_object_or_404(Scenario, pk=scenario1_id)
            scenario2 = get_object_or_404(Scenario, pk=scenario2_id)

            # Calculate results for both scenarios
            try:
                # Extract phase1 data from nested structure
                scenario1_phase1 = scenario1.data.get('phase1', {})
                scenario2_phase1 = scenario2.data.get('phase1', {})

                result1 = calculate_accumulation_phase(scenario1_phase1)
                result2 = calculate_accumulation_phase(scenario2_phase1)

                # Determine which scenario performs better (higher future value)
                if result1.future_value > result2.future_value:
                    better_scenario = 1
                elif result2.future_value > result1.future_value:
                    better_scenario = 2
                else:
                    better_scenario = 'tie'

                comparison_data = {
                    'scenario1': {
                        'name': scenario1.name,
                        'result': result1,
                    },
                    'scenario2': {
                        'name': scenario2.name,
                        'result': result2,
                    }
                }
            except (KeyError, ValueError) as e:
                error_message = f"Error calculating scenarios: {str(e)}"

    return render(request, 'calculator/scenario_compare.html', {
        'scenarios': scenarios,
        'comparison': comparison_data,
        'error_message': error_message,
        'better_scenario': better_scenario,
    })


# =============================================================================
# EMAIL SCENARIO REPORTS
# =============================================================================

@login_required
def email_scenario(request, scenario_id):
    """
    Queue scenario report email to be sent in the background.
    """
    from django_q.tasks import async_task

    # Check if user has an email address
    if not request.user.email:
        return HttpResponse(
            '<div class="text-red-600">Please add an email address to your profile to receive scenario reports.</div>'
        )

    # Get scenario (ensure user owns it)
    scenario = get_object_or_404(Scenario, pk=scenario_id, user=request.user)

    try:
        # Queue email task to run in background
        async_task(
            'calculator.tasks.send_scenario_email',
            scenario_id,
            request.user.email
        )

        return HttpResponse('<div class="text-green-600">✓ Scenario report email queued successfully! You\'ll receive it shortly.</div>')

    except Exception as e:
        return HttpResponse(f'<div class="text-red-600">Error queuing email: {str(e)}</div>')


# =============================================================================
# AUTHENTICATION
# =============================================================================

def register(request):
    """
    User registration view with required email.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after registration
            return redirect('calculator:multi_phase_calculator')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    """
    User profile edit page.

    Handles two forms on one page:
    - ProfileUpdateForm (email editing)
    - CustomPasswordChangeForm (password change)

    Forms distinguished by 'action' parameter.
    """
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            # Handle email update
            profile_form = ProfileUpdateForm(
                request.POST,
                instance=request.user,
                user=request.user
            )
            password_form = CustomPasswordChangeForm(user=request.user)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('calculator:profile')

        elif action == 'change_password':
            # Handle password change
            profile_form = ProfileUpdateForm(instance=request.user, user=request.user)
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)

            if password_form.is_valid():
                user = password_form.save()
                # Keep user logged in after password change
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('calculator:profile')

        else:
            # No action specified, show both forms
            profile_form = ProfileUpdateForm(instance=request.user, user=request.user)
            password_form = CustomPasswordChangeForm(user=request.user)

    else:
        # GET request - show both forms
        profile_form = ProfileUpdateForm(instance=request.user, user=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'calculator/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })


# =============================================================================
# PDF REPORT GENERATION
# =============================================================================

@login_required
def generate_pdf_report(request, scenario_id):
    """
    Generate and download a PDF report for a saved scenario.

    Monte Carlo charts are automatically included if the scenario has phase data.

    Args:
        scenario_id: ID of the scenario to generate PDF for
    """
    from .pdf_generator import generate_retirement_pdf
    from .phase_calculator import (
        calculate_accumulation_phase,
        calculate_phased_retirement_phase,
        calculate_active_retirement_phase,
        calculate_late_retirement_phase
    )

    # Get scenario and ensure user owns it
    scenario = get_object_or_404(Scenario, id=scenario_id, user=request.user)

    # Calculate all phases from saved data (so PDF matches what user saw)
    phase_results = {}
    scenario_data = scenario.data

    # Phase 1: Accumulation
    if 'current_age' in scenario_data:
        try:
            phase_results['phase1'] = calculate_accumulation_phase(scenario_data)
        except (KeyError, ValueError, TypeError):
            pass

    # Phase 2: Phased Retirement (optional)
    if 'phase_start_age' in scenario_data:
        try:
            # Use Phase 1 ending as Phase 2 starting
            phase2_data = scenario_data.copy()
            if 'phase1' in phase_results:
                phase2_data['starting_portfolio'] = phase_results['phase1'].future_value
            phase_results['phase2'] = calculate_phased_retirement_phase(phase2_data)
        except (KeyError, ValueError, TypeError):
            pass

    # Phase 3: Active Retirement
    if 'active_retirement_start_age' in scenario_data:
        try:
            # Cascade starting portfolio
            phase3_data = scenario_data.copy()
            if 'phase2' in phase_results:
                phase3_data['starting_portfolio'] = phase_results['phase2'].ending_portfolio
            elif 'phase1' in phase_results:
                phase3_data['starting_portfolio'] = phase_results['phase1'].future_value
            phase_results['phase3'] = calculate_active_retirement_phase(phase3_data)
        except (KeyError, ValueError, TypeError):
            pass

    # Phase 4: Late Retirement
    if 'late_retirement_start_age' in scenario_data:
        try:
            # Cascade starting portfolio
            phase4_data = scenario_data.copy()
            if 'phase3' in phase_results:
                phase4_data['starting_portfolio'] = phase_results['phase3'].ending_portfolio
            elif 'phase2' in phase_results:
                phase4_data['starting_portfolio'] = phase_results['phase2'].ending_portfolio
            elif 'phase1' in phase_results:
                phase4_data['starting_portfolio'] = phase_results['phase1'].future_value
            phase_results['phase4'] = calculate_late_retirement_phase(phase4_data)
        except (KeyError, ValueError, TypeError):
            pass

    # Generate PDF with calculated results
    pdf_buffer = generate_retirement_pdf(scenario, phase_results)

    # Create response
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')

    # Set filename (clean scenario name for filename)
    filename = f"{scenario.name.replace(' ', '_')}_Report.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@login_required
def generate_pdf_from_current(request):
    """
    Generate PDF from current calculator state (not saved scenario).

    Creates a temporary scenario from POST data, calculates results, and generates PDF.
    Monte Carlo charts are automatically included if phase data is available.
    """
    from .pdf_generator import generate_retirement_pdf
    from .models import Scenario
    from .phase_calculator import (
        calculate_accumulation_phase,
        calculate_phased_retirement_phase,
        calculate_active_retirement_phase,
        calculate_late_retirement_phase
    )

    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    # Gather all form data from POST
    scenario_data = dict(request.POST.items())
    # Remove non-data fields
    scenario_data.pop('csrfmiddlewaretoken', None)
    scenario_data.pop('scenario_name', None)

    # Create temporary scenario (not saved to database)
    temp_scenario = Scenario(
        user=request.user,
        name=request.POST.get('scenario_name', 'Current Calculation'),
        data=scenario_data
    )

    # Calculate all phases from the data (same logic as generate_pdf_report)
    phase_results = {}

    # Phase 1: Accumulation
    if 'current_age' in scenario_data:
        try:
            phase_results['phase1'] = calculate_accumulation_phase(scenario_data)
        except (KeyError, ValueError, TypeError):
            pass

    # Phase 2: Phased Retirement (optional)
    if 'phase_start_age' in scenario_data:
        try:
            phase2_data = scenario_data.copy()
            if 'phase1' in phase_results:
                phase2_data['starting_portfolio'] = phase_results['phase1'].future_value
            phase_results['phase2'] = calculate_phased_retirement_phase(phase2_data)
        except (KeyError, ValueError, TypeError):
            pass

    # Phase 3: Active Retirement
    if 'active_retirement_start_age' in scenario_data:
        try:
            phase3_data = scenario_data.copy()
            if 'phase2' in phase_results:
                phase3_data['starting_portfolio'] = phase_results['phase2'].ending_portfolio
            elif 'phase1' in phase_results:
                phase3_data['starting_portfolio'] = phase_results['phase1'].future_value
            phase_results['phase3'] = calculate_active_retirement_phase(phase3_data)
        except (KeyError, ValueError, TypeError):
            pass

    # Phase 4: Late Retirement
    if 'late_retirement_start_age' in scenario_data:
        try:
            phase4_data = scenario_data.copy()
            if 'phase3' in phase_results:
                phase4_data['starting_portfolio'] = phase_results['phase3'].ending_portfolio
            elif 'phase2' in phase_results:
                phase4_data['starting_portfolio'] = phase_results['phase2'].ending_portfolio
            elif 'phase1' in phase_results:
                phase4_data['starting_portfolio'] = phase_results['phase1'].future_value
            phase_results['phase4'] = calculate_late_retirement_phase(phase4_data)
        except (KeyError, ValueError, TypeError):
            pass

    # Generate PDF with calculated results
    pdf_buffer = generate_retirement_pdf(temp_scenario, phase_results)

    # Create response
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')

    # Set filename
    filename = f"Retirement_Plan_Report.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


# =============================================================================
# WHAT-IF SCENARIO ANALYSIS
# =============================================================================

@login_required
def what_if_comparison(request, scenario_id):
    """
    Display what-if comparison interface for a saved scenario.

    Shows side-by-side comparison:
    - Left: Original scenario (locked, read-only)
    - Right: Adjustable inputs with live calculations

    Args:
        scenario_id: ID of the base scenario to analyze

    Returns:
        Rendered template with base scenario and adjustable forms
    """
    # Get scenario and ensure user owns it
    base_scenario = get_object_or_404(Scenario, id=scenario_id, user=request.user)

    # Initialize forms with base scenario data
    scenario_data = base_scenario.data

    # Create forms pre-populated with base scenario data
    accumulation_form = None
    phased_retirement_form = None
    active_retirement_form = None
    late_retirement_form = None

    # Handle both nested (phase1, phase2, etc.) and flat data structures
    # Nested format: {'phase1': {...}, 'phase2': {...}}
    # Flat format: {'current_age': 30, 'retirement_start_age': 60, ...}

    if 'phase1' in scenario_data:
        # New nested format
        if 'phase1' in scenario_data:
            phase1_data = scenario_data['phase1'].copy()
            # Handle old field name for backward compatibility
            if 'retirement_age' in phase1_data and 'retirement_start_age' not in phase1_data:
                phase1_data['retirement_start_age'] = phase1_data.pop('retirement_age')
            accumulation_form = AccumulationPhaseForm(initial=phase1_data)
        if 'phase2' in scenario_data:
            phased_retirement_form = PhasedRetirementForm(initial=scenario_data['phase2'])
        if 'phase3' in scenario_data:
            active_retirement_form = ActiveRetirementForm(initial=scenario_data['phase3'])
        if 'phase4' in scenario_data:
            late_retirement_form = LateRetirementForm(initial=scenario_data['phase4'])
    else:
        # Old flat format - distribute fields to appropriate forms based on field names
        # Phase 1 fields: current_age, retirement_start_age, current_savings, monthly_contribution, etc.
        phase1_data = {}
        phase2_data = {}
        phase3_data = {}
        phase4_data = {}

        # Phase 1 (Accumulation) fields
        phase1_fields = ['current_age', 'retirement_start_age', 'current_savings', 'monthly_contribution',
                        'employer_match_rate', 'annual_salary_increase', 'stock_allocation',
                        'expected_return', 'inflation_rate', 'return_volatility']
        for field in phase1_fields:
            if field in scenario_data:
                phase1_data[field] = scenario_data[field]

        # Phase 2 (Phased Retirement) fields
        phase2_fields = ['starting_portfolio', 'phase_start_age', 'full_retirement_age',
                        'part_time_income', 'monthly_contribution', 'annual_withdrawal', 'expected_return',
                        'inflation_rate', 'stock_allocation', 'return_volatility']
        for field in phase2_fields:
            if field in scenario_data:
                phase2_data[field] = scenario_data[field]

        # Phase 3 (Active Retirement) fields
        phase3_fields = ['starting_portfolio', 'active_retirement_start_age', 'active_retirement_end_age',
                        'annual_expenses', 'annual_healthcare_costs', 'expected_return', 'inflation_rate',
                        'stock_allocation', 'return_volatility']
        for field in phase3_fields:
            if field in scenario_data:
                phase3_data[field] = scenario_data[field]

        # Phase 4 (Late Retirement) fields
        phase4_fields = ['starting_portfolio', 'late_retirement_start_age', 'life_expectancy',
                        'annual_basic_expenses', 'annual_healthcare_costs', 'desired_legacy',
                        'expected_return', 'inflation_rate']
        for field in phase4_fields:
            if field in scenario_data:
                phase4_data[field] = scenario_data[field]

        # Only create forms if we have data for them
        if phase1_data:
            accumulation_form = AccumulationPhaseForm(initial=phase1_data)
        if phase2_data and 'phase_start_age' in phase2_data:
            phased_retirement_form = PhasedRetirementForm(initial=phase2_data)
        if phase3_data and 'active_retirement_start_age' in phase3_data:
            active_retirement_form = ActiveRetirementForm(initial=phase3_data)
        if phase4_data and 'late_retirement_start_age' in phase4_data:
            late_retirement_form = LateRetirementForm(initial=phase4_data)

    context = {
        'base_scenario': base_scenario,
        'accumulation_form': accumulation_form,
        'phased_retirement_form': phased_retirement_form,
        'active_retirement_form': active_retirement_form,
        'late_retirement_form': late_retirement_form,
    }

    return render(request, 'calculator/what_if_comparison.html', context)
