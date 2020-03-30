import json

from django import forms
from django.conf import settings
from django.forms.widgets import SelectMultiple
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.staticfiles import versioned_static


class AdminReviewerChooser(SelectMultiple):

    def render(self, name, value, attrs=None, renderer=None):
        from .models import Reviewer
        from .admin_api.serializers import ReviewerSerializer

        if value:
            reviewers = Reviewer.objects.filter(id__in=value)
        else:
            reviewers = Reviewer.objects.none()

        return render_to_string("wagtail_review/widgets/reviewer_chooser.html", {
            'widget': self,
            'name': name,
            'reviewers_data': json.dumps(ReviewerSerializer(reviewers, many=True).data),
            # Get the csrf header name in case a custom one is being used
            # Replace underscores with hyphens and remove any HTTP prefix
            # as otherwise these headers will be stripped
            'csrf_header_name': getattr(settings, 'CSRF_HEADER_NAME', 'HTTP_X_CSRFTOKEN').upper().replace('_', '-').replace('HTTP-', '')
        })

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtail_review/js/wagtail-review-admin.js'),
        ])
