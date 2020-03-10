from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from wagtail.core.models import Page, Site

from wagtail_review.models import Share
from wagtail_review.token import Token

from .factories import ReviewerFactory
from .models import SimplePage


class TestReviewView(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        homepage = Page.objects.get(url_path='/home/').specific
        self.page = homepage.add_child(instance=SimplePage(title="A simple page"))
        self.page_revision = self.page.save_revision()
        self.reviewer = ReviewerFactory.create_external()
        self.token = Token(self.reviewer, self.page_revision)
        self.share = Share.objects.create(
            external_user=self.reviewer.external,
            page=self.page,
            can_comment=True,
            shared_by=User.objects.get(username="homer"),
        )

        # Need to update site record so the hostname matches what Django will sent to the view
        # This prevents a 400 (Bad Request) error when the preview is generated
        Site.objects.update(hostname="testserver")

    def test_get_review(self):
        response = self.client.get(reverse('wagtail_review:review', args=[self.token.encode()]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')

        self.share.refresh_from_db()
        self.assertTrue(self.share.first_accessed_at)
        self.assertTrue(self.share.last_accessed_at)

    def test_get_review_without_share(self):
        self.share.delete()
        response = self.client.get(reverse('wagtail_review:review', args=[self.token.encode()]))
        self.assertEqual(response.status_code, 403)

    def test_get_review_with_expired_share(self):
        self.share.expires_at = timezone.now()
        self.share.save()

        response = self.client.get(reverse('wagtail_review:review', args=[self.token.encode()]))
        self.assertEqual(response.status_code, 403)
