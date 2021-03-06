import logging
import urllib
from django import template
from BeautifulSoup import BeautifulSoup
register = template.Library()

@register.filter
def responsivise(txt):
    #return txt
    soup = BeautifulSoup(txt)
    els = soup.findAll("table", recursive=True)
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
        ghref = href.replace("https://www.google.com/url?q=","")
        if ghref != href:
            href = ghref
            try:
                href, bobbins = href.split("&sa=", 1)
                href = urllib.unquote(href)
            except ValueError:
                pass
        a['href'] = href
    return unicode(soup)