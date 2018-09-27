from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from wagtail.core.models import Page

from wagtail_review.models import Review, Reviewer


class TestReviewerModel(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.homepage = Page.objects.get(url_path='/home/').specific
        self.revision = self.homepage.save_revision()
        self.review = Review.objects.create(page_revision=self.revision, submitter=User.objects.first())

    def test_tokens_are_assigned(self):
        """Test that response_token and view_token are populated on save"""
        reviewer = Reviewer.objects.create(review=self.review, email='bob@example.com')
        self.assertRegexpMatches(reviewer.response_token, r'^\w{16}$')
        self.assertRegexpMatches(reviewer.view_token, r'^\w{16}$')

    def test_validate_email_or_user_required(self):
        reviewer = Reviewer(review=self.review)
        with self.assertRaises(ValidationError):
            reviewer.full_clean()

    def test_get_email_address(self):
        reviewer1 = Reviewer(review=self.review, email='bob@example.com')
        reviewer2 = Reviewer(review=self.review, user=User.objects.get(username='spongebob'))
        self.assertEqual(reviewer1.get_email_address(), 'bob@example.com')
        self.assertEqual(reviewer2.get_email_address(), 'spongebob@example.com')

    def test_get_respond_url(self):
        reviewer = Reviewer.objects.create(review=self.review, email='bob@example.com')
        self.assertEqual(
            reviewer.get_respond_url(),
            '/review/respond/%d/%s/' % (reviewer.id, reviewer.response_token)
        )
        self.assertEqual(
            reviewer.get_respond_url(absolute=True),
            'http://test.local/review/respond/%d/%s/' % (reviewer.id, reviewer.response_token)
        )

    def test_get_view_url(self):
        reviewer = Reviewer.objects.create(review=self.review, email='bob@example.com')
        self.assertEqual(
            reviewer.get_view_url(),
            '/review/view/%d/%s/' % (reviewer.id, reviewer.view_token)
        )
        self.assertEqual(
            reviewer.get_view_url(absolute=True),
            'http://test.local/review/view/%d/%s/' % (reviewer.id, reviewer.view_token)
        )
