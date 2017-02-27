from django.db import models


class Biblio(models.Model):
    citekey = models.CharField(max_length=300, unique=True)
    DOI = models.CharField(max_length=300, unique=True, null=True, blank=True)
    bibkey = models.CharField(
        max_length=300, unique=True,
        null=True, blank=True)
    title = models.CharField(max_length=500, blank=True, default="")
    display_string = models.CharField(max_length=1000, blank=True, default="")
    inline_html = models.TextField(null=True, blank=True)
    footnote_html = models.TextField(null=True, blank=True)
    unknown = models.BooleanField(default=False)

    """

    def bust(self):
        self._get_html_from_drupal()


    def _get_html_from_drupal(self):
        try:
            api = C21RESTRequests()
            ret = api.get_endnote_html(self.citekey)
            self.inline_html = ret[0]['html']
            self.footnote_html = self.inline_html
            self.title = ret[0]['value']
            self.save()
        except IndexError:
            self.unknown = True
            self.inline_html = ""
            self.footnote_html = ""
            self.title = ""
            self.save()
            raise Biblio.DoesNotExist(
                "Unknown reference: '%s'." % self.citekey)
    """

    def get_inline_html(self):
        if self.unknown:
            return False
        if not self.inline_html:
            return ""
        return self.inline_html

    def get_footnote_html(self):
        if self.unknown:
            return False
        if not self.footnote_html:
            return ""
        return self.footnote_html

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "title__icontains", )

    def __unicode__(self):
        return self.citekey + ": " + self.title
