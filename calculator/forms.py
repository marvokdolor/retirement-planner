from django import forms
from django.core.exceptions import ValidationError


# Custom validator function (reusable across forms)
def validate_realistic_return(value):
    """Reusable validator: Returns above 15% are unrealistic"""
    if value > 15:
        raise ValidationError(
            '%(value)s%% is unrealistic. Historical stock market average is 7-10%%.',
            params={'value': value}
        )


class RetirementCalculatorForm(forms.Form):
    """Form for retirement calculator inputs"""

    current_age = forms.IntegerField(
        label='Current Age',
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., 30'
        })
    )

    retirement_age = forms.IntegerField(
        label='Retirement Age',
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., 65'
        })
    )

    current_savings = forms.DecimalField(
        label='Current Savings ($)',
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., 50000',
            'step': '0.01'
        })
    )

    monthly_contribution = forms.DecimalField(
        label='Monthly Contribution ($)',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., 1000',
            'step': '0.01'
        })
    )

    expected_return = forms.DecimalField(
        label='Expected Annual Return (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        validators=[validate_realistic_return],  # Custom validator
        help_text='Typical stock market average is 7-10%',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., 7.5',
            'step': '0.01'
        })
    )

    variance = forms.DecimalField(
        label='Return Variance/Volatility (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=50,
        initial=2.0,
        required=False,
        help_text='Standard deviation of returns (typically 2-5% for diversified portfolios)',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., 2.5',
            'step': '0.01'
        })
    )

    # Field-specific custom validation
    def clean_monthly_contribution(self):
        """Custom validation for monthly contribution"""
        value = self.cleaned_data['monthly_contribution']

        # Warn if contribution seems too high
        if value > 10000:
            raise ValidationError(
                'Monthly contribution of $%(value)s seems very high. Please verify.',
                params={'value': value}
            )

        return value

    def clean_variance(self):
        """Custom validation for variance field"""
        value = self.cleaned_data.get('variance')

        # If not provided, return default
        if value is None:
            return 2.0

        # Validate reasonable range
        if value > 10:
            raise ValidationError(
                'Variance above 10%% indicates extremely high risk. Consider more conservative estimate.'
            )

        return value

    # Form-level validation (validates multiple fields together)
    def clean(self):
        """Cross-field validation for the entire form"""
        cleaned_data = super().clean()
        current_age = cleaned_data.get('current_age')
        retirement_age = cleaned_data.get('retirement_age')
        current_savings = cleaned_data.get('current_savings')
        monthly_contribution = cleaned_data.get('monthly_contribution')

        # Validation 1: Retirement age must be greater than current age
        if current_age and retirement_age:
            if retirement_age <= current_age:
                raise ValidationError(
                    'Retirement age must be greater than current age.'
                )

            # Validation 2: Warn if retirement period is very short
            years_to_retirement = retirement_age - current_age
            if years_to_retirement < 5:
                raise ValidationError(
                    'Less than 5 years to retirement is too short for meaningful planning.'
                )

        # Validation 3: Check if user has any savings plan at all
        if current_savings == 0 and monthly_contribution == 0:
            raise ValidationError(
                'You must have either current savings or monthly contributions (or both).'
            )

        return cleaned_data
