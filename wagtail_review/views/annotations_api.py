import json

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.cache import never_cache

from wagtail_review.models import Annotation, Reviewer


def _check_reviewer_credentials(request):
    try:
        mode = request.META.get('HTTP_X_WAGTAILREVIEW_MODE') or request.GET['mode']
        reviewer_id = request.META.get('HTTP_X_WAGTAILREVIEW_REVIEWER') or request.GET['reviewer']
        token = request.META.get('HTTP_X_WAGTAILREVIEW_TOKEN') or request.GET['token']
        reviewer = Reviewer.objects.get(id=reviewer_id)
    except (KeyError, Reviewer.DoesNotExist):
        raise PermissionDenied

    if (mode == 'respond' or mode == 'comment') and token == reviewer.response_token:
        pass
    elif mode == 'view' and token == reviewer.view_token:
        pass
    else:
        raise PermissionDenied

    return (reviewer, mode)


def root(request):
    return JsonResponse({
        "name": "Annotator Store API",
        "version": "2.0.0"
    })


@never_cache
def index(request):
    reviewer, mode = _check_reviewer_credentials(request)

    if request.method == 'GET':
        results = [
            annotation.as_json_data()
            for annotation in reviewer.review.get_annotations()
        ]
        return JsonResponse(results, safe=False)

    elif request.method == 'POST':
        if mode not in ('respond', 'comment'):
            raise PermissionDenied

        if reviewer.review.status == 'closed':
            raise PermissionDenied

        data = json.loads(request.body)

        annotation = reviewer.annotations.create(quote=data['quote'], text=data['text'])
        for r in data['ranges']:
            annotation.ranges.create(
                start=r['start'], start_offset=r['startOffset'], end=r['end'], end_offset=r['endOffset']
            )

        return redirect('wagtail_review:annotations_api_item', annotation.id)
    else:
        return HttpResponseNotAllowed(['GET', 'POST'], "Method not allowed")


@never_cache
def item(request, id):
    reviewer, mode = _check_reviewer_credentials(request)

    if request.method == 'GET':
        annotation = get_object_or_404(Annotation, id=id)

        # only allow retrieving annotations within the same review as the current user's credentials
        if reviewer.review != annotation.reviewer.review:
            raise PermissionDenied

        return JsonResponse(annotation.as_json_data())

    else:
        return HttpResponseNotAllowed(['GET'], "Method not allowed")


@never_cache
def search(request):
    reviewer, mode = _check_reviewer_credentials(request)

    results = [
        annotation.as_json_data()
        for annotation in reviewer.review.get_annotations()
    ]
    return JsonResponse({
        'total': len(results),
        'rows': results
    })
