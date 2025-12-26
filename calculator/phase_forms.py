"""
Forms for the four retirement planning phases.

Phases:
1. Accumulation - Building wealth during working years
2. Phased Retirement - Semi-retired, optional continued contributions
3. Active Retirement - Early retirement years (lower healthcare costs, active lifestyle)
4. Late Retirement - Final years with higher healthcare/long-term care costs
"""

from django import forms
from django.core.exceptions import ValidationError


def validate_realistic_return(value):
    """Reusable validator: Returns above 15% are unrealistic"""
    if value > 15:
        raise ValidationError(
            '%(value)s%% is unrealistic. Historical stock market average is 7-10%%.',
            params={'value': value}
        )


class BaseCalculatorForm(forms.Form):
    """
    Base form with common field styling.

    All phase forms inherit from this to maintain consistent Tailwind UI.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Tailwind styling to all number inputs
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.NumberInput):
                current_classes = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f'{current_classes} w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'.strip()


# ===== PHASE 1: ACCUMULATION =====
class AccumulationPhaseForm(BaseCalculatorForm):
    """
    Phase 1: Accumulation (Building wealth during working years)

    Typical age range: 25-60
    Focus: Maximizing savings through contributions and compound interest
    """

    current_age = forms.IntegerField(
        label='Current Age',
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 30'})
    )

    retirement_start_age = forms.IntegerField(
        label='Planned Retirement Start Age',
        min_value=40,
        max_value=100,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 60'})
    )

    current_savings = forms.DecimalField(
        label='Current Retirement Savings',
        max_digits=12,
        decimal_places=0,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 50,000', 'step': '1'})
    )

    monthly_contribution = forms.DecimalField(
        label='Monthly Contribution',
        max_digits=10,
        decimal_places=0,
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 1,500', 'step': '1'})
    )

    employer_match_rate = forms.DecimalField(
        label='Employer Match Rate (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        required=False,
        help_text='Employer 401k match as % of your contribution',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 50', 'step': '0.01'})
    )

    expected_return = forms.DecimalField(
        label='Expected Annual Return (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        validators=[validate_realistic_return],
        help_text='Historical stock market average: 7-10%',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 7.5', 'step': '0.01'})
    )

    annual_salary_increase = forms.DecimalField(
        label='Expected Annual Salary Increase (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        required=False,
        help_text='Assumes contributions increase with salary',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 3.0', 'step': '0.01'})
    )

    return_volatility = forms.DecimalField(
        label='Return Volatility Range (±%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=50,
        required=False,
        initial=10.0,
        help_text='Range of returns above/below expected (Conservative: 5%, Moderate: 10%, Aggressive: 15-20%)',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 10.0', 'step': '0.1'})
    )

    def clean(self):
        cleaned_data = super().clean()
        current_age = cleaned_data.get('current_age')
        retirement_start_age = cleaned_data.get('retirement_start_age')
        current_savings = cleaned_data.get('current_savings')
        monthly_contribution = cleaned_data.get('monthly_contribution')

        if current_age and retirement_start_age:
            if retirement_start_age <= current_age:
                raise ValidationError(
                    f'Your retirement age ({retirement_start_age}) must be greater than your current age ({current_age}). '
                    'Please increase your retirement start age.'
                )

            years_to_retirement = retirement_start_age - current_age
            if years_to_retirement < 5:
                raise ValidationError(
                    f'You have only {years_to_retirement} years until retirement. '
                    'The accumulation phase requires at least 5 years. Consider adjusting your retirement age or current age.'
                )

        if current_savings == 0 and monthly_contribution == 0:
            raise ValidationError(
                'Please enter either current savings or monthly contributions (or both). '
                'You need at least one source of funds to build your retirement portfolio.'
            )

        return cleaned_data


# ===== PHASE 2: PHASED RETIREMENT =====
class PhasedRetirementForm(BaseCalculatorForm):
    """
    Phase 2: Phased Retirement (Semi-retired, optional continued work)

    Typical age range: 60-70
    Focus: Transitioning to retirement while still earning and contributing
    """

    starting_portfolio = forms.DecimalField(
        label='Portfolio Value at Phase Start',
        max_digits=12,
        decimal_places=0,
        min_value=0,
        help_text='Value accumulated from Phase 1',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 800,000', 'step': '1'})
    )

    phase_start_age = forms.IntegerField(
        label='Phase Start Age',
        min_value=50,
        max_value=100,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 60'})
    )

    full_retirement_age = forms.IntegerField(
        label='Full Retirement Age',
        min_value=50,
        max_value=100,
        help_text='When you stop working completely',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 67'})
    )

    part_time_income = forms.DecimalField(
        label='Annual Part-Time Income',
        max_digits=10,
        decimal_places=0,
        min_value=0,
        required=False,
        help_text='Consulting, part-time work, etc.',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 40,000', 'step': '1'})
    )

    monthly_contribution = forms.DecimalField(
        label='Optional Monthly Contributions',
        max_digits=10,
        decimal_places=0,
        min_value=0,
        required=False,
        help_text='If still contributing from part-time income',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 500', 'step': '1'})
    )

    annual_withdrawal = forms.DecimalField(
        label='Annual Withdrawal Needed',
        max_digits=10,
        decimal_places=0,
        min_value=0,
        required=False,
        help_text='Supplement part-time income if needed',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 20,000', 'step': '1'})
    )

    expected_return = forms.DecimalField(
        label='Expected Annual Return (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        validators=[validate_realistic_return],
        help_text='Typically 5-7% (more conservative than Phase 1)',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 6.0', 'step': '0.01'})
    )

    stock_allocation = forms.DecimalField(
        label='Stock Allocation (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        help_text='Gradually reducing risk',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 60', 'step': '0.01'})
    )

    return_volatility = forms.DecimalField(
        label='Return Volatility Range (±%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=50,
        required=False,
        initial=10.0,
        help_text='Range of returns above/below expected (Conservative: 5%, Moderate: 10%, Aggressive: 15-20%)',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 10.0', 'step': '0.1'})
    )

    inflation_rate = forms.DecimalField(
        label='Expected Inflation Rate (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=20,
        required=False,
        initial=3.0,
        help_text='Historical average: 2-3%',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 3.0', 'step': '0.1'})
    )

    def clean(self):
        cleaned_data = super().clean()
        phase_start_age = cleaned_data.get('phase_start_age')
        full_retirement_age = cleaned_data.get('full_retirement_age')

        if phase_start_age and full_retirement_age:
            if full_retirement_age <= phase_start_age:
                raise ValidationError(
                    f'Your full retirement age ({full_retirement_age}) must be after your phased retirement start age ({phase_start_age}). '
                    'Phased retirement is a transition period before full retirement.'
                )

            phase_duration = full_retirement_age - phase_start_age
            if phase_duration > 20:
                raise ValidationError(
                    f'Your phased retirement period is {phase_duration} years, which seems unusually long. '
                    'Most phased retirements last 3-10 years. Consider shortening this period or using Active Retirement instead.'
                )

        return cleaned_data


# ===== PHASE 3: ACTIVE RETIREMENT =====
class ActiveRetirementForm(BaseCalculatorForm):
    """
    Phase 3: Active Retirement (Early retirement years, active lifestyle)

    Typical age range: 65-80
    Focus: Sustainable withdrawals, travel/activities, lower healthcare costs
    """

    starting_portfolio = forms.DecimalField(
        label='Portfolio Value at Active Retirement Start',
        max_digits=12,
        decimal_places=0,
        min_value=0,
        help_text='Value at beginning of this phase',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 1,200,000', 'step': '1'})
    )

    active_retirement_start_age = forms.IntegerField(
        label='Active Retirement Start Age',
        min_value=50,
        max_value=100,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 65'})
    )

    active_retirement_end_age = forms.IntegerField(
        label='Active Retirement End Age',
        min_value=60,
        max_value=100,
        help_text='Transition to Late Retirement phase',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 80'})
    )

    annual_expenses = forms.DecimalField(
        label='Annual Living Expenses',
        max_digits=10,
        decimal_places=0,
        min_value=0,
        help_text='Travel, activities, daily living',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 70,000', 'step': '1'})
    )

    annual_healthcare_costs = forms.DecimalField(
        label='Annual Healthcare Costs',
        max_digits=10,
        decimal_places=0,
        min_value=0,
        help_text='Premiums, out-of-pocket, prescriptions',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 8,000', 'step': '1'})
    )

    # Social Security and Pension - COMMENTED OUT FOR FUTURE FUNCTIONALITY
    # social_security_annual = forms.DecimalField(
    #     label='Annual Social Security Income ($)',
    #     max_digits=10,
    #     decimal_places=2,
    #     min_value=0,
    #     required=False,
    #     widget=forms.NumberInput(attrs={'placeholder': 'e.g., 28000', 'step': '0.01'})
    # )

    # pension_annual = forms.DecimalField(
    #     label='Annual Pension Income ($)',
    #     max_digits=10,
    #     decimal_places=2,
    #     min_value=0,
    #     required=False,
    #     widget=forms.NumberInput(attrs={'placeholder': 'e.g., 15000', 'step': '0.01'})
    # )

    expected_return = forms.DecimalField(
        label='Expected Annual Return (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        help_text='Typically 4-6% for balanced portfolio',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 5.0', 'step': '0.01'})
    )

    inflation_rate = forms.DecimalField(
        label='Expected Inflation Rate (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        initial=3.0,
        help_text='Expenses increase with inflation',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 3.0', 'step': '0.01'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_age = cleaned_data.get('active_retirement_start_age')
        end_age = cleaned_data.get('active_retirement_end_age')

        if start_age and end_age:
            if end_age <= start_age:
                raise ValidationError(
                    f'Your active retirement end age ({end_age}) must be greater than start age ({start_age}). '
                    'This phase represents your early retirement years.'
                )

            phase_duration = end_age - start_age
            if phase_duration < 5:
                raise ValidationError(
                    f'Your active retirement period is only {phase_duration} years. '
                    'Plan for at least 5 years to account for the active early retirement lifestyle. '
                    'Consider extending the end age or combining with late retirement.'
                )
            if phase_duration > 30:
                raise ValidationError(
                    f'Your active retirement period is {phase_duration} years, which is unusually long. '
                    'Most active retirement phases last 10-20 years. Consider splitting this into Active and Late retirement phases.'
                )

        return cleaned_data


# ===== PHASE 4: LATE RETIREMENT =====
class LateRetirementForm(BaseCalculatorForm):
    """
    Phase 4: Late Retirement (High healthcare/long-term care costs)

    Typical age range: 80+
    Focus: Long-term care planning, higher medical costs, portfolio preservation
    """

    starting_portfolio = forms.DecimalField(
        label='Portfolio Value at Late Retirement Start',
        max_digits=12,
        decimal_places=0,
        min_value=0,
        help_text='Remaining portfolio from Active Retirement',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 600,000', 'step': '1'})
    )

    late_retirement_start_age = forms.IntegerField(
        label='Late Retirement Start Age',
        min_value=70,
        max_value=100,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 80'})
    )

    life_expectancy = forms.IntegerField(
        label='Expected Life Expectancy',
        min_value=75,
        max_value=120,
        help_text='Plan conservatively (90-100)',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 95'})
    )

    annual_basic_expenses = forms.DecimalField(
        label='Annual Basic Living Expenses',
        max_digits=10,
        decimal_places=0,
        min_value=0,
        help_text='Reduced activity spending',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 40,000', 'step': '1'})
    )

    annual_healthcare_costs = forms.DecimalField(
        label='Annual Healthcare Costs',
        max_digits=10,
        decimal_places=0,
        min_value=0,
        help_text='Higher medical costs',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 15,000', 'step': '1'})
    )

    # Long-term care fields - COMMENTED OUT FOR FUTURE FUNCTIONALITY
    # long_term_care_annual = forms.DecimalField(
    #     label='Expected Long-Term Care Costs ($)',
    #     max_digits=10,
    #     decimal_places=2,
    #     min_value=0,
    #     required=False,
    #     help_text='Assisted living, nursing home, in-home care',
    #     widget=forms.NumberInput(attrs={'placeholder': 'e.g., 75000', 'step': '0.01'})
    # )

    # ltc_insurance_coverage = forms.DecimalField(
    #     label='Long-Term Care Insurance Coverage ($)',
    #     max_digits=10,
    #     decimal_places=2,
    #     min_value=0,
    #     required=False,
    #     help_text='Annual benefit from LTC policy',
    #     widget=forms.NumberInput(attrs={'placeholder': 'e.g., 40000', 'step': '0.01'})
    # )

    # Social Security - COMMENTED OUT FOR FUTURE FUNCTIONALITY
    # social_security_annual = forms.DecimalField(
    #     label='Annual Social Security Income ($)',
    #     max_digits=10,
    #     decimal_places=2,
    #     min_value=0,
    #     required=False,
    #     widget=forms.NumberInput(attrs={'placeholder': 'e.g., 32000', 'step': '0.01'})
    # )

    expected_return = forms.DecimalField(
        label='Expected Annual Return (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        help_text='Very conservative portfolio (3-4%)',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 3.5', 'step': '0.01'})
    )

    inflation_rate = forms.DecimalField(
        label='Expected Inflation Rate (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        initial=3.0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 3.0', 'step': '0.01'})
    )

    desired_legacy = forms.DecimalField(
        label='Desired Legacy Amount',
        max_digits=12,
        decimal_places=0,
        min_value=0,
        required=False,
        help_text='Target amount to leave heirs',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 200,000', 'step': '1'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_age = cleaned_data.get('late_retirement_start_age')
        life_expectancy = cleaned_data.get('life_expectancy')

        if start_age and life_expectancy:
            if life_expectancy <= start_age:
                raise ValidationError(
                    f'Your life expectancy ({life_expectancy}) must be greater than late retirement start age ({start_age}). '
                    'Late retirement is your final phase leading up to end of life. Consider increasing life expectancy.'
                )

            phase_duration = life_expectancy - start_age
            if phase_duration < 5:
                raise ValidationError(
                    f'Your late retirement period is only {phase_duration} years. '
                    'Plan for at least 5 years to account for increased healthcare needs and legacy planning. '
                    'Consider extending life expectancy or adjusting the start age.'
                )

        return cleaned_data
