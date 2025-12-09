# Django Template System Guide

## 1. Template Inheritance

### base.html (Parent Template)
```django
{% load static tailwind_tags %}
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Default Title{% endblock %}</title>
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
    {% block footer %}Default Footer{% endblock %}
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### child.html (Child Template)
```django
{% extends 'base.html' %}

{% block title %}My Page{% endblock %}

{% block content %}
    <h1>This replaces the content block</h1>
{% endblock %}

{% block extra_css %}
    <style>/* Custom CSS */</style>
{% endblock %}
```

**How it works:**
- `{% extends %}` must be the first tag
- `{% block %}` defines replaceable sections
- Child templates can override any block
- Unoverridden blocks use parent's default

---

## 2. Built-in Template Tags

### Control Flow
```django
{% if user.is_authenticated %}
    Welcome back!
{% elif user.is_guest %}
    Guest mode
{% else %}
    Please log in
{% endif %}

{% for item in items %}
    {{ item.name }}
    {% empty %}
    No items found
{% endfor %}
```

### URL Generation
```django
<a href="{% url 'home' %}">Home</a>
<a href="{% url 'calculator:retirement_calculator' %}">Calculator</a>
<a href="{% url 'detail' id=item.id %}">View {{ item.name }}</a>
```

### Including Other Templates
```django
{% include 'navbar.html' %}
{% include 'sidebar.html' with user=request.user %}
```

### Comments
```django
{# Single line comment #}

{% comment %}
Multi-line comment
Can span multiple lines
{% endcomment %}
```

---

## 3. Built-in Filters

### String Filters
```django
{{ name|lower }}           → lowercase
{{ name|upper }}           → UPPERCASE
{{ name|title }}           → Title Case
{{ text|truncatewords:30 }} → First 30 words...
{{ text|slice:":100" }}    → First 100 characters
```

### Number Filters
```django
{{ price|floatformat:2 }}     → 123.46
{{ number|add:5 }}            → number + 5
{{ number|divisibleby:3 }}    → True/False
```

### Date/Time Filters
```django
{{ date|date:"Y-m-d" }}       → 2025-12-08
{{ date|date:"F j, Y" }}      → December 8, 2025
{% now "Y-m-d H:i" %}         → Current date/time
```

### List Filters
```django
{{ list|length }}             → Number of items
{{ list|first }}              → First item
{{ list|last }}               → Last item
{{ list|join:", " }}          → Join with comma
```

### Safe/Escape
```django
{{ html_content|safe }}       → Don't escape HTML
{{ user_input|escape }}       → Escape HTML (default)
```

---

## 4. Custom Template Tags & Filters

### Location
```
calculator/
    templatetags/
        __init__.py
        calculator_tags.py
```

### Custom Filter
```python
# calculator_tags.py
from django import template
register = template.Library()

@register.filter(name='currency')
def currency(value):
    """Format as currency"""
    return f'${value:,.2f}'
```

**Usage:**
```django
{% load calculator_tags %}
{{ amount|currency }}  → $1,234.56
```

### Custom Simple Tag
```python
@register.simple_tag
def calculate_percentage(part, total):
    """Calculate percentage"""
    return (part / total) * 100
```

**Usage:**
```django
{% calculate_percentage 500 1000 as pct %}
{{ pct }}%  → 50%
```

### Custom Inclusion Tag
```python
@register.inclusion_tag('calculator/snippets/currency_card.html')
def currency_card(title, amount, color='blue'):
    """Renders a reusable component"""
    return {
        'title': title,
        'amount': amount,
        'color': color
    }
```

**Usage:**
```django
{% currency_card "Savings" total_amount "green" %}
```

---

## 5. Template Variables & Context

### Accessing Variables
```django
{{ variable }}                → Simple variable
{{ user.name }}              → Object attribute
{{ user.get_full_name }}     → Method call (no args)
{{ items.0 }}                → List/tuple index
{{ dict.key }}               → Dictionary key
```

### Variable Assignment
```django
{% with total=items|length %}
    {{ total }} items
{% endwith %}

{% calculate_percentage 500 1000 as pct %}
Percentage: {{ pct }}%
```

---

## 6. Template Best Practices

### ✅ DO
- Keep logic in views, display in templates
- Use template inheritance (DRY principle)
- Create custom filters for reusable formatting
- Use `{% load %}` at top of template
- Use `{% url %}` instead of hardcoded URLs

### ❌ DON'T
- Put business logic in templates
- Nest too many levels of inheritance
- Perform database queries in templates
- Use complex Python expressions

---

## 7. Common Patterns

### Conditional Classes
```django
<div class="{% if user.is_premium %}gold{% else %}silver{% endif %}">
```

### Loop Counter
```django
{% for item in items %}
    {{ forloop.counter }}. {{ item.name }}
    {% if forloop.first %}First!{% endif %}
    {% if forloop.last %}Last!{% endif %}
{% endfor %}
```

### Default Values
```django
{{ value|default:"N/A" }}
{{ value|default_if_none:"0" }}
```

### Multiple Filters (Chained)
```django
{{ text|lower|truncatewords:10|title }}
```

---

## 8. Debug Mode

### Show Template Variables
```django
{{ debug }}  → Shows all available variables (if DEBUG=True)
```

### Template Comments for Debugging
```django
{# DEBUG: user = {{ user }} #}
{# DEBUG: items count = {{ items|length }} #}
```

---

## Real Examples from Our Project

### Currency Formatting
```django
{% load calculator_tags %}
{{ results.future_value|currency }}           → $1,234,567.89
{{ results.future_value|currency_short }}     → $1.2M
```

### Percentage with Custom Precision
```django
{{ results.expected_return|percent:2 }}       → 7.50%
{{ results.roi|percent:0 }}                   → 150%
```

### Pluralization
```django
{{ years }} {{ years|years_plural }}          → "1 year" or "5 years"
```

### Calculate and Display
```django
{% calculate_percentage gains total as roi %}
ROI: {{ roi|percent:1 }}
```
