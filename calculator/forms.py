from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Scenario


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
        decimal_places=0,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., 50000',
            'step': '1'
        })
    )

    monthly_contribution = forms.DecimalField(
        label='Monthly Contribution ($)',
        max_digits=10,
        decimal_places=0,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., 1000',
            'step': '1'
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


class ScenarioNameForm(forms.ModelForm):
    """Form for saving a scenario - only asks for name, data is captured from calculator"""
    class Meta:
        model = Scenario
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g., Conservative Retirement Plan'
            })
        }


class CustomUserCreationForm(UserCreationForm):
    """Custom registration form for saving scenarios."""

    email = forms.EmailField(
        required=False,
        help_text='Optional. Only needed if you want to reset your password later.',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'your.email@example.com (optional)'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Choose a username'
            })
        }

    def save(self, commit=True):
        """Save email to user model if provided."""
        user = super().save(commit=False)
        if self.cleaned_data.get('email'):
            user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user email (username read-only)."""

    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
                'placeholder': 'your.email@example.com'
            })
        }
        help_texts = {
            'email': 'Optional. Used for password reset and scenario emails.'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False

    def clean_email(self):
        """Validate email is unique (excluding current user)."""
        email = self.cleaned_data.get('email')
        if email and self.user:
            # Check if another user has this email
            if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
                raise forms.ValidationError('This email address is already in use.')
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Tailwind styling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Style all password fields with Tailwind
        for field_name in ['old_password', 'new_password1', 'new_password2']:
            self.fields[field_name].widget.attrs.update({
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
            })

        # Update labels for clarity
        self.fields['old_password'].label = 'Current Password'
        self.fields['new_password1'].label = 'New Password'
        self.fields['new_password2'].label = 'Confirm New Password'
