from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from wagtail_review.forms import ResponseForm
from wagtail_review.models import Response, Reviewer


def view(request, reviewer_id, token):
    reviewer = get_object_or_404(Reviewer, id=reviewer_id)
    if token != reviewer.view_token:
        raise PermissionDenied

    page = reviewer.review.page_revision.as_page_object()
    dummy_request = page.dummy_request(request)
    dummy_request.wagtailreview_mode = 'view'
    dummy_request.wagtailreview_reviewer = reviewer
    return page.serve_preview(dummy_request, page.default_preview_mode)


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
            return HttpResponse("Thank you, your review has been received.")

    else:
        page = reviewer.review.page_revision.as_page_object()
        dummy_request = page.dummy_request(request)
        dummy_request.wagtailreview_mode = 'respond'
        dummy_request.wagtailreview_reviewer = reviewer
        return page.serve_preview(dummy_request, page.default_preview_mode)
