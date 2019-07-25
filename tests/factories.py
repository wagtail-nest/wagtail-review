from django.contrib.auth.models import User

import factory

from wagtail_review import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('sentence', nb_words=2)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class ExternalReviewerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ExternalReviewer

    email = factory.Faker('email')


class ShareFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Share

    external_user = factory.SubFactory(ExternalReviewerFactory)
    page = None  # Set in test
    shared_by = factory.SubFactory(UserFactory)
    can_comment = True


class ReviewerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Reviewer

    internal = factory.SubFactory(UserFactory)
    external = factory.SubFactory(ExternalReviewerFactory)

    @classmethod
    def create_internal(cls, user=None):
        if user is None:
            user = UserFactory.create()

        return cls.create(internal=user, external=None)

    @classmethod
    def create_external(cls, external_reviewer=None):
        if external_reviewer is None:
            external_reviewer = ExternalReviewerFactory.create()

        return cls.create(internal=None, external=external_reviewer)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Comment

    page_revision = None  # Set in test
    reviewer = factory.LazyAttribute(lambda o: ReviewerFactory.create_internal())
    quote = "This is the quote"
    text = "This is some text"
    content_path = "title"
    start_xpath = "."
    start_offset = 0
    end_xpath = "."
    end_offset = 10


class CommentReplyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.CommentReply

    comment = None  # Set in test
    reviewer = factory.LazyAttribute(lambda o: ReviewerFactory.create_internal())
    text = "This is the reply text"


class ReviewRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ReviewRequest

    page_revision = None  # Set in test
    submitted_by = factory.SubFactory(UserFactory)
    is_closed = False

    @factory.post_generation
    def assignees(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for assignee in extracted:
                self.assignees.add(group)


class ReviewResponseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ReviewResponse

    request = None  # Set in test
    submitted_by = factory.LazyAttribute(lambda o: ReviewerFactory.create_internal())
    status = models.ReviewResponse.STATUS_APPROVED
    comment = "This is a comment"
