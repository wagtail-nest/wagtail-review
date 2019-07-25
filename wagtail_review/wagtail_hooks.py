from django.conf import settings
from django.conf.urls import include, url
from django.contrib import messages as django_messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from wagtail.admin import messages
from wagtail.admin.action_menu import ActionMenuItem
from wagtail.admin.menu import MenuItem
from wagtail.core import hooks

from wagtail_review import admin_urls
from wagtail_review.forms import ReviewAssigneeFormSet, get_review_form_class
from wagtail_review.models import ReviewRequest


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^wagtail_review/', include(admin_urls, namespace='wagtail_review_admin')),
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
        ReviewForm = get_review_form_class()

        review_request = ReviewRequest(page_revision=page.get_latest_revision(), submitted_by=request.user)
        form = ReviewForm(request.POST, instance=review_request, prefix='create_review')
        reviewer_formset = ReviewAssigneeFormSet(request.POST, prefix='create_review_assignees')

        # forms should already have been validated at the point of submission, so treat validation failures
        # at this point as a hard error
        if not form.is_valid():
            raise Exception("Review form failed validation")
        if not reviewer_formset.is_valid():
            raise Exception("Reviewer formset failed validation")

        review_request = form.save()

        for form in reviewer_formset:
            review_request.assignees.add(form.get_user(review_request))

        review_request.send_request_emails()

        # clear original confirmation message as set by the create/edit view,
        # so that we can replace it with our own
        list(django_messages.get_messages(request))

        message = _(
            "Page '{0}' has been submitted for review."
        ).format(
            page.get_admin_display_title()
        )

        messages.success(request, message)

        # redirect back to the explorer
        return redirect('wagtailadmin_explore', page.get_parent().id)


hooks.register('after_create_page', handle_submit_for_review)
hooks.register('after_edit_page', handle_submit_for_review)


class ReviewsMenuItem(MenuItem):
    def is_shown(self, request):
        return bool(ReviewRequest.get_pages_with_reviews_for_user(request.user))


@hooks.register('register_admin_menu_item')
def register_images_menu_item():
    return ReviewsMenuItem(
        _('Reviews'), reverse('wagtail_review_admin:dashboard'),
        name='reviews', classnames='icon icon-tick', order=1000
    )


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        'wagtail_review/js/wagtail-review-admin.js',
    ]
    js_includes = format_html_join(
        '\n',
        '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes


# Inject code into the action menu that tells the UI which page is being viewed
# This isn't actually a menu item. It's the only way to inject code into the Wagtail
# editor where we also have the page ID
class GuacamoleMenuItem(ActionMenuItem):
    def render_html(self, request, context):
        return mark_safe(f"<script>window.wagtailPageId = {context['page'].id};</script>")


@hooks.register('register_page_action_menu_item')
def register_guacamole_menu_item():
    return GuacamoleMenuItem(order=10)
