from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import get_connection
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import override

from wagtail.admin.mail import EmailNotifier, OpenedConnection, logger, send_mail
from wagtail.core.models import TaskState
from wagtail.users.models import UserProfile

from .models import GroupReviewTask, Reviewer, ReviewTask, ReviewTaskState, get_review_url
from .token import Token


class ReviewTaskStateSubmissionEmailNotifier(EmailNotifier):
    """A EmailNotifier to send updates for ReviewTask/GroupReviewTask submissions"""

    notification = 'submitted'
    template_directory = 'wagtail_review/notifications/'

    def __init__(self):
        super().__init__((TaskState, ReviewTaskState))

    def can_handle(self, instance, **kwargs):
        if super().can_handle(instance, **kwargs) and isinstance(instance.task.specific, (ReviewTask, GroupReviewTask)):
            # Don't send notifications if a Task has been cancelled and then resumed - ie page was updated to a new revision
            return not TaskState.objects.filter(workflow_state=instance.workflow_state, task=instance.task, status=TaskState.STATUS_CANCELLED).exists()
        return False

    def get_context(self, task_state, **kwargs):
        context = super().get_context(task_state, **kwargs)
        context['page'] = task_state.workflow_state.page
        context['task'] = task_state.task.specific
        context['revision'] = task_state.page_revision
        return context

    def get_template_base_prefix(self, instance, **kwargs):
        return super().get_template_base_prefix(instance.specific, **kwargs)

    def get_valid_recipients(self, instance, **kwargs):
        recipients = self.get_recipient_users(instance, **kwargs)

        valid_internal_recipients = {recipient for recipient in recipients if recipient.internal and recipient.get_email() and getattr(
            UserProfile.get_for_user(recipient.internal),
            self.notification + '_notifications'
        )}

        valid_external_recipients = {recipient for recipient in recipients if recipient.external and recipient.get_email()}

        return valid_external_recipients|valid_internal_recipients

    def get_recipient_users(self, task_state, **kwargs):
        triggering_user = kwargs.get('user', None)

        try:
            recipients = task_state.task.specific.reviewers.all()
        except AttributeError:
            recipients = Reviewer.objects.filter(internal__groups__in=task_state.task.specific.groups.all())

            # If any users without a Reviewer instance exist, create those instances
            group_members_without_reviewers = get_user_model().objects.filter(groups__in=task_state.task.specific.groups.all()).exclude(pk__in=recipients.values_list('internal__pk', flat=True))
            if group_members_without_reviewers.exists():
                Reviewer.objects.bulk_create([Reviewer(internal=user) for user in group_members_without_reviewers])
                recipients = Reviewer.objects.filter(internal__groups__in=task_state.task.specific.groups.all())

        include_superusers = getattr(settings, 'WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS', True)
        if include_superusers:
            superusers = get_user_model().objects.filter(is_superuser=True)
            superuser_reviewers = Reviewer.objects.filter(internal__pk__in=superusers.values_list('pk', flat=True))

            # check that all superusers have a Reviewer instance attached, and create one if not
            if superusers.count() != superuser_reviewers.count():
                superusers_without_reviewers = superusers.exclude(id__in=Reviewer.objects.all().values_list('internal__pk', flat=True))
                Reviewer.objects.bulk_create(Reviewer(internal=user) for user in superusers_without_reviewers)
                superuser_reviewers = Reviewer.objects.filter(internal__pk__in=superusers.values_list('pk', flat=True))
            recipients = recipients | superuser_reviewers

        if triggering_user:
            recipients = recipients.exclude(internal__pk=triggering_user.pk)

        recipients.select_related('external')

        return recipients

    def send_emails(self, template_set, context, recipients, **kwargs):

        connection = get_connection()

        with OpenedConnection(connection) as open_connection:

            # Send emails
            sent_count = 0
            for recipient in recipients:
                try:

                    # update context with this recipient
                    context["user"] = recipient.internal
                    context["reviewer"] = recipient
                    context["review_url"] = get_review_url(Token(recipient, context["revision"]))

                    # Translate text to the recipient language settings
                    if recipient.internal:
                        with override(recipient.internal.wagtail_userprofile.get_preferred_language()):
                            # Get email subject and content
                            email_subject = render_to_string(template_set['subject'], context).strip()
                            email_content = render_to_string(template_set['text'], context).strip()
                    else:
                        email_subject = render_to_string(template_set['subject'], context).strip()
                        email_content = render_to_string(template_set['text'], context).strip()

                    kwargs = {}
                    if getattr(settings, 'WAGTAILADMIN_NOTIFICATION_USE_HTML', False):
                        kwargs['html_message'] = render_to_string(template_set['html'], context)

                    # Send email
                    send_mail(email_subject, email_content, [recipient.get_email()], connection=open_connection, **kwargs)
                    sent_count += 1
                except Exception:
                    logger.exception(
                        "Failed to send notification email '%s' to %s",
                        email_subject, recipient.email
                    )

        return sent_count == len(recipients)
