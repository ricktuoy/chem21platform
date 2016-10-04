import logging
from django import template
from BeautifulSoup import BeautifulSoup
register = template.Library()

@register.filter
def responsivise(txt):
    soup = BeautifulSoup(txt)
    els = soup.findAll("table", recursive=False)
    for tab in els:
    	cls = tab.get('class', [])
    	try:
        	tab['class'] = " ".join(cls + ['ui-responsive',])
        except TypeError:
        	tab['class'] = "%s ui-responsive" % cls
        tab['data-role'] = "table"

    els = soup.findAll("a", recursive=True)
    for a in els:
        href = a.get('href', "")
        href = href.replace("https://www.google.com/url?q=","")
        a['href'] = href
    return soup.prettify()