from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from wagtail_review.models import Reviewer


def view(request, reviewer_id, token):
    reviewer = get_object_or_404(Reviewer, id=reviewer_id)
    if token != reviewer.view_token:
        raise PermissionDenied

    page = reviewer.review.page_revision.as_page_object()
    return page.serve_preview(page.dummy_request(request), page.default_preview_mode)


def respond(request, reviewer_id, token):
    reviewer = get_object_or_404(Reviewer, id=reviewer_id)
    if token != reviewer.response_token:
        raise PermissionDenied

    page = reviewer.review.page_revision.as_page_object()
    return page.serve_preview(page.dummy_request(request), page.default_preview_mode)
