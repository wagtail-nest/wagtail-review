from django.utils.translation import ugettext_lazy as _

from wagtail.admin.action_menu import ActionMenuItem
from wagtail.core import hooks


# Replace 'submit for moderation' action with 'submit for review'

class SubmitForReviewMenuItem(ActionMenuItem):
    label = _("Submit for review")
    name = 'action-submit-for-review'

    class Media:
        js = ['wagtail_review/js/submit.js']


@hooks.register('construct_page_action_menu')
def remove_submit_to_moderator_option(menu_items, request, context):
    for (i, menu_item) in enumerate(menu_items):
        if menu_item.name == 'action-submit':
            menu_items[i] = SubmitForReviewMenuItem()
