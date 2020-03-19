from wagtail.core.models import TaskState, WorkflowState
from wagtail.core.signals import (
    task_submitted, workflow_approved, workflow_rejected, workflow_submitted)

from .mail import ReviewTaskStateSubmissionEmailNotifier

review_task_submission_email_notifier = ReviewTaskStateSubmissionEmailNotifier()

def register_signal_handlers():
    task_submitted.connect(review_task_submission_email_notifier, dispatch_uid='review_task_submitted_email_notification')
