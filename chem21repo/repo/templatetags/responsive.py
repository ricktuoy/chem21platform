import logging
from django import template
from BeautifulSoup import BeautifulSoup
register = template.Library()

@register.filter
def responsivise(txt):
    soup = BeautifulSoup(txt)
    els = soup.findAll("table", recursive=False)
    for tab in els:
        tab['class'] = " ".join(tab.get('class', []) + ['ui-responsive',])
        tab['data-role'] = "table"
    return soup.prettify()