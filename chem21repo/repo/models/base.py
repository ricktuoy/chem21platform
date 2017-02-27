from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from django.db import models
from django.db import transaction
from django.db.models import Max


class BaseModel(models.Model):
    class Meta:
        abstract = True


class OrderedModel(BaseModel):
    order = models.IntegerField(default=0)
    order_dirty = models.BooleanField(default=True)

    def move_to(self, el):
        type(self).move(self, el)

    def order_is_dirty(self):
        return self.order_dirty

    class Meta:
        abstract = True
        ordering = ('order',)


class OrderedManagerBase:
    __metaclass__ = ABCMeta

    @abstractproperty
    def order_field(self):
        return None

    @property
    def order_dirty_field(self):
        return self.order_field + "_dirty"

    @property
    def force_reset_order(self):
        return True

    @abstractmethod
    def order_queryset(self):
        return None

    @property
    def new_order_val(self):
        max_order = self.order_queryset().aggregate(
            Max('order'))['order__max']
        if not max_order:
            max_order = 0
        return max_order + 1

    def order_incr_dict(self):
        return {self.order_field: models.F(self.order_field) + 1,
                self.order_dirty_field: True}

    def order_decr_dict(self):
        return {self.order_field: models.F(self.order_field) - 1,
                self.order_dirty_field: True}

    def order_slice_dict(self, val1, val2):
        return {self.order_field + "__gt": val1,
                self.order_field + "__lte": val2}

    def get_order_value(self, el):
        return getattr(el, self.order_field)

    def set_order_value(self, el, val):
        setattr(el, self.order_dirty_field, True)
        return setattr(el, self.order_field, val)

    def order_sum(self):
        # gets sum of orders from DB. should be equal to self.order_triangle if
        # DB is consistent
        q = self.order_queryset().aggregate(
            order_sum=models.Sum(self.order_field))
        return q['order_sum']

    def order_triangle(self):
        # calculates what sum of orders from DB should be if consistent
        n = self.order_queryset().count()
        return (n * (n + 1)) / 2

    def _reset_order(self):
        i = 1
        for o in self.order_queryset().order_by(self.order_field):
            print i
            self.set_order_value(o, i)
            i += 1
            o.save()

    def _ensure_order_consistent(self):
        """ Check orders are consistent in DB, else recalculates """
        if self.order_sum() != self.order_triangle() or \
                self.force_reset_order is True:
            self._reset_order()
            self._have_reset_order = True
        else:
            self._have_reset_order = False
        return self._have_reset_order

    def _load_obj_from_arg(self, arg):
        # make sure we have up-to-date objects loaded from DB after reset
        # if args are integers (PKs) load the object now
        if self._have_reset_order or isinstance(arg, (int, long)):
            try:
                elId = arg.id
            except AttributeError:
                elId = arg
            return self.model.objects.get(pk=elId)
        return arg

    def save_structure_change(self):
        for qs in self.touched_structure_querysets:
            qs.update(changed=True)

    @transaction.atomic
    def move_to_top(self, source, parent=None):
        if parent:
            try:
                self.set_m2m_key_value(parent)
            except AttributeError:
                pass
        self._current_element = source
        self._ensure_order_consistent()
        source = self._load_obj_from_arg(source)
        self._current_element = source

        sval = self.get_order_value(source)
        self.order_queryset().filter(
            **self.order_slice_dict(0, sval)).update(**self.order_incr_dict())
        self.set_order_value(source, 1)
        source.save_structure_change()
        return (True, "Success")

    @transaction.atomic
    def move(self, source, dest, parent=None):
        if parent:
            try:
                self.set_m2m_key_value(parent)
            except AttributeError:
                pass

        self._current_element = source
        self._current_target_element = dest
        self._ensure_order_consistent()
        source = self._load_obj_from_arg(source)
        dest = self._load_obj_from_arg(dest)
        self._current_element = source
        self._current_target_element = dest

        # get current orders
        sval = self.get_order_value(source)
        dval = self.get_order_value(dest)

        if sval == dval:
            return (False, "Destination file same as file being moved")
        elif sval < dval:
            self.order_queryset().filter(
                **self.order_slice_dict(
                    sval, dval)
            ).update(
                **self.order_decr_dict())
        elif sval > dval:
            self.order_queryset().filter(
                **self.order_slice_dict(
                    dval, sval)
            ).update(
                **self.order_incr_dict())

        self.set_order_value(source, dval + 1)
        source.save()
        source.save_structure_change()

        return (True, "Success")


class OrderedRelationalManagerBase(OrderedManagerBase):

    @abstractproperty
    def order_key(self):
        return None

    def _get_order_key_value(self):
        return getattr(self._current_element, self.order_key)

    def order_queryset(self):
        return self.get_queryset().filter(
            **{self.order_key: self._get_order_key_value()})


class OrderedManyToManyManagerBase(OrderedRelationalManagerBase):

    def set_m2m_key_value(self, val):
        self._current_m2m_key_value = val

    def get_m2m_key_value(self):
        return self._current_m2m_key_value

    def order_queryset(self):
        return self.get_queryset().filter(
            **{self.order_key + "__pk": self.get_m2m_key_value()})


class OrderedManager(models.Manager, OrderedManagerBase):

    @property
    def order_field(self):
        return "order"

    def order_queryset(self, el=None, new_parent=None):
        return self.get_queryset()

    def get_queryset(self):
        return super(OrderedManager, self).get_queryset()


class ActiveManager(models.Manager):

    def get_queryset(self):
        return super(ActiveManager, self).get_queryset().filter(active=True)


def UnicodeMixinFactory(name_field):

    class _NameMixin(object):

        def __unicode__(self):
            try:
                n = getattr(self, name_field)
                if n:
                    return n
                else:
                    return ""
            except TypeError:
                return " ".join([unicode(getattr(self, field))
                                 for field in name_field])
    return _NameMixin


NameUnicodeMixin = UnicodeMixinFactory("name")
NameUnicodeMixin.__name__ = "NameUnicodeMixin"
PathUnicodeMixin = UnicodeMixinFactory("path")
PathUnicodeMixin.__name__ = "PathUnicodeMixin"
TitleUnicodeMixin = UnicodeMixinFactory("title")
TitleUnicodeMixin.__name__ = "TitleUnicodeMixin"


