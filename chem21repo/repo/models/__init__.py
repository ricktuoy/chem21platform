from functools import wraps

from .base import *
from .biblio import *
from .google import *
from .legacy import *
from .media import *
from .sco_base import *
from .scorm import *
from .scos import *
from .versions import *


def disable_for_loaddata(signal_handler):
    """
    Decorator that turns off signal handlers when loading fixture data.
    """

    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if 'raw' in kwargs.keys() and kwargs['raw']:
            return
        signal_handler(*args, **kwargs)

    return wrapper

@receiver(models.signals.pre_save)
@disable_for_loaddata
def generate_dirty_record(sender,
                          instance, raw,
                          using, update_fields,
                          **kwargs):
    if isinstance(instance, SCOBase) \
            and not isinstance(instance, UniqueFile):
        instance.changed = True

@receiver(models.signals.pre_save)
@disable_for_loaddata
def save_slug(sender, instance, **kwargs):
    if isinstance(instance, Question) or isinstance(instance, Lesson) \
            or isinstance(instance, Topic) or isinstance(instance, Module):
        if not instance.slug:
            instance.slug = slugify(instance.title)

@receiver(models.signals.pre_save, dispatch_uid="save_order")
@disable_for_loaddata
def save_order(sender, instance, **kwargs):
    if not (
            isinstance(instance, Lesson) or
            isinstance(instance, Topic) or
            isinstance(instance, Module)):
        return
    if isinstance(instance, OrderedModel):
        if not instance.order:
            try:
                # insert at end
                instance.order = sender.objects.new_order_val
            except Exception, e:
                logging.debug(type(e))
                logging.debug(e)


@receiver(models.signals.post_save, dispatch_uid="create_child")
@disable_for_loaddata
def create_page(sender, instance, **kwargs):
    if not (
            isinstance(instance, Lesson) or
            isinstance(instance, Topic) or
            isinstance(instance, Module)):
        return
    if instance.page:
        return
    else:
        pg = Question()
    instance.copy_page_fields_to(pg)
    pg.save()
    instance.page = pg
    instance.save()

@receiver(models.signals.post_save, dispatch_uid="set_changed")
@disable_for_loaddata
def set_changed(sender, instance, **kwargs):
    if isinstance(instance, SCOBase) \
            and not isinstance(instance, UniqueFile):
        for qs in instance.touched_structure_querysets:
            qs.update(changed=True)

@receiver(models.signals.m2m_changed)
@disable_for_loaddata
def save_m2m_order(
        sender, instance, action,
        reverse, model, pk_set, **kwargs):
    if not (
            isinstance(instance, Question) or
            isinstance(instance, Lesson) or
            isinstance(instance, Topic) or
            isinstance(instance, Module)):
        return
    if action != "post_add":
        return
    if not reverse:
        children = [instance, ]
        parents = list(model.objects.filter(pk__in=pk_set))
        child_model = instance.__class__
    else:
        children = list(model.objects.filter(pk__in=pk_set))
        parents = [instance, ]
        child_model = model
    for c in children:
        if not c.order:
            c.order = 0
            child_model.objects._current_element = c
            for p in parents:
                child_model.objects.set_m2m_key_value(p.pk)
                new_order = child_model.objects.new_order_val
                if new_order > c.order:
                    c.order = new_order
            child_model.objects._ensure_order_consistent()
            c.save()
