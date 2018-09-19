from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _


REVIEW_STATUS_CHOICES = [
    ('open', _("Open")),
    ('closed', _("Closed")),
]


class BaseReview(models.Model):
    """
    Abstract base class for Review models. Can be subclassed to specify application-specific fields, e.g. review type
    """
    page_revision = models.ForeignKey('wagtailcore.PageRevision', related_name='reviews', on_delete=models.CASCADE, editable=False)
    status = models.CharField(max_length=30, default='open', choices=REVIEW_STATUS_CHOICES, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Review(BaseReview):
    pass


def get_review_model_string():
    """
    Get the dotted ``app.Model`` name for the review model as a string.
    """
    return getattr(settings, 'WAGTAILREVIEW_REVIEW_MODEL', 'wagtail_review.Review')


def get_review_model():
    """
    Get the review model from the ``WAGTAILREVIEW_REVIEW_MODEL`` setting.
    """
    from django.apps import apps
    model_string = get_review_model_string()
    try:
        return apps.get_model(model_string)
    except ValueError:
        raise ImproperlyConfigured("WAGTAILREVIEW_REVIEW_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "WAGTAILREVIEW_REVIEW_MODEL refers to model '%s' that has not been installed" % model_string
        )
