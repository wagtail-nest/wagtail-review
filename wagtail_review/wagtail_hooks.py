from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.action_menu import ActionMenuItem
from wagtail.core import hooks

from wagtail_review import admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^wagtail_review/', include(admin_urls, namespace='wagtail_review')),
    ]


# Replace 'submit for moderation' action with 'submit for review'

class SubmitForReviewMenuItem(ActionMenuItem):
    label = _("Submit for review")
    name = 'action-submit-for-review'
    template = 'wagtail_review/submit_for_review_menu_item.html'

    class Media:
        js = ['wagtail_review/js/submit.js']
        css = {
            'all': ['wagtail_review/css/create_review.css']
        }


@hooks.register('construct_page_action_menu')
def remove_submit_to_moderator_option(menu_items, request, context):
    for (i, menu_item) in enumerate(menu_items):
        if menu_item.name == 'action-submit':
            menu_items[i] = SubmitForReviewMenuItem()


def handle_submit_for_review(request, page):
    if 'action-submit-for-review' in request.POST:
        raise Exception("TODO: handle submit-for-review action")

hooks.register('after_create_page', handle_submit_for_review)
hooks.register('after_edit_page', handle_submit_for_review)
