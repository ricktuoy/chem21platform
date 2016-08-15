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
from citeproc.types import WEBPAGE


class BibTeXParsing(object):

    @classmethod
    def get_html_from_bibref(kls, ref, url):
        if url:
            ref = kls._title_pattern.sub(kls._get_replace_title(url), ref)
        return kls._tag_pattern.sub(kls._replace_tag, ref)

    @classmethod
    def get_bib_raw(kls, f):
        kls._key_count = 1
        bib_raw = kls._key_pattern.sub(kls._key_rep_callback, f.read().decode("utf-8"))
        bib_raw = kls._hyphen_pattern.sub(kls._hyphen_rep_callback, bib_raw)
        bib_raw = kls._webpage_pattern.sub(kls._webpage_rep_callback, bib_raw)
        bib_raw = bib_raw.replace("\ufeff","" )
        return bib_raw
        #
    @classmethod
    def get_bib_source(kls, bib_raw):
        BT = kls._get_bibtex_class()
        with tempfile.NamedTemporaryFile(dir="/tmp", delete=False) as tf:
            tf.write(bib_raw.encode("ascii","ignore"))
            fname = tf.name
        bib_source = BT(fname)
        os.remove(fname)
        return bib_source

    @staticmethod
    def _get_bibtex_class():
        from citeproc.source import Reference
        class BibTeXmod(BibTeX):
            # PATCHES 0.3.0 to trunk ...
            MONTHS = ('jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
            RE_DAY = '(?P<day>\d+)'
            RE_MONTH = '(?P<month>\w+)'
            @staticmethod
            def _parse_month(month):
                def month_name_to_index(name):
                    try:
                        return BibTeXmod.MONTHS.index(name[:3].lower()) + 1
                    except ValueError:
                        return int(name)

                begin = {}
                end = {}
                month = month.strip()
                month = month.replace(', ', '-')
                if month.isdecimal():
                    begin['month'] = end['month'] = month
                elif month.replace('-', '').isalpha():
                    if '-' in month:
                        begin['month'], end['month'] = month.split('-')
                    else:
                        begin['month'] = end['month'] = month
                else:
                    m = re.match(BibTeXmod.RE_DAY + '[ ~]*' + BibTeXmod.RE_MONTH, month)
                    if m is None:
                        m = re.match(BibTeXmod.RE_MONTH + '[ ~]*' + BibTeXmod.RE_DAY, month)
                    begin['day'] = end['day'] = int(m.group('day'))
                    begin['month'] = end['month'] = m.group('month')
                begin['month'] = month_name_to_index(begin['month'])
                end['month'] = month_name_to_index(end['month'])
                return begin, end
            def create_reference(self, key, bibtex_entry):
                csl_type = self.types[bibtex_entry.document_type]
                csl_fields = self._bibtex_to_csl(bibtex_entry)
                csl_date = self._bibtex_to_csl_date(bibtex_entry)
                if csl_date:
                    if csl_type == self.types['webpage']:
                        csl_fields['accessed'] = csl_date
                    else:
                        csl_fields['issued'] = csl_date
                return Reference(key, csl_type, **csl_fields)
        BibTeXmod.fields['doi'] = "DOI"
        BibTeXmod.fields['url'] = "url"
        BibTeXmod.fields['month'] = "month"
        BibTeXmod.fields['year'] = "year"
        BibTeXmod.types['webpage'] = WEBPAGE
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
    def get_doi_url(entry):
        doi = None
        url = None
        

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

        return (doi, url)


    #-------------------------------------------------- REGEX
    _key_pattern = re.compile(r'\@(\w+)\{\s+')
    @classmethod
    def _key_rep_callback(kls, match):
        key = "@%s{k_%d,\r\n" % (match.group(1), kls._key_count)
        kls._key_count += 1
        return key
    
    # relies on new lines and quotes in Bibtex file
    #_webpage_pattern_str_1 = 
    _webpage_pattern = re.compile(r'^\@MISC\{(?P<key>.*?)$(?P<atts1>.*?)^\s*note\s*=\s*\"Accessed\:\s*(?P<year>.*?)-(?P<month>.*?)-.*?$(?P<atts2>.*?)^\s*\}\s*$', re.MULTILINE|re.DOTALL)
    @staticmethod
    def _webpage_rep_callback(match):
        return "@WEBPAGE{%s%s  year\t= %s,\n  month\t= \"%s\",%s}\n" % (
            match.group('key'), 
            match.group('atts1'),
            match.group('year'),
            match.group('month'),
            match.group('atts2'))

    _hyphen_pattern = re.compile(r'\{(\d+)-(\d+)\}')
    @staticmethod
    def _hyphen_rep_callback(match):
        return "{%s--%s}" % (match.group(1), match.group(2))

    _title_pattern = re.compile(r'\{\{title\:(.*?)\}\}', re.DOTALL)

    @staticmethod
    def _get_replace_title(url):
        def _replace_title_link(match):
            return "<a class=\"citeproc-title\" href=\"%s\">%s</a>" % (url, match.group(1))
        return _replace_title_link

    _tag_pattern = re.compile(r'\{\{(\w+?)\:(.*?)\}\}', re.DOTALL)
    @staticmethod
    def _replace_tag(match):
        return "<span class=\"citeproc-%s\">%s</span>" % (match.group(1), match.group(2))