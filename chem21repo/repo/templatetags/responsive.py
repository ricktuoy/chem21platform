import logging
from django import template
from BeautifulSoup import BeautifulSoup
register = template.Library()

@register.filter
def responsivise(txt):
    soup = BeautifulSoup(txt)
    els = soup.findAll("table", recursive=False)
    logging.debug("Soup!")
    for tab in els:
        logging.debug("Found tab")
    	cls = tab.get('class', [])
    	try:
        	tab['class'] = " ".join(cls + ['ui-responsive',])
        except TypeError:
        	tab['class'] = "%s ui-responsive" % cls
        tab['data-role'] = "table"

    return soup.prettify()