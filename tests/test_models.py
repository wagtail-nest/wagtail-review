from django.test import TestCase

from wagtail.core.models import Page

from wagtail_review.models import Review, Reviewer


class TestReviewerModel(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.homepage = Page.objects.get(url_path='/home/').specific
        self.revision = self.homepage.save_revision()
        self.review = Review.objects.create(page_revision=self.revision)

    def test_tokens_are_assigned(self):
        """Test that response_token and view_token are populated on save"""
        reviewer = Reviewer.objects.create(review=self.review, email='bob@example.com')
        self.assertRegexpMatches(reviewer.response_token, r'^\w{16}$')
        self.assertRegexpMatches(reviewer.view_token, r'^\w{16}$')
