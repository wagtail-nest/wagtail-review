from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import models, transaction
from django.db.models import Case, Q, Value, When
from django.db.models.constraints import CheckConstraint, UniqueConstraint
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.mail import send_mail
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page, UserPagePermissionsProxy, Task, TaskState
from django.shortcuts import redirect

from .edit_handlers import ReviewerChooserPanel
from .token import Token
from .utils import normalize_email

from modelcluster.fields import ParentalManyToManyField


def get_review_url_impl(token):
    return settings.BASE_URL + reverse('wagtail_review:review', args=[token.encode()])


def get_review_url(token):
    REVIEW_URL_BUILDER = getattr(settings, 'WAGTAILREVIEW_REVIEW_URL_BUILDER', None)

    if REVIEW_URL_BUILDER is not None:
        review_url_builder = import_string(REVIEW_URL_BUILDER)
    else:
        review_url_builder = get_review_url_impl

    return review_url_builder(token)


class ExternalReviewer(models.Model):
    """
    Represents an external user who doesn't have an account but may need to view
    draft revisions of pages and comment on them.
    """
    email = models.EmailField(unique=True)

    def save(self, **kwargs):
        # Normalize email addresses before saving or the unique constraint won't work
        self.email = normalize_email(self.email)

        super().save()

    def get_reviewer(self):
        user, created = Reviewer.objects.get_or_create(external=self)
        return user


class Share(models.Model):
    """
    Grants access to draft revisions of a page to an external user.
    """
    external_user = models.ForeignKey(ExternalReviewer, on_delete=models.CASCADE, related_name='shares')
    page = models.ForeignKey('wagtailcore.Page', on_delete=models.CASCADE, related_name='wagtailreview_shares')
    shared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    shared_at = models.DateTimeField(auto_now_add=True)
    can_comment = models.BooleanField(default=False)
    first_accessed_at = models.DateTimeField(null=True)
    last_accessed_at = models.DateTimeField(null=True)
    expires_at = models.DateTimeField(null=True)

    def send_share_email(self):
        """
        Emails the user with the review link
        """
        email_address = self.external_user.email
        review_token = Token(self.external_user.get_reviewer(), self.page.get_latest_revision())

        email_body = render_to_string('wagtail_review/email/share.txt', {
            'page': self.page,
            'review_url': get_review_url(review_token),
        })

        send_mail("A page has been shared with you", email_body, [email_address])

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


class Reviewer(models.Model):
    """
    This model represents a union of the AUTH_USER_MODEL and ExternalReviewer models.

    It's intended as a place to reference in ForeignKeys in places where either an internal or external
    user could be specified.
    """
    internal = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE, related_name='+')
    external = models.ForeignKey(ExternalReviewer, null=True, on_delete=models.CASCADE, related_name='+')

    def get_name(self):
        if self.internal:
            return self.internal.get_full_name() or self.internal.email
        else:
            return self.external.email

    def get_email(self):
        if self.internal:
            return self.internal.email
        else:
            return self.external.email

    def page_perms(self, page):
        return ReviewerPagePermissions(self, page)

    class Meta:
        constraints = [
            # Either internal or external must be set and not both
            CheckConstraint(
                check=Q(internal__isnull=False, external__isnull=True) | Q(internal__isnull=True, external__isnull=False),
                name='either_internal_or_external'
            ),

            # Internal must be unique if it is not null
            UniqueConstraint(fields=['internal'], condition=Q(internal__isnull=False), name='unique_internal'),

            # External must be unique if it is not null
            UniqueConstraint(fields=['external'], condition=Q(external__isnull=False), name='unique_external'),
        ]


class ReviewerPagePermissions:
    def __init__(self, reviewer, page):
        self.reviewer = reviewer
        self.page = page

    @cached_property
    def share(self):
        if self.reviewer.external_id:
            return Share.objects.filter(external_user_id=self.reviewer.external_id, page=self.page).first()

    def can_review(self):
        """
        Returns True if the workflow is in a ReviewTask or GroupReviewTask and the reviewer is one of the reviewers.
        """
        try:
            actions = {action[0] for action in self.page.current_workflow_task.get_actions(self.page, user=None, reviewer=self.reviewer)}
            if 'review' in actions:
                return True
        except AttributeError:
            pass

        return False

    def can_view(self):
        """
        Returns True if the reviewer can view the page
        """
        # If the page is in a workflow and this user is a reviewer then they can view
        if self.can_review():
            return True

        # Otherwise, check if this page is shared with the user
        if self.reviewer.external_id:
            if self.share is None:
                # Not shared with this reviewer before
                return False

            if self.share.expires_at is not None and self.share.expires_at < timezone.now():
                # Share has expired
                return False

        return True

    def can_comment(self):
        """
        Returns True if the reviewer can comment on the page
        """
        if not self.can_view():
            return False

        if self.reviewer.external_id and not self.share.can_comment:
            # External users can leave comments without a share if they are a reviewer
            if self.can_review():
                return True

            # Reviewer can view but not comment
            return False

        return True

    def can_respond(self):
        """
        Returns True if the reviewer can approve or reject the stage
        """
        if not self.can_review():
            return False

        actions = {action[0] for action in self.page.current_workflow_task.get_actions(self.page, user=None, reviewer=self.reviewer)}
        if 'approve' in actions or 'reject' in actions:
            return True

        return False


class Comment(models.Model):
    page_revision = models.ForeignKey('wagtailcore.PageRevision', on_delete=models.CASCADE, related_name='wagtailreview_comments')
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE, related_name='comments')
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

    def get_frontend_url(self, reviewer):
        review_token = Token(reviewer, self.page_revision_id)
        return get_review_url(review_token) + "?comment=" + str(self.id)


class CommentReply(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='replies')
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE, related_name='comment_replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReviewRequestQuerySet(models.QuerySet):
    def has_approved_response(self):
        return self.filter(responses__in=ReviewResponse.objects.approved())

    def has_no_approved_response(self):
        return self.exclude(responses__in=ReviewResponse.objects.approved())

    def open(self):
        return self.filter(is_closed=False)

    def closed(self):
        return self.filter(is_closed=True)


class ReviewRequest(models.Model):
    page_revision = models.ForeignKey('wagtailcore.PageRevision', on_delete=models.CASCADE, related_name='wagtailreview_reviewrequests')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    submitted_at = models.DateTimeField(auto_now_add=True)
    assignees = models.ManyToManyField(Reviewer)
    is_closed = models.BooleanField(default=False)

    objects = ReviewRequestQuerySet.as_manager()

    def get_review_url(self, reviewer):
        review_token = Token(reviewer, self.page_revision_id)
        return get_review_url(review_token)

    def send_request_emails(self):
        # send request emails to all reviewers except the reviewer record for the user submitting the request
        for reviewer in self.assignees.all():
            email = reviewer.get_email()

            context = {
                'email': email,
                'user': reviewer.internal,
                'reviewer': reviewer,
                'review_request': self,
                'page': self.page_revision.as_page_object(),
                'submitter': self.submitted_by,
                'review_url': self.get_review_url(reviewer),
            }

            email_subject = render_to_string('wagtail_review/email/request_review_subject.txt', context).strip()
            email_content = render_to_string('wagtail_review/email/request_review.txt', context).strip()

            send_mail(email_subject, email_content, [email])

    @classmethod
    def get_pages_with_reviews_for_user(cls, user):
        """
        Return a queryset of pages which have reviews, for which the user has edit permission
        """
        user_perms = UserPagePermissionsProxy(user)
        reviewed_pages = (
            cls.objects
            .order_by('-submitted_at')
            .values_list('page_revision__page_id', 'submitted_at')
        )
        # Annotate datetime when a review was last created for this page
        last_review_requested_at = Case(
            *[
                When(pk=pk, then=Value(submitted_at))
                for pk, submitted_at in reviewed_pages
            ],
            output_field=models.DateTimeField(),
        )
        return (
            user_perms.editable_pages()
            .filter(pk__in=(page[0] for page in reviewed_pages))
            .annotate(last_review_requested_at=last_review_requested_at)
            .order_by('-last_review_requested_at')
        )

    def get_assignees_without_response(self):
        return self.assignees.exclude(
            id__in=ReviewResponse.objects.filter(request=self).values_list('submitted_by_id', flat=True)
        )


class ReviewResponseQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(status=ReviewResponse.STATUS_APPROVED)

    def needs_changes(self):
        return self.filter(status=ReviewResponse.STATUS_NEEDS_CHANGES)


class ReviewResponse(models.Model):
    STATUS_APPROVED = 'approved'
    STATUS_NEEDS_CHANGES = 'needs-changes'
    STATUS_CHOICES = [
        (STATUS_APPROVED, _("approved")),
        (STATUS_NEEDS_CHANGES, _("needs changes")),
    ]

    request = models.ForeignKey(ReviewRequest, on_delete=models.CASCADE, related_name='responses')
    submitted_by = models.ForeignKey(Reviewer, on_delete=models.CASCADE, related_name='+')
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES)
    comment = models.TextField(blank=True)

    objects = ReviewResponseQuerySet.as_manager()


class ReviewTaskState(TaskState):
    comment = models.TextField(blank=True)
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE, related_name='+', null=True)

    def _finalise(self, user=None, reviewer=None, comment=''):
        self.comment = comment
        self.reviewer = reviewer
        if reviewer and reviewer.internal_id:
            self.finished_by_id = reviewer.internal_id
        elif user and user.is_authenticated:
            self.finished_by = user
        self.finished_at = timezone.now()

    @transaction.atomic
    def approve(self, user=None, reviewer=None, comment='', **kwargs):
        self._finalise(
            user=user,
            reviewer=reviewer,
            comment=comment,
        )
        super().approve(**kwargs)

    @transaction.atomic
    def reject(self, user=None, reviewer=None, comment='', **kwargs):
        self._finalise(
            user=user,
            reviewer=reviewer,
            comment=comment,
        )
        super().reject(**kwargs)

    def get_comment(self):
        if self.status in [self.STATUS_APPROVED, self.STATUS_REJECTED]:
            external_user = self.reviewer and self.reviewer.external

            if external_user:
                return format_html(
                    """
                    Reviewed by external user: <b>{}</b><br/>
                    <blockquote>{}</blockquote>
                    """,
                    external_user.email,
                    self.comment
                )
            else:
                return format_html("<blockquote>{}</blockquote>", self.comment)

        return ""


class ReviewTask(Task):
    reviewers = models.ManyToManyField(Reviewer)

    panels = Task.panels + [ReviewerChooserPanel('reviewers')]

    task_state_class = ReviewTaskState

    def start(self, workflow_state, user=None):
        if workflow_state.page.locked_by:
            # If the person who locked the page isn't a reviewer, unlock the page
            if not self.reviewers.filter(internal__pk=workflow_state.page.locked_by.pk).exists():
                workflow_state.page.locked = False
                workflow_state.page.locked_by = None
                workflow_state.page.locked_at = None
                workflow_state.page.save(update_fields=['locked', 'locked_by', 'locked_at'])

        return super().start(workflow_state, user=user)

    def user_can_access_editor(self, page, user):
        return self.reviewers.filter(internal__pk=user.pk).exists()

    def user_can_lock(self, page, user):
        return self.reviewers.filter(internal__pk=user.pk).exists()

    def user_can_unlock(self, page, user):
        return False

    def get_actions(self, page, user, reviewer=None, **kwargs):
        if not reviewer:
            reviewer = Reviewer.objects.get(internal__pk=user.pk)
        if self.reviewers.filter(pk=reviewer.pk).exists() or user.is_superuser:
            return [
                ('review', _("Review")),
                ('approve', _("Approve")),
                ('reject', _("Reject")),
            ]
        else:
            return []

    def on_action(self, task_state, user, action_name, reviewer=None, comment='', **kwargs):
        if action_name == 'approve':
            task_state.approve(user=user, reviewer=reviewer, comment=comment)
        elif action_name == 'reject':
            task_state.reject(user=user, reviewer=reviewer, comment=comment)
        elif action_name == 'review':
            review_token = Token(Reviewer.objects.get_or_create(internal=user)[0], task_state.page_revision, task_state)
            return redirect(get_review_url(review_token))

    def get_task_states_user_can_moderate(self, user, **kwargs):
        if self.reviewers.filter(internal__pk=user.pk).exists() or user.is_superuser:
            return TaskState.objects.filter(status=TaskState.STATUS_IN_PROGRESS, task=self.task_ptr)
        else:
            return TaskState.objects.none()

    class Meta:
        verbose_name = _('Review task')
        verbose_name_plural = _('Review tasks')


class GroupReviewTask(Task):
    groups = models.ManyToManyField(Group, verbose_name=_('groups'), help_text=_('Pages at this step in a workflow will be commented on or approved by these groups of users'))

    panels = Task.panels + [FieldPanel('groups', heading=_("Choose review groups"))]
    exclude_on_edit = {'groups'}

    task_state_class = ReviewTaskState

    def start(self, workflow_state, user=None):
        if workflow_state.page.locked_by:
            # If the person who locked the page isn't in one of the groups, unlock the page
            if not workflow_state.page.locked_by.groups.filter(id__in=self.groups.all()).exists():
                workflow_state.page.locked = False
                workflow_state.page.locked_by = None
                workflow_state.page.locked_at = None
                workflow_state.page.save(update_fields=['locked', 'locked_by', 'locked_at'])

        return super().start(workflow_state, user=user)

    def user_can_access_editor(self, page, user):
        return self.groups.filter(id__in=user.groups.all()).exists()

    def user_can_lock(self, page, user):
        return self.groups.filter(id__in=user.groups.all()).exists()

    def user_can_unlock(self, page, user):
        return False

    def get_actions(self, page, user, reviewer=None, **kwargs):
        if reviewer and (not user or not user.is_authenticated):
            user = get_user_model().objects.get(pk=reviewer.internal.pk)
        if self.groups.all().filter(id__in=user.groups.all()).exists() or user.is_superuser:
            return [
                ('review', _("Review")),
                ('approve', _("Approve")),
                ('reject', _("Reject")),
            ]
        else:
            return []

    def on_action(self, task_state, user, action_name, reviewer=None, comment='', **kwargs):
        if action_name == 'approve':
            task_state.approve(user=user, reviewer=reviewer, comment=comment)
        elif action_name == 'reject':
            task_state.reject(user=user, reviewer=reviewer, comment=comment)
        elif action_name == 'review':
            review_token = Token(Reviewer.objects.get_or_create(internal=user)[0], task_state.page_revision, task_state)
            return redirect(get_review_url(review_token))

    def get_task_states_user_can_moderate(self, user, **kwargs):
        if self.groups.filter(id__in=user.groups.all()).exists() or user.is_superuser:
            return TaskState.objects.filter(status=TaskState.STATUS_IN_PROGRESS, task=self.task_ptr)
        else:
            return TaskState.objects.none()

    class Meta:
        verbose_name = _('Group review task')
        verbose_name_plural = _('Group review tasks')
