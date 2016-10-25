import logging
import urllib
import re
from django import template
from ..models import GlossaryTerm
register = template.Library()

@register.filter
def glossarize(txt):
    repls = []
    terms = {}
    repl_terms = set([])
    
    def sub_fn(match):
        term = match.group(2).lower()

        if term not in repl_terms:
            repl_terms.add(term)
            desc_markup = "<a class=\"glossary_term\" href=\"#\" title=\"%s\">%s</a>" % (terms[term], match.group(2))
            repls.append(desc_markup)
            return "%s%s%s" % (match.group(1), desc_markup, match.group(3))
        else:
            return match.group(0)
    
    re_terms = []
    for term in GlossaryTerm.objects.all():
        terms[term.name.lower()] = term.description
        re_terms.append(re.escape(term.name))

    search_term = "|".join(re_terms)
    logging.debug(search_term)
    span_1 = re.escape("<span style=\"font-weight: bold;\">")
    span_2 = re.escape("</span>")
    txt = re.sub("(%s\s*?)(%s)(\s*?%s)" % (span_1, search_term, span_2), sub_fn, txt, flags=re.IGNORECASE)
        
    """
    for term, desc in terms.iteritems():
        desc_markup = "<a class=\"glossary_term\" href=\"#\" title=\"%s\">\g<1></a>" % (desc)
        txt = re.sub("\[\*\[("+re.escape(term)+")\]\*\]", desc_markup, txt, count=1, flags=re.IGNORECASE)
    return txt
    """
    return txt