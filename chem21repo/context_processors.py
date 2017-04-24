from chem21repo.repo.admin.menu_actions import PageActionRegistry
import logging


def page_admin_menu(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return {}
    return {}
