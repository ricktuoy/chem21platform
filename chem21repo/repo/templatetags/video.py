import re

import logging

from abc import ABCMeta
from abc import abstractproperty
from abc import abstractmethod
from chem21repo.repo.models import Biblio
from chem21repo.repo.models import Lesson
from chem21repo.repo.models import Module
from chem21repo.repo.models import Question
from chem21repo.repo.models import Topic
from chem21repo.repo.models import UniqueFile
from django import template
from django.template.loader import get_template

register = template.Library()

class PlaceVideoNode(template.Node):
    def __init__(self, text_field, video_field):
        self.text = template.Variable(text_field)
        self.video = template.Variable(video_field)

    def render(self, context):
        txt = self.text.resolve(context)
        video = self.video.resolve(context)
        num_paras = txt.count("</p>") 
        vid_template = template.loader.get_template("includes/video_%s.html" % video.render_type)
        vid_cxt = video.render_args
        vid_html = vid_template.render(vid_cxt)
        if num_paras > 3:
            # display as an aside
            insert_char = txt.find("</p>")+4
            vid_html = "<aside>%s</aside>" % vid_html
            txt = txt[0:insert_char] + vid_html + txt[insert_char:]
            context['text_with_inset_video'] = txt
        context['video'] = vid_html
        return ""


@register.tag(name="try_inset_video")
def do_try_inset_video(parser, token):
    try:
        tag_name, text_field, video_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly two arguments" % token.contents.split()[
                0]
        )
    return PlaceVideoNode(text_field, video_field)
