from unittest import TestCase

from django.conf import settings

from chem21repo.repo.models import UniqueFile
from chem21repo.repo.shortcodes import HTMLShortcodeParser, FigureGroupProcessor
from chem21repo.repo.shortcodes.renderers import FigureGroupRenderer, FigureRenderer


class StubFileObj:

    def __init__(self, pk, url):
        self.pk = pk
        self.url = url

    def get_absolute_url(self):
        return self.url


class FigureShortcodeTestCase(TestCase):
    para_text = "<p>Pellentesque habitant morbi tristique senectus et netus " + \
                "et malesuada fames ac turpis egestas.</p>"

    def get_n_paras(self, n):
        return "".join([self.para_text for _ in range(0, n)])

    def test_that_figure_can_be_inserted_within_figgroup(self):
        input_html = self.get_n_paras(5)

        figure_renderers = [FigureRenderer(StubFileObj(i, "/img/%s.jpg" % i), alt="Image %s" % i) for i in range(0, 1)]

        renderer = FigureGroupRenderer(figures=figure_renderers)

        parser = HTMLShortcodeParser(input_html)
        output_html = parser.insert_shortcode(3, renderer)
        expected_shortcode = "<p>[figgroup:figure:][figure:local:0:Image 0][/figgroup]</p>"

        self.assertEqual(output_html, self.get_n_paras(3) + expected_shortcode + self.get_n_paras(2))

    def test_that_multiple_figures_can_be_inserted_within_figgroup(self):
        input_html = self.get_n_paras(5)

        figure_renderers = [FigureRenderer(StubFileObj(i, "/img/%s.jpg" % i), alt="Image %s" % i) for i in range(0, 4)]

        renderer = FigureGroupRenderer(figures=figure_renderers, layout=['stacked2'])

        parser = HTMLShortcodeParser(input_html)
        output_html = parser.insert_shortcode(1, renderer)
        expected_shortcode = "<p>[figgroup:figure:stacked2][figure:local:0:Image 0][figure:local:1:Image 1]" + \
                             "[figure:local:2:Image 2][figure:local:3:Image 3][/figgroup]</p>"

        self.assertEqual(output_html, self.get_n_paras(1) + expected_shortcode + self.get_n_paras(4))

    def test_that_figgroups_are_rendered_as_html(self):
        input_html = self.get_n_paras(5)
        files = [self._create_file(i) for i in range(0, 4)]
        figure_renderers = [FigureRenderer(file_obj=f, alt="Image %s" % f.pk) for f in files]

        renderer = FigureGroupRenderer(figures=figure_renderers)

        parser = HTMLShortcodeParser(input_html)
        shortcode_html = parser.insert_shortcode(1, renderer)
        parser2 = HTMLShortcodeParser(shortcode_html)
        parser2.register_block_shortcode(FigureGroupProcessor)

        output_html = parser2.get_rendered_html()

        expected_rendered_html = "<aside><figure class=\" inline\">"
        expected_rendered_html += "".join([self._expected_rendered_image_html(f) for f in files])
        expected_rendered_html += "</figure></aside>"

        self.assertEqual(output_html, self.get_n_paras(1) + expected_rendered_html + self.get_n_paras(4))

    def _expected_rendered_image_html(self, f):
        html_template = "<a href=\"{media_uri}image/{id}.jpg\" title=\"image/{id}\">" + \
                        "<img src=\"{media_uri}image/{id}.jpg\" alt=\"Image {id}\" /></a>"
        return html_template.format(
            media_uri=settings.MEDIA_URL + "sources/", id=f.pk)

    def _create_file(self, id):
        f = UniqueFile(pk=id)
        f.filename = "image/%s.jpg" % id
        f.save()
        return f
