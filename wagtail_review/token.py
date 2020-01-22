from django.conf import settings
from django.utils.functional import cached_property

import jwt
from wagtail.core.models import PageRevision, TaskState

REVIEWER_ID_KEY = 'rvid'
PAGE_REVISION_ID_KEY = 'prid'
TASK_STATE_ID_KEY = 'tsid'


class Token:
    def __init__(self, reviewer_id, page_revision_id, task_state_id=None):
        from .models import Reviewer
        from .models import ReviewRequest

        if isinstance(reviewer_id, Reviewer):
            self.__dict__['reviewer'] = reviewer_id
            self.reviewer_id = self.reviewer.id
        else:
            self.reviewer_id = reviewer_id

        if isinstance(page_revision_id, PageRevision):
            self.__dict__['page_revision'] = page_revision_id
            self.page_revision_id = self.page_revision.id
        else:
            self.page_revision_id = page_revision_id

        if isinstance(task_state_id, TaskState):
            self.__dict__['task_state'] = task_state_id
            self.task_state_id = self.task_state.id
        else:
            self.task_state_id = task_state_id

    def encode(self):
        payload = {
            REVIEWER_ID_KEY: self.reviewer_id,
            PAGE_REVISION_ID_KEY: self.page_revision_id,
        }

        if self.task_state_id is not None:
            payload[TASK_STATE_ID_KEY] = self.task_state_id

        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256').decode('utf-8')

    @classmethod
    def decode(cls, token):
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        reviewer_id = data.get(REVIEWER_ID_KEY)
        page_revision_id = data.get(PAGE_REVISION_ID_KEY)
        task_state_id = data.get(TASK_STATE_ID_KEY)
        return cls(reviewer_id, page_revision_id, task_state_id)

    @cached_property
    def reviewer(self):
        from .models import Reviewer
        return Reviewer.objects.get(id=self.reviewer_id)

    @cached_property
    def page_revision(self):
        return PageRevision.objects.get(id=self.page_revision_id)

    @cached_property
    def task_state(self):
        if self.task_state_id is not None:
            from .models import TaskState
            return TaskState.objects.get(id=self.task_state_id)
