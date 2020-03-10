from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

import jwt
from wagtail.core.models import PageRevision

from wagtail_review import models


def review(request, token):
    data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

    reviewer = get_object_or_404(models.Reviewer, id=data['rvid'])
    page_revision = get_object_or_404(PageRevision.objects.select_related('page'), id=data['prid'])
    page = page_revision.as_page_object()
    perms = reviewer.page_perms(page)

    if not perms.can_view():
        raise PermissionDenied

    if perms.share is not None:
        perms.share.log_access()

    if 'tsid' in data:
        task_state = get_object_or_404(models.TaskState, id=data['tsid'])
    else:
        task_state = None

    return page.make_preview_request(
        original_request=request,
        extra_request_attrs={
            'wagtailreview_token': token,
            'wagtailreview_perms': perms,
            'wagtailreview_task_state': task_state,
        }
    )
