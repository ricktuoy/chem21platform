import logging
import urllib
from django import template
from ..models import GlossaryTerm
register = template.Library()

@register.filter
def glossarize(txt):
    for term in GlossaryTerm.objects.all():
        desc = "<a class=\"glossary_term\" href=\"#\" title=\"%s\">%s</a>" % (term.description, term.name)
        txt = txt.replace(term.name, desc)
    return txt