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
from django.core.urlresolvers import reverse
from django import template
from django.template.loader import get_template
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup
import logging

register = template.Library()

class PlaceVideoNode(template.Node):
    def __init__(self, text_field, video_field):
        self.text = template.Variable(text_field)
        self.video = template.Variable(video_field)

    def render(self, context):
        txt = self.text.resolve(context)
        video = self.video.resolve(context)
        soup = BeautifulSoup(txt)
        els = soup.findAll(True, recursive=False)
        num_blocks = len(els)
        vid_template = template.loader.get_template("includes/video_youtube.html")
        vid_cxt = video.render_args
        request = context['request']

        vid_cxt['tools'] = not context.get('staticgenerator', False) and request.user.is_authenticated()
        obj = context['object']
        try:
            par = obj.get_parent()
        except:
            par = None
        vid_cxt['vid_pk'] = video.pk
        vid_cxt['front_slide_url'] = video.get_video_slide_url(par, obj) 
        vid_cxt['remove_url'] = reverse("media_detach", kwargs={'type':obj.learning_object_type, 'tpk': obj.pk, 'fpk':video.pk})
        vid_cxt['module_title'] = par.title
        vid_cxt['title'] = obj.title
        vid_cxt['lobj_pk'] = obj.pk
        vid_cxt['lobj_type'] = obj.learning_object_type
        vid_cxt['authors'] = video.author_string
        vid_cxt['timeline_url'] = reverse("video_timeline", kwargs={'pk':video.pk})
        vid_html = vid_template.render(vid_cxt)
        if num_blocks > 0:
            # display as an aside
            html_class = "half"
            if html_class:
                html_class = " class=\"%s\"" % html_class
            vid_html = "<aside%s>%s</aside>" % (html_class, vid_html)
            context['pre_content'] = context.get('pre_content', "") + vid_html
            return ""
        else:
            context['video'] = vid_html
        return ""

@register.tag(name="get_video")
def do_try_inset_video(parser, token):
    try:
        tag_name, text_field, video_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly two arguments" % token.contents.split()[
                0]
        )
    return PlaceVideoNode(text_field, video_field)
