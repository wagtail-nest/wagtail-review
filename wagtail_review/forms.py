from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.forms.formsets import DELETION_FIELD_NAME
from django.utils.module_loading import import_string
from django.utils.translation import ugettext

from wagtail_review.models import ReviewRequest, Reviewer, Response, User as WagtailReviewUser, Share, ExternalUser


User = get_user_model()


class CreateReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRequest
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


class BaseReviewAssigneeFormSet(forms.BaseFormSet):
    def clean(self):
        # Confirm that at least one assignee has been specified.
        # Do this as a custom validation step (rather than passing min_num=1 /
        # validate_min=True to inlineformset_factory) so that we can have a
        # custom error message.
        if (self.total_form_count() - len(self.deleted_forms) < 1):
            raise ValidationError(
                ugettext("Please select one or more assignees."),
                code='too_few_forms'
            )


class ReviewAssigneeForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False, widget=forms.HiddenInput)
    email = forms.EmailField(required=False, widget=forms.HiddenInput)

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data['user'] and not cleaned_data['email']:
            raise ValidationError(
                ugettext("Please specify either a user or an email address."),
                code='user_or_email_unspecified'
            )

        if cleaned_data['user'] and cleaned_data['email']:
            raise ValidationError(
                ugettext("Please specify either a user or an email address. Not both"),
                code='both_user_and_email_specified'
            )

        return cleaned_data

    def get_user(self, review_request):
        if self.cleaned_data['user']:
            user, created = WagtailReviewUser.objects.get_or_create(
                internal=self.cleaned_data['user'],
            )
            return user
        else:
            external_user, created = ExternalUser.objects.get_or_create(
                email=self.cleaned_data['email'],
            )
            share, created = Share.objects.get_or_create(
                external_user=external_user,
                page_id=review_request.page_revision.page_id,
                defaults={
                    'shared_by_id': review_request.submitted_by_id,
                    'shared_at': review_request.submitted_at,
                    'can_comment': True,
                }
            )
            user, created = WagtailReviewUser.objects.get_or_create(
                external=external_user,
            )
            return user

    class Meta:
        fields = ['user', 'email']


ReviewAssigneeFormSet = forms.formset_factory(
    ReviewAssigneeForm,
    formset=BaseReviewAssigneeFormSet,
    extra=0,
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
