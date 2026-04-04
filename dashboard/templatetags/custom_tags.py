from django import template
register = template.Library()

@register.filter
def pluck(lst, key):
    return [item[key] for item in lst]
