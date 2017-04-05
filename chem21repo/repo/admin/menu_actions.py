from django.core.urlresolvers import reverse


class BasePageMenuAction(object):
    view_name = None
    extra_args = []

    def __init__(self, page_id):
        self.page_id = page_id

    @property
    def url(self):
        return reverse(self.view_name, args=[self.page_id, ])


class EditTextAction(BasePageMenuAction):
    view_name = "admin:page_edit_text"


class LoadTextAction(BasePageMenuAction):
    view_name = "admin:page_load_text"
    extra_args = ["gdoc", ]


class AddFigureAction(BasePageMenuAction):
    view_name = "admin:page_add_figure"
    extra_args = ["para", "order"]


class RemoveFigureAction(BasePageMenuAction):
    view_name = "admin:page_remove_figure"
    extra_args = ["para", "order"]


class EditFigureAction(BasePageMenuAction):
    view_name = "admin:page_edit_figure"
    extra_args = ["para", "order"]


class AddVideoAction(BasePageMenuAction):
    view_name = "admin:page_add_video"


class EditVideoAction(BasePageMenuAction):
    view_name = "admin:page_edit_video"


class AddReferencesAction(BasePageMenuAction):
    view_name = "admin:page_add_references"
