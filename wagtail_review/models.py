import random
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, Value, When, Q
from django.db.models.constraints import CheckConstraint, UniqueConstraint
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

import swapper
import jwt

from wagtail.admin.utils import send_mail
from wagtail.core.models import UserPagePermissionsProxy


class ExternalUser(models.Model):
    """
    Represents an external user who doesn't have an account but may need to view
    draft revisions of pages and comment on them.
    """
    email = models.EmailField()


class Share(models.Model):
    """
    Grants access to draft revisions of a page to an external user.
    """
    external_user = models.ForeignKey(ExternalUser, on_delete=models.CASCADE, related_name='shares')
    page = models.ForeignKey('wagtailcore.Page', on_delete=models.CASCADE, related_name='wagtailreview_shares')
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    shared_at = models.DateTimeField(auto_now_add=True)
    can_comment = models.BooleanField(default=False)
    first_accessed_at = models.DateTimeField(null=True)
    last_accessed_at = models.DateTimeField(null=True)
    expires_at = models.DateTimeField(null=True)

    def log_access(self):
        """
        Updates the *_accessed_at fields
        """
        self.last_accessed_at = timezone.now()

        if self.first_accessed_at is None:
            self.first_accessed_at = self.last_accessed_at

        self.save(update_fields=['first_accessed_at', 'last_accessed_at'])

    class Meta:
        unique_together = [
            ('external_user', 'page'),
        ]


class User(models.Model):
    """
    This model represents a union of the AUTH_USER_MODEL and ExternalUser models.

    It's intended as a place to reference in ForeignKeys in places where either an internal or external
    user could be specified.
    """
    internal = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE, related_name='+')
    external = models.ForeignKey(ExternalUser, null=True, on_delete=models.CASCADE, related_name='+')

    def get_name(self):
        if self.internal:
            return self.internal.get_full_name() or self.internal.email
        else:
            return self.external.email

    def page_perms(self, page_id):
        return UserPagePermissions(self, page_id)

    def get_review_token(self, page_revision_id):
        payload = {
            'usid': self.id,  # User ID
            'prid': page_revision_id,  # Page revision ID
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256').decode('utf-8')

    class Meta:
        constraints = [
            # Either internal or external must be set and not both
            CheckConstraint(
                check=Q(internal__isnull=False, external__isnull=True) |
                      Q(internal__isnull=True, external__isnull=False),
                name='either_internal_or_external'
            ),

            # Internal must be unique if it is not null
            UniqueConstraint(fields=['internal'], condition=Q(internal__isnull=False), name='unique_internal'),

            # External must be unique if it is not null
            UniqueConstraint(fields=['external'], condition=Q(external__isnull=False), name='unique_external'),
        ]


class UserPagePermissions:
    def __init__(self, user, page_id):
        self.user = user
        self.page_id = page_id

    @cached_property
    def share(self):
        if self.user.external_id:
            return Share.objects.filter(external_user_id=self.user.external_id, page_id=self.page_id).first()

    def can_view(self):
        """
        Returns True if the user can view the page
        """
        if self.user.external_id:
            if self.share is None:
                # Not shared with this user before
                return False

            if self.share.expires_at < timezone.now():
                # Share has expired
                return False

        return True

    def can_comment(self):
        """
        Returns True if the user can comment on the page
        """
        if not self.can_view():
            return False

        if self.user.external_id and not self.share.can_comment:
            # User can view but not comment
            return False

        return True


class Comment(models.Model):
    page_revision = models.ForeignKey('wagtailcore.PageRevision', on_delete=models.CASCADE, related_name='wagtailreview_comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    quote = models.TextField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True)

    content_path = models.TextField()
    start_xpath = models.TextField()
    start_offset = models.IntegerField()
    end_xpath = models.TextField()
    end_offset = models.IntegerField()


class CommentReply(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# OLD MODELS BELOW


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

    def send_request_emails(self):
        # send request emails to all reviewers except the reviewer record for the user submitting the request
        for reviewer in self.reviewers.exclude(user=self.submitter):
            reviewer.send_request_email()

    @cached_property
    def revision_as_page(self):
        return self.page_revision.as_page_object()

    def get_annotations(self):
        return Annotation.objects.filter(reviewer__review=self).prefetch_related('ranges')

    def get_responses(self):
        return Response.objects.filter(reviewer__review=self).order_by('created_at').select_related('reviewer')

    def get_non_responding_reviewers(self):
        return self.reviewers.filter(responses__isnull=True).exclude(user=self.submitter)

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


def generate_token():
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(16))


class Reviewer(models.Model):
    review = models.ForeignKey(swapper.get_model_name('wagtail_review', 'Review'), related_name='reviewers', on_delete=models.CASCADE)
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

    # TEMPORARY
    def into_user(self):
        if self.user:
            user, created = User.objects.get_or_create(
                internal=self.user,
            )
            return user
        else:
            external_user, created = ExternalUser.objects.get_or_create(
                email=self.email,
            )
            user, created = User.objects.get_or_create(
                external=external_user,
            )
            return user

    def clean(self):
        if self.user is None and not self.email:
            raise ValidationError("A reviewer must have either an email address or a user account")

    def get_email_address(self):
        return self.email or self.user.email

    def get_name(self):
        return self.user.get_full_name() if self.user else self.email

    def save(self, **kwargs):
        if not self.response_token:
            self.response_token = generate_token()
        if not self.view_token:
            self.view_token = generate_token()

        super().save(**kwargs)

    def get_respond_url(self, absolute=False):
        url = reverse('wagtail_review:respond', args=[self.id, self.response_token])
        if absolute:
            url = settings.BASE_URL + url
        return url

    def get_view_url(self, absolute=False):
        url = reverse('wagtail_review:view', args=[self.id, self.view_token])
        if absolute:
            url = settings.BASE_URL + url
        return url

    def send_request_email(self):
        email_address = self.get_email_address()

        context = {
            'email': email_address,
            'user': self.user,
            'review': self.review,
            'page': self.review.revision_as_page,
            'submitter': self.review.submitter,
            'respond_url': self.get_respond_url(absolute=True),
            'view_url': self.get_view_url(absolute=True),
        }

        email_subject = render_to_string('wagtail_review/email/request_review_subject.txt', context).strip()
        email_content = render_to_string('wagtail_review/email/request_review.txt', context).strip()

        send_mail(email_subject, email_content, [email_address])


class Annotation(models.Model):
    reviewer = models.ForeignKey(Reviewer, related_name='annotations', on_delete=models.CASCADE)
    quote = models.TextField(blank=True)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AnnotationRange(models.Model):
    annotation = models.ForeignKey(Annotation, related_name='ranges', on_delete=models.CASCADE)
    start = models.TextField()
    start_offset = models.IntegerField()
    end = models.TextField()
    end_offset = models.IntegerField()


RESULT_CHOICES = (
    ('approve', 'Approved'),
    ('comment', 'Comment'),
)


class Response(models.Model):
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
