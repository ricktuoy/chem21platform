import logging
import urllib
import re
from django import template
from ..models import GlossaryTerm
register = template.Library()

@register.filter
def glossarize(txt):

    terms = {}
    for term in GlossaryTerm.objects.all():
        txt = re.sub("(\<p\>.*?)("+re.escape(term.name)+")(.*\<\/p\>)", "\g<1>[*[\g<2>]*]\g<3>", txt, count=1, flags=re.IGNORECASE)
        terms[term.name] = term.description

    for term, desc in terms.iteritems():
        desc_markup = "<a class=\"glossary_term\" href=\"#\" title=\"%s\">\g<1></a>" % (desc)
        txt = re.sub("\[\*\[("+re.escape(term)+")\]\*\]", desc_markup, txt, count=1, flags=re.IGNORECASE)
    return txt