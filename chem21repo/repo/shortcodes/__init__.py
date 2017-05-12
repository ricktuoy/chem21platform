from .processors import *
from .errors import *
import re






class Token(object):

    @classmethod
    def processor_from_name(kls, nm):
        return eval(nm.capitalize() + "Processor")

    @classmethod
    def class_from_name(kls, nm):
        return eval(nm.capitalize() + "Token")

    @classmethod
    def create(kls, tp, para, fig, question, *args, **kwargs):
        token_class = kls.class_from_name(tp)
        return token_class(para=para, question=question, fig=fig,
                           *args, **kwargs)

    @classmethod
    def get(kls, tp, para, fig, question):
        token_class = kls.class_from_name(tp)
        return token_class.get(para=para, question=question, fig=fig,
            order=order)