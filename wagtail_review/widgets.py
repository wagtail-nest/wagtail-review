import json

from django import forms
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
            'reviewers_data': json.dumps(ReviewerSerializer(reviewers, many=True).data)
        })

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtail_review/js/wagtail-review-admin.js'),
        ])
