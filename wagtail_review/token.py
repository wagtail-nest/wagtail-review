from django.conf import settings
from django.utils.functional import cached_property

import jwt
from wagtail.core.models import PageRevision

REVIEWER_ID_KEY = 'rvid'
PAGE_REVISION_ID_KEY = 'prid'
REVIEW_REQUEST_ID_KEY = 'rrid'


class Token:
    def __init__(self, reviewer_id, page_revision_id, review_request_id=None):
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

        if isinstance(review_request_id, ReviewRequest):
            self.__dict__['review_request'] = review_request_id
            self.review_request_id = self.review_request.id
        else:
            self.review_request_id = review_request_id

    def encode(self):
        payload = {
            REVIEWER_ID_KEY: self.reviewer_id,
            PAGE_REVISION_ID_KEY: self.page_revision_id,
        }

        if self.review_request_id is not None:
            payload[REVIEW_REQUEST_ID_KEY] = self.review_request_id

        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256').decode('utf-8')

    @classmethod
    def decode(cls, token):
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        reviewer_id = data.get(REVIEWER_ID_KEY)
        page_revision_id = data.get(PAGE_REVISION_ID_KEY)
        review_request_id = data.get(REVIEW_REQUEST_ID_KEY)
        return cls(reviewer_id, page_revision_id, review_request_id)

    @cached_property
    def reviewer(self):
        from .models import Reviewer
        return Reviewer.objects.get(id=self.reviewer_id)

    @cached_property
    def page_revision(self):
        return PageRevision.objects.get(id=self.page_revision_id)

    @cached_property
    def review_request(self):
        if self.review_request_id is not None:
            from .models import ReviewRequest
            return ReviewRequest.objects.get(id=self.review_request_id)
