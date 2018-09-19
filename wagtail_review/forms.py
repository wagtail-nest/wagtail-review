from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from wagtail_review.models import get_review_model


class CreateReviewForm(forms.ModelForm):
    class Meta:
        model = get_review_model()
        fields = []


def get_review_form_class():
    """
    Get the review form class from the ``WAGTAILREVIEW_REVIEW_FORM`` setting.
    """
    form_class_name = getattr(settings, 'WAGTAILREVIEW_REVIEW_FORM', 'wagtail_review.Review')
    try:
        return import_string(form_class_name)
    except ImportError:
        raise ImproperlyConfigured(
            "WAGTAILREVIEW_REVIEW_FORM refers to a form '%s' that is not available" % form_class_name
        )
