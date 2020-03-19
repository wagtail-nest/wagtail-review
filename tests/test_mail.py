from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase, override_settings

from wagtail.core.models import Page, Workflow, WorkflowState, WorkflowTask

from wagtail_review.signal_handlers import review_task_submission_email_notifier
from wagtail_review.models import GroupReviewTask, ReviewTask, ReviewTaskState

from .factories import ReviewerFactory, UserFactory


class TestReviewTaskMail(TestCase):
    fixtures = ['test.json']

    def setUp(self):

        page = Page.objects.get(id=2)
        self.page_revision = page.save_revision()

        self.internal_reviewer = ReviewerFactory.create_internal()
        self.external_reviewer = ReviewerFactory.create_external()
        self.superuser = UserFactory.create(is_superuser=True)

        # Set up a workflow
        self.workflow = Workflow.objects.create()
        self.workflow_task = ReviewTask.objects.create()
        self.workflow_task.reviewers.add(self.internal_reviewer)
        self.workflow_task.reviewers.add(self.external_reviewer)
        WorkflowTask.objects.create(workflow=self.workflow, task=self.workflow_task)

        workflow_state = WorkflowState.objects.create(
            workflow=self.workflow,
            page=page,
        )

        self.task_state = ReviewTaskState.objects.create(
            workflow_state=workflow_state,
            task=self.workflow_task,
            page_revision=self.page_revision,
        )

    @override_settings(WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=False)
    def test_send_submission_emails(self):
        review_task_submission_email_notifier(instance=self.task_state)
        recipient_addresses = [address for email in mail.outbox for address in email.to]
        self.assertEqual(len(recipient_addresses), 2)
        self.assertIn(self.internal_reviewer.get_email(), recipient_addresses)
        self.assertIn(self.external_reviewer.get_email(), recipient_addresses)

    @override_settings(WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=True)
    def test_send_submission_emails_include_admins(self):
        review_task_submission_email_notifier(instance=self.task_state)
        recipient_addresses = [address for email in mail.outbox for address in email.to]
        self.assertEqual(len(recipient_addresses), 3)
        self.assertIn(self.superuser.email, recipient_addresses)


class TestGroupReviewTaskMail(TestCase):
    fixtures = ['test.json']

    def setUp(self):

        page = Page.objects.get(id=2)
        self.page_revision = page.save_revision()

        self.internal_reviewer = ReviewerFactory.create_internal()
        self.superuser = UserFactory.create(is_superuser=True)

        self.group = Group.objects.create(name="test_group")
        self.group.user_set.add(self.internal_reviewer.internal)

        # Set up a workflow
        self.workflow = Workflow.objects.create()
        self.workflow_task = GroupReviewTask.objects.create()
        self.workflow_task.groups.add(self.group)
        WorkflowTask.objects.create(workflow=self.workflow, task=self.workflow_task)

        workflow_state = WorkflowState.objects.create(
            workflow=self.workflow,
            page=page,
        )

        self.task_state = ReviewTaskState.objects.create(
            workflow_state=workflow_state,
            task=self.workflow_task,
            page_revision=self.page_revision,
        )

    @override_settings(WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=False)
    def test_send_submission_emails(self):
        review_task_submission_email_notifier(instance=self.task_state)
        recipient_addresses = [address for email in mail.outbox for address in email.to]
        self.assertEqual(len(recipient_addresses), 1)
        self.assertIn(self.internal_reviewer.get_email(), recipient_addresses)

    @override_settings(WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=True)
    def test_send_submission_emails_include_admins(self):
        review_task_submission_email_notifier(instance=self.task_state)
        recipient_addresses = [address for email in mail.outbox for address in email.to]
        self.assertEqual(len(recipient_addresses), 2)
        self.assertIn(self.superuser.email, recipient_addresses)