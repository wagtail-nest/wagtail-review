import random
import string

import jwt
from jwt.exceptions import InvalidTokenError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, Value, When
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

import swapper

from wagtail.admin.utils import send_mail
from wagtail.core.models import UserPagePermissionsProxy


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
    assignees = models.ManyToManyField('Reviewer', related_name='+')

    def send_request_emails(self):
        # send request emails to all reviewers except the reviewer record for the user submitting the request
        for reviewer in self.assignees.exclude(user=self.submitter):
            email_address = reviewer.get_email_address()

            context = {
                'email': email_address,
                'user': reviewer.user,
                'review': self,
                'page': self.revision_as_page,
                'submitter': self.submitter,
                'respond_url': reviewer.get_respond_url(self.page_revision_id, absolute=True),
                'view_url': reviewer.get_view_url(self.page_revision_id, absolute=True),
            }

            email_subject = render_to_string('wagtail_review/email/request_review_subject.txt', context).strip()
            email_content = render_to_string('wagtail_review/email/request_review.txt', context).strip()

            send_mail(email_subject, email_content, [email_address])

    @cached_property
    def revision_as_page(self):
        return self.page_revision.as_page_object()

    def get_comments(self):
        return Comment.objects.filter(reviewer__review=self).prefetch_related('page_locations')

    def get_responses(self):
        return Response.objects.filter(reviewer__review=self).order_by('created_at').select_related('reviewer')

    def get_non_responding_reviewers(self):
        return self.assignees.filter(responses__isnull=True).exclude(user=self.submitter)

    @classmethod
    def get_pages_with_reviews_for_user(cls, user):
        """
        Return a queryset of pages which have reviews, for which the user has edit permission
        """
        user_perms = UserPagePermissionsProxy(user)
        reviewed_pages = (
            cls.objects
            .order_by('-created_at')
            .values_list('page_revision__page_id', 'created_at')
        )
        # Annotate datetime when a review was last created for this page
        last_review_requested_at = Case(
            *[
                When(pk=pk, then=Value(created_at))
                for pk, created_at in reviewed_pages
            ],
            output_field=models.DateTimeField(),
        )
        return (
            user_perms.editable_pages()
            .filter(pk__in=(page[0] for page in reviewed_pages))
            .annotate(last_review_requested_at=last_review_requested_at)
            .order_by('-last_review_requested_at')
        )

    class Meta:
        abstract = True


class Review(BaseReview):
    class Meta:
        swappable = swapper.swappable_setting('wagtail_review', 'Review')


class Share(models.Model):
    """
    Grants permission for an external user to access draft revisions of a page
    """
    email = models.EmailField()
    page = models.ForeignKey('wagtailcore.Page', on_delete=models.CASCADE, related_name='wagtailreview_shares')


class Reviewer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name='+')
    email = models.EmailField(blank=True)

    def clean(self):
        if self.user is None and not self.email:
            raise ValidationError("A reviewer must have either an email address or a user account")

    def get_email_address(self):
        return self.user.email if self.user else self.email

    def get_name(self):
        return self.user.get_full_name() if self.user else self.email

    def get_token(self, page_revision_id, enable_comments=False):
        # Use a code to make tokens shorter.
        # Prefixes:
        #  rv - Reviewer
        #  cm - Commenting
        #  pr - Page Revision
        #
        # Suffixes:
        #  id - Identifier
        #  nm - Name (for display purposes)
        #  en - Enabled
        payload = {
            'rvid': self.id,
            'rvnm': self.get_name(),
            'prid': page_revision_id,
            'cmen': enable_comments,
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256').decode('utf-8')

    def verify_token(self, token, page_revision_id, require_comments=False):
        try:
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithm='HS256')
        except InvalidTokenError:
            return False

        if decoded['rvid'] != self.id:
            return False

        if decoded['prid'] !=page_revision_id:
            return False

        if require_comments and not decoded['cmen']:
            return False

        return True

    def get_respond_url(self, page_revision_id, absolute=False):
        url = reverse('wagtail_review:respond', args=[self.id, self.get_token(page_revision_id, enable_comments=True)])
        if absolute:
            url = settings.BASE_URL + url
        return url

    def get_view_url(self, page_revision_id, absolute=False):
        url = reverse('wagtail_review:view', args=[self.id, self.get_token(page_revision_id)])
        if absolute:
            url = settings.BASE_URL + url
        return url


class Comment(models.Model):
    page_revision = models.ForeignKey('wagtailcore.PageRevision', related_name='wagtailreview_comments', on_delete=models.CASCADE)
    reviewer = models.ForeignKey(Reviewer, related_name='comments', on_delete=models.CASCADE)
    review = models.ForeignKey(swapper.get_model_name('wagtail_review', 'Review'), null=True, related_name='comments', on_delete=models.SET_NULL)
    quote = models.TextField(blank=True)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def as_json_data(self):
        return {
            'id': self.id,
            'annotator_schema_version': 'v1.0',
            'created': self.created_at.isoformat(),
            'updated': self.updated_at.isoformat(),
            'text': self.text,
            'quote': self.quote,
            'user': {
                'id': self.reviewer.id,
                'name': self.reviewer.get_name(),
            },
            'ranges': [r.as_json_data() for r in self.page_locations.all()],
        }


class CommentPageLocation(models.Model):
    comment = models.ForeignKey(Comment, related_name='page_locations', on_delete=models.CASCADE)
    content_path = models.TextField(blank=True)
    start = models.TextField()
    start_offset = models.IntegerField()
    end = models.TextField()
    end_offset = models.IntegerField()

    def as_json_data(self):
        return {
            'start': self.start,
            'startOffset': self.start_offset,
            'end': self.end,
            'endOffset': self.end_offset,
        }


RESULT_CHOICES = (
    ('approve', 'Approved'),
    ('comment', 'Comment'),
)


class Response(models.Model):
    review = models.ForeignKey(swapper.get_model_name('wagtail_review', 'Review'), related_name='responses', on_delete=models.CASCADE)
    reviewer = models.ForeignKey(Reviewer, related_name='responses', on_delete=models.CASCADE)
    result = models.CharField(choices=RESULT_CHOICES, max_length=10, blank=False, default=None)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def send_notification_to_submitter(self):
        submitter = self.reviewer.review.submitter
        if submitter.email:

            context = {
                'submitter': submitter,
                'reviewer': self.reviewer,
                'review': self.reviewer.review,
                'page': self.reviewer.review.revision_as_page,
                'response': self,
            }

            email_subject = render_to_string('wagtail_review/email/response_received_subject.txt', context).strip()
            email_content = render_to_string('wagtail_review/email/response_received.txt', context).strip()

            send_mail(email_subject, email_content, [submitter.email])
