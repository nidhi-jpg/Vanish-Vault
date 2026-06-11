from django import template

register = template.Library()

@register.filter
def percentage(value):
    """Convert decimal (0.0 to 1.0) to percentage string"""
    try:
        value = float(value)
        return f"{value * 100:.1f}%"
    except (ValueError, TypeError):
        return "0.0%"

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
