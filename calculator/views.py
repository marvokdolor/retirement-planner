from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .forms import RetirementCalculatorForm
from .calculator import calculate_retirement_savings
from .phase_forms import (
    AccumulationPhaseForm,
    PhasedRetirementForm,
    ActiveRetirementForm,
    LateRetirementForm
)
from .models import Scenario


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


def multi_phase_calculator(request):
    """
    Multi-phase retirement calculator with tabbed interface.
    Displays all 4 retirement phases in separate tabs.
    """
    # Initialize all forms (empty on GET)
    accumulation_form = AccumulationPhaseForm()
    phased_retirement_form = PhasedRetirementForm()
    active_retirement_form = ActiveRetirementForm()
    late_retirement_form = LateRetirementForm()

    return render(request, 'calculator/multi_phase_calculator.html', {
        'accumulation_form': accumulation_form,
        'phased_retirement_form': phased_retirement_form,
        'active_retirement_form': active_retirement_form,
        'late_retirement_form': late_retirement_form,
    })


# CRUD Views for Scenario model
class ScenarioListView(ListView):
    """Display list of all saved scenarios."""
    model = Scenario
    template_name = 'calculator/scenario_list.html'
    context_object_name = 'scenarios'


class ScenarioCreateView(CreateView):
    """Create a new scenario."""
    model = Scenario
    fields = ['name', 'data']
    template_name = 'calculator/scenario_form.html'
    success_url = reverse_lazy('calculator:scenario_list')


class ScenarioUpdateView(UpdateView):
    """Update an existing scenario."""
    model = Scenario
    fields = ['name', 'data']
    template_name = 'calculator/scenario_form.html'
    success_url = reverse_lazy('calculator:scenario_list')


class ScenarioDeleteView(DeleteView):
    """Delete a scenario."""
    model = Scenario
    template_name = 'calculator/scenario_confirm_delete.html'
    success_url = reverse_lazy('calculator:scenario_list')
