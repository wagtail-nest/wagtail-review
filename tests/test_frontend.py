from django.contrib.auth.models import User
from django.test import TestCase

from wagtail.core.models import Page

from wagtail_review.models import Review, Reviewer
from tests.models import SimplePage


class TestFrontendViews(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='password'
        )

        self.homepage = Page.objects.get(url_path='/home/').specific
        self.page = SimplePage(title="Simple page original", slug="simple-page")
        self.homepage.add_child(instance=self.page)

        self.page.title = "Simple page submitted"
        submitted_revision = self.page.save_revision()
        self.review = Review.objects.create(page_revision=submitted_revision, submitter=self.admin_user)
        self.reviewer = Reviewer.objects.create(review=self.review, user=User.objects.get(username='spongebob'))

        self.page.title = "Simple page with draft edit"
        self.page.save_revision()

    def test_view_token_must_match(self):
        response = self.client.get('/review/view/%d/xxxxx/' % self.reviewer.id)
        self.assertEqual(response.status_code, 403)

    def test_view(self):
        response = self.client.get('/review/view/%d/%s/' % (self.reviewer.id, self.reviewer.view_token))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Simple page submitted</h1>")
        self.assertContains(response, "var app = new annotator.App();")
        self.assertContains(response, "app.include(annotatorExt.viewerModeUi);")

    def test_response_token_must_match(self):
        response = self.client.get('/review/respond/%d/xxxxx/' % self.reviewer.id)
        self.assertEqual(response.status_code, 403)

    def test_respond_view(self):
        response = self.client.get('/review/respond/%d/%s/' % (self.reviewer.id, self.reviewer.response_token))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Simple page submitted</h1>")
        self.assertContains(response, "var app = new annotator.App();")
        self.assertContains(response, "app.include(annotator.ui.main,")

    def test_live_page_has_no_annotator_js(self):
        response = self.client.get('/simple-page/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Simple page original</h1>")
        self.assertNotContains(response, "var app = new annotator.App();")
