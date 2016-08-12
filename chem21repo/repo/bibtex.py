import re
import os
import tempfile
from django.conf import settings
from citeproc.py2compat import *

# The references are parsed from a BibTeX database, so we import the
# corresponding parser.
from citeproc.source.bibtex import BibTeX

# Import the citeproc-py classes we'll use below.
from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation, CitationItem


class BibTeXParsing(object):

    @classmethod
    def get_html_from_bibref(kls, ref, url):
        if url:
            ref = kls._title_pattern.sub(kls._get_replace_title(url), ref)
        return kls._tag_pattern.sub(kls._replace_tag, ref)

    @classmethod
    def get_bib_source(kls, f):
        BT = kls._get_bibtex_class()
        kls._key_count = 1
        bib_raw = kls._key_pattern.sub(kls._key_rep_callback, f.read().decode("utf-8"))
        bib_raw = kls._hyphen_pattern.sub(kls._hyphen_rep_callback, bib_raw)
        bib_raw = bib_raw.replace("\ufeff","" )
        with tempfile.NamedTemporaryFile(dir="/tmp", delete=False) as tf:
            tf.write(bib_raw.encode("ascii","ignore"))
            fname = tf.name
        bib_source = BT(fname)
        os.remove(fname)
        return bib_source, bib_raw

    @staticmethod
    def _get_bibtex_class():
        BibTeXmod = BibTeX
        BibTeXmod.fields['doi'] = "DOI"
        BibTeXmod.fields['url'] = "url"
        return BibTeXmod

    @staticmethod
    def get_bibliography_ordered(bib_source):
        csl_path = settings.CITEPROC_DEFAULT_STYLE_PATH
        bib_style = CitationStylesStyle(csl_path, validate=False)
        bibliography = CitationStylesBibliography(bib_style, bib_source,
                                          formatter.plain)
        order = []
        for k in bib_source:
            cite = Citation([CitationItem(k)])
            bibliography.register(cite)
            order.append(k)
        return (bibliography, order)

    @staticmethod
    def get_issn_doi_url(entry):
        issn = None
        doi = None
        url = None
        if 'ISSN' in entry:
            issn = str(entry['ISSN'])
            try:
                new, cruft = issn.split(",", 1)
                issn = new
            except ValueError:
                pass

        if 'DOI' in entry:
            doi = str(entry['DOI'])
            url = "http://dx.doi.org/%s" % doi
        elif 'url' in entry:
            url = str(entry['url'])
            try:
                new, cruft = url.split("", 1)
                url = new
            except ValueError:
                pass

        return (issn, doi, url)

    #-------------------------------------------------- REGEX
    _key_pattern = re.compile(r'\@(\w+)\{\s+')
    @classmethod
    def _key_rep_callback(kls, match):
        key = "@%s{k_%d,\r\n" % (match.group(1), kls._key_count)
        kls._key_count += 1
        return key
    
    # relies on new lines and quotes 
    _webpage_pattern = re.compile(r'\^@MISC\{(?P<key>.*?,?)$(?P<atts1>.*?)^\s*note\s*=\s*\"Accessed\:\s*(?P<year>.*?)-(?P<month>.*?)-.*$(<?P<atts2>.*?)^\s*\}\s*$')
    @staticmethod
    def _webpage_rep_callback(match):
        return "@WEBPAGE{%s\n%s\nyear=%s\nmonth=%s\n%s\n}" % (
            match.group('key'), 
            match.group('atts1'),
            match.group('year'),
            match.group('month'),
            match.group('atts2'))

    _hyphen_pattern = re.compile(r'\{(\d+)-(\d+)\}')
    @staticmethod
    def _hyphen_rep_callback(match):
        return "{%s--%s}" % (match.group(1), match.group(2))

    _title_pattern = re.compile(r'\{\{title\:(.*?)\}\}')

    @staticmethod
    def _get_replace_title(url):
        def _replace_title_link(match):
            return "<a class=\"citeproc-title\" href=\"%s\">%s</a>" % (url, match.group(1))
        return _replace_title_link

    _tag_pattern = re.compile(r'\{\{(\w+?)\:(.*?)\}\}')
    @staticmethod
    def _replace_tag(match):
        return "<span class=\"citeproc-%s\">%s</span>" % (match.group(1), match.group(2))