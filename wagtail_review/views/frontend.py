from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.middleware.csrf import get_token as get_csrf_token
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

import jwt

from wagtail.core.models import PageRevision

from wagtail_review import models


def review(request, token):
    data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

    user = get_object_or_404(models.User, id=data['usid'])
    page_revision = get_object_or_404(PageRevision.objects.select_related('page'), id=data['prid'])
    page = page_revision.as_page_object()
    perms = user.page_perms(page)

    if not perms.can_view():
        raise PermissionDenied

    if perms.share is not None:
        perms.share.log_access()

    if 'rrid' in data:
        review_request = get_object_or_404(models.ReviewRequest, id=data['rrid'])
    else:
        review_request = None

    dummy_request = page.dummy_request(request)
    dummy_request.wagtailreview_token = token
    dummy_request.wagtailreview_perms = perms
    dummy_request.wagtailreview_review_request = review_request
    return page.serve_preview(dummy_request, page.default_preview_mode)
