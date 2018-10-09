from django.conf.urls import include, url
from django.contrib import messages as django_messages
from django.templatetags.static import static
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

import swapper

from wagtail.admin import messages
from wagtail.admin.menu import MenuItem
from wagtail.core import hooks

from wagtail_review import admin_urls
from wagtail_review.forms import get_review_form_class, ReviewerFormSet

Review = swapper.load_model('wagtail_review', 'Review')


# Whether to use the construct_page_action_menu hook to customise the page editor menu;
# currently disabled, but will become a Wagtail version check as and when
# https://github.com/wagtail/wagtail/pull/4781 is shipped
HAS_ACTION_MENU_HOOK = False

if HAS_ACTION_MENU_HOOK:
    from wagtail.admin.action_menu import ActionMenuItem


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^wagtail_review/', include(admin_urls, namespace='wagtail_review_admin')),
    ]


# Replace 'submit for moderation' action with 'submit for review'

if HAS_ACTION_MENU_HOOK:
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
else:
    # Fallback for construct_page_action_menu being unavailable:
    # use Javascript to replace the 'submit for moderation' button
    @hooks.register('insert_editor_css')
    def submit_for_review_css():
        return format_html(
            '<link rel="stylesheet" href="{}">',
            static('wagtail_review/css/create_review.css')
        )

    @hooks.register('insert_editor_js')
    def submit_for_review_js():
        return format_html('''
                <script>
                    $(function() {{
                        $('input[name="action-submit"]').attr({{
                            'name': 'action-submit-for-review',
                            'value': "Submit for review",
                            'data-url': "{0}"
                        }})
                    }});
                </script>
                <script src="{1}"></script>
            ''',
            reverse('wagtail_review_admin:create_review'), static('wagtail_review/js/submit.js')
        )


def handle_submit_for_review(request, page):
    if 'action-submit-for-review' in request.POST:
        ReviewForm = get_review_form_class()

        review = Review(page_revision=page.get_latest_revision(), submitter=request.user)
        form = ReviewForm(request.POST, instance=review, prefix='create_review')
        reviewer_formset = ReviewerFormSet(request.POST, instance=review, prefix='create_review_reviewers')

        # forms should already have been validated at the point of submission, so treat validation failures
        # at this point as a hard error
        if not form.is_valid():
            raise Exception("Review form failed validation")
        if not reviewer_formset.is_valid():
            raise Exception("Reviewer formset failed validation")

        form.save()
        reviewer_formset.save()

        # create a reviewer record for the current user
        review.reviewers.create(user=review.submitter)

        review.send_request_emails()

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
        return bool(Review.get_pages_with_reviews_for_user(request.user))


@hooks.register('register_admin_menu_item')
def register_images_menu_item():
    return ReviewsMenuItem(
        _('Reviews'), reverse('wagtail_review_admin:dashboard'),
        name='reviews', classnames='icon icon-tick', order=1000
    )
