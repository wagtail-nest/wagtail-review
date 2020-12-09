from django.contrib.auth.models import User
from django.core import mail
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from wagtail.core.models import Page

from wagtail_review.models import Comment, ExternalReviewer, Reviewer, Share

from .factories import ReviewerFactory


class TestShareModel(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.homer = User.objects.get(username="homer")
        self.bart = ExternalReviewer.objects.create(email="bart@example.com")

    def test_send_share_email(self):
        share = Share.objects.create(external_user=self.bart, shared_by=self.homer, page_id=2)

        share.send_share_email()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].recipients(), ["bart@example.com"])

    def test_log_access(self):
        share = Share.objects.create(external_user=self.bart, shared_by=self.homer, page_id=2)

        self.assertIsNone(share.first_accessed_at)
        self.assertIsNone(share.last_accessed_at)

        share.log_access()

        self.assertIsNotNone(share.first_accessed_at)
        self.assertIsNotNone(share.last_accessed_at)
        self.assertEqual(share.first_accessed_at, share.last_accessed_at)

        initial_first_accessed_at = share.first_accessed_at

        share.log_access()

        self.assertEqual(initial_first_accessed_at, share.first_accessed_at)
        self.assertNotEqual(share.first_accessed_at, share.last_accessed_at)


class TestReviewerModel(TestCase):
    fixtures = ['test.json']

    def test_internal_reviewer(self):
        homer = User.objects.get(username="homer")
        reviewer = Reviewer.objects.create(internal=homer)

        self.assertEqual(reviewer.get_name(), "Homer Simpson")
        self.assertEqual(reviewer.get_email(), "homer@example.com")

        page_perms = reviewer.page_perms(2)
        self.assertTrue(page_perms.can_view())
        self.assertTrue(page_perms.can_comment())

    def test_external_reviewer(self):
        bart = ExternalReviewer.objects.create(email="bart@example.com")
        reviewer = Reviewer.objects.create(external=bart)

        self.assertEqual(reviewer.get_name(), "bart@example.com")
        self.assertEqual(reviewer.get_email(), "bart@example.com")

        page_perms = reviewer.page_perms(2)
        self.assertFalse(page_perms.can_view())
        self.assertFalse(page_perms.can_comment())

    # Test external user with shares

    def test_external_reviewer_with_share(self):
        bart = ExternalReviewer.objects.create(email="bart@example.com")
        reviewer = Reviewer.objects.create(external=bart)

        homer = User.objects.get(username="homer")
        Share.objects.create(external_user=bart, shared_by=homer, page_id=2, can_comment=True)

        page_perms = reviewer.page_perms(2)
        self.assertTrue(page_perms.can_view())
        self.assertTrue(page_perms.can_comment())

    def test_external_reviewer_with_share_but_no_commenting(self):
        bart = ExternalReviewer.objects.create(email="bart@example.com")
        reviewer = Reviewer.objects.create(external=bart)

        homer = User.objects.get(username="homer")
        Share.objects.create(external_user=bart, shared_by=homer, page_id=2, can_comment=False)

        page_perms = reviewer.page_perms(2)
        self.assertTrue(page_perms.can_view())
        self.assertFalse(page_perms.can_comment())

    def test_external_reviewer_with_expired_share(self):
        bart = ExternalReviewer.objects.create(email="bart@example.com")
        reviewer = Reviewer.objects.create(external=bart)

        homer = User.objects.get(username="homer")
        Share.objects.create(external_user=bart, shared_by=homer, page_id=2, can_comment=True, expires_at=timezone.now())

        page_perms = reviewer.page_perms(2)
        self.assertFalse(page_perms.can_view())
        self.assertFalse(page_perms.can_comment())

    # Test database constraints

    def test_cant_create_duplicate_internal_user(self):
        homer = User.objects.get(username="homer")

        Reviewer.objects.create(internal=homer)

        with self.assertRaises(IntegrityError):
            Reviewer.objects.create(internal=homer)

    def test_cant_create_duplicate_external_user(self):
        bart = ExternalReviewer.objects.create(email="bart@example.com")

        Reviewer.objects.create(external=bart)

        with self.assertRaises(IntegrityError):
            Reviewer.objects.create(external=bart)

    def test_cant_create_both_internal_and_external(self):
        homer = User.objects.get(username="homer")
        bart = ExternalReviewer.objects.create(email="bart@example.com")

        with self.assertRaises(IntegrityError):
            Reviewer.objects.create(internal=homer, external=bart)


class TestCommentModel(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        reviewer = ReviewerFactory.create_internal()

        self.comment = Comment.objects.create(
            page_revision=Page.objects.get(id=2).save_revision(),
            reviewer=reviewer,
            quote="Test",
            text="Foo",
            content_path="title",
            start_xpath=".",
            start_offset=0,
            end_xpath=".",
            end_offset =0,
        )

    def test_get_frontend_url(self):
        reviewer = ReviewerFactory.create_external()

        self.assertTrue(self.comment.get_frontend_url(reviewer))
