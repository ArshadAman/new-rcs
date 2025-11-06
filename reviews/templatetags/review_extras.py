from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary by key.
    Usage: {{ dictionary|get_item:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0

@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide the value by the argument."""
    try:
        if int(arg) == 0:
            return 0
        return int(value) / int(arg) * 100
    except (ValueError, TypeError):
        return 0

