from django import template

register = template.Library()


@register.filter('range_to')
def range_to(start, end):
    return range(start, end + 1)
