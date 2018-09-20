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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Review(BaseReview):
    class Meta:
        swappable = swapper.swappable_setting('wagtail_review', 'Review')
