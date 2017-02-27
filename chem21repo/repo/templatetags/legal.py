from django import template
register = template.Library()


@register.inclusion_tag(
    'includes/legal_statement.html',
    takes_context=True)
def legal_statement(context):
    return {}
