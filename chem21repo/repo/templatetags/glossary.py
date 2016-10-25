import logging
import urllib
import re
from django import template
from ..models import GlossaryTerm
register = template.Library()

@register.filter
def glossarize(txt):
    for term in GlossaryTerm.objects.all():
        desc = "<a class=\"glossary_term\" href=\"#\" title=\"%s\">\g<0></a>" % (term.description)
        txt = re.sub(re.escape(term.name), desc, txt, count=1, flags=re.IGNORECASE)
    return txt