"""
Custom template tags and filters for the calculator app.

Usage in templates:
    {% load calculator_tags %}
    {{ amount|currency }}
    {{ percentage|percent }}
"""

from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name='currency')
def currency(value):
    """
    Format a number as USD currency.

    Usage: {{ amount|currency }}
    Example: 1234567.89 → $1,234,567.89
    """
    if value is None:
        return '$0.00'

    try:
        # Convert to Decimal for precision
        amount = Decimal(str(value))
        # Format with commas and 2 decimal places
        return f'${amount:,.2f}'
    except (ValueError, TypeError, ArithmeticError):
        return '$0.00'


@register.filter(name='currency_short')
def currency_short(value):
    """
    Format currency in short form (K, M).

    Usage: {{ amount|currency_short }}
    Examples:
        1500 → $1.5K
        1500000 → $1.5M
        1500000000 → $1.5B
    """
    if value is None:
        return '$0'

    try:
        amount = float(value)

        if amount >= 1_000_000_000:
            return f'${amount / 1_000_000_000:.1f}B'
        elif amount >= 1_000_000:
            return f'${amount / 1_000_000:.1f}M'
        elif amount >= 1_000:
            return f'${amount / 1_000:.1f}K'
        else:
            return f'${amount:.0f}'
    except (ValueError, TypeError):
        return '$0'


@register.filter(name='percent')
def percent(value, decimals=2):
    """
    Format a number as a percentage.

    Usage: {{ rate|percent }}
    Example: 7.5 → 7.50%
    """
    if value is None:
        return '0.00%'

    try:
        number = Decimal(str(value))
        return f'{number:.{decimals}f}%'
    except (ValueError, TypeError, ArithmeticError):
        return '0.00%'


@register.simple_tag
def calculate_percentage(part, total):
    """
    Calculate what percentage 'part' is of 'total'.

    Usage: {% calculate_percentage gains total %}
    Example: {% calculate_percentage 500000 1000000 %} → 50.0
    """
    try:
        if total == 0:
            return 0
        return (Decimal(str(part)) / Decimal(str(total))) * 100
    except (ValueError, TypeError, ZeroDivisionError, ArithmeticError):
        return 0


@register.inclusion_tag('calculator/snippets/currency_card.html')
def currency_card(title, amount, color='blue'):
    """
    Renders a styled currency card component.

    Usage:
        {% currency_card "Savings" total_amount "green" %}

    This is an inclusion tag - it renders a template snippet.
    """
    return {
        'title': title,
        'amount': amount,
        'color': color
    }


@register.filter(name='years_plural')
def years_plural(value):
    """
    Return 'year' or 'years' based on the value.

    Usage: {{ years|years_plural }}
    Example: 1 year, 5 years
    """
    try:
        num = int(value)
        return 'year' if num == 1 else 'years'
    except (ValueError, TypeError):
        return 'years'
