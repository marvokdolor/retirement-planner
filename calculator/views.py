from django.shortcuts import render
from .forms import RetirementCalculatorForm
from .calculator import calculate_retirement_savings


def retirement_calculator(request):
    """
    Handle retirement calculator form.
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
