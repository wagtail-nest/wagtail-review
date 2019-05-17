from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.forms.formsets import DELETION_FIELD_NAME
from django.utils.module_loading import import_string
from django.utils.translation import ugettext

import swapper

from wagtail_review.models import Reviewer, Response

Review = swapper.load_model('wagtail_review', 'Review')


class CreateReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = []


def get_review_form_class():
    """
    Get the review form class from the ``WAGTAILREVIEW_REVIEW_FORM`` setting.
    """
    form_class_name = getattr(settings, 'WAGTAILREVIEW_REVIEW_FORM', 'wagtail_review.forms.CreateReviewForm')
    try:
        return import_string(form_class_name)
    except ImportError:
        raise ImproperlyConfigured(
            "WAGTAILREVIEW_REVIEW_FORM refers to a form '%s' that is not available" % form_class_name
        )


class BaseReviewerFormSet(forms.BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()

    def clean(self):
        # Confirm that at least one reviewer has been specified.
        # Do this as a custom validation step (rather than passing min_num=1 /
        # validate_min=True to inlineformset_factory) so that we can have a
        # custom error message.
        if (self.total_form_count() - len(self.deleted_forms) < 1):
            raise ValidationError(
                ugettext("Please select one or more reviewers."),
                code='too_few_forms'
            )


ReviewerFormSet = forms.inlineformset_factory(
    Review, Reviewer,
    fields=['user', 'email'],
    formset=BaseReviewerFormSet,
    extra=0,
    widgets={
        'user': forms.HiddenInput,
        'email': forms.HiddenInput,
    }
)


class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['result', 'comment']
        widgets = {
            'result': forms.RadioSelect,
            'comment': forms.Textarea(attrs={
                'placeholder': 'Enter your comments',
            }),
        }
