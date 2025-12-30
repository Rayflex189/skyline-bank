# In your app, create templatetags/loan_filters.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_percentage(value, percentage):
    """Add percentage to value"""
    try:
        return float(value) * (1 + float(percentage) / 100)
    except (ValueError, TypeError):
        return value