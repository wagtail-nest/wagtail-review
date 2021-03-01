from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.middleware.csrf import get_token as get_csrf_token
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from wagtail import VERSION as WAGTAIL_VERSION
from wagtail_review.forms import ResponseForm
from wagtail_review.models import Response, Reviewer

SUCCESS_RESPONSE_MESSAGE = "Thank you, your review has been received."


def view(request, reviewer_id, token):
    reviewer = get_object_or_404(Reviewer, id=reviewer_id)
    if token != reviewer.view_token:
        raise PermissionDenied

    page = reviewer.review.page_revision.as_page_object()
    if WAGTAIL_VERSION < (2, 7):
        dummy_request = page.dummy_request(request)
        dummy_request.wagtailreview_mode = 'view'
        dummy_request.wagtailreview_reviewer = reviewer
        return page.serve_preview(dummy_request, page.default_preview_mode)
    else:
        return page.make_preview_request(
            original_request=request,
            extra_request_attrs={
                'wagtailreview_mode': 'view',
                'wagtailreview_reviewer': reviewer,
            }
        )


def respond(request, reviewer_id, token):
    reviewer = get_object_or_404(Reviewer, id=reviewer_id)
    if token != reviewer.response_token:
        raise PermissionDenied

    if request.method == 'POST':
        response = Response(reviewer=reviewer)
        form = ResponseForm(request.POST, instance=response)
        if form.is_valid() and reviewer.review.status != 'closed':
            form.save()
            response.send_notification_to_submitter()
            if request.user.has_perm('wagtailadmin.access_admin'):
                messages.success(request, SUCCESS_RESPONSE_MESSAGE)
                return redirect(reverse('wagtail_review_admin:dashboard'))
            return HttpResponse(SUCCESS_RESPONSE_MESSAGE)

    else:
        page = reviewer.review.page_revision.as_page_object()
        # Fetch the CSRF token so that Django will return a set-cookie header in the case that this is
        # the user's first request, and ensure that the dummy request (where the submit-review form is
        # rendered) is using the same token
        get_csrf_token(request)

        if WAGTAIL_VERSION < (2, 7):
            dummy_request = page.dummy_request(request)
            dummy_request.META["CSRF_COOKIE"] = request.META["CSRF_COOKIE"]

            dummy_request.wagtailreview_mode = 'respond'
            dummy_request.wagtailreview_reviewer = reviewer
            return page.serve_preview(dummy_request, page.default_preview_mode)
        else:
            return page.make_preview_request(
                original_request=request,
                extra_request_attrs={
                    'wagtailreview_mode': 'respond',
                    'wagtailreview_reviewer': reviewer,
                }
            )