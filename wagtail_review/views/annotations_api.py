from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect


def root(request):
    return JsonResponse({
        "name": "Annotator Store API",
        "version": "2.0.0"
    })


def index(request):
    if request.method == 'POST':
        return redirect('wagtail_review:annotations_api_item', 0)
    else:
        return HttpResponseNotAllowed(['POST'], "Method not allowed")


def item(request, id):
    if request.method == 'GET':
        return JsonResponse({
            'id': id,
            'text': 'hello',
            'quote': 'world',
            'ranges': []
        })
    else:
        return HttpResponseNotAllowed(['GET'], "Method not allowed")


def search(request):
    results = []
    return JsonResponse({
        'total': len(results),
        'rows': results
    })
