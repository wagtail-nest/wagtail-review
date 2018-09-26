import random
import string

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

import swapper

# make the setting name WAGTAILREVIEW_REVIEW_MODEL rather than WAGTAIL_REVIEW_REVIEW_MODEL
swapper.set_app_prefix('wagtail_review', 'wagtailreview')


REVIEW_STATUS_CHOICES = [
    ('open', _("Open")),
    ('closed', _("Closed")),
]


class BaseReview(models.Model):
    """
    Abstract base class for Review models. Can be subclassed to specify application-specific fields, e.g. review type
    """
    page_revision = models.ForeignKey('wagtailcore.PageRevision', related_name='+', on_delete=models.CASCADE, editable=False)
    status = models.CharField(max_length=30, default='open', choices=REVIEW_STATUS_CHOICES, editable=False)
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+', editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Review(BaseReview):
    class Meta:
        swappable = swapper.swappable_setting('wagtail_review', 'Review')


def generate_token():
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(16))


class Reviewer(models.Model):
    review = models.ForeignKey(swapper.get_model_name('wagtail_review', 'Review'), related_name='reviewers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name='+')
    email = models.EmailField(blank=True)
    response_token = models.CharField(
        max_length=32, editable=False,
        help_text="Secret token this user must supply to be allowed to respond to the review"
    )
    view_token = models.CharField(
        max_length=32, editable=False,
        help_text="Secret token this user must supply to be allowed to view the page revision being reviewed"
    )

    def save(self, **kwargs):
        if not self.response_token:
            self.response_token = generate_token()
        if not self.view_token:
            self.view_token = generate_token()

        super().save(**kwargs)
