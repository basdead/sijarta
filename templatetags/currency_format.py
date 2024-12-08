from django import template

register = template.Library()

@register.filter
def currency_format(value):
    try:
        if value is None:
            return "Rp 0"
        value = float(value)
        # Format with Indonesian number format (using . as thousand separator)
        formatted = f"{value:,.0f}".replace(",", ".")
        return f"Rp {formatted}"
    except (ValueError, TypeError):
        return value
