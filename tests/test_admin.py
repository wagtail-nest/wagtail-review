import json

from django.contrib.auth.models import User
from django.test import TestCase

from wagtail.core.models import Page


class TestAdminViews(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        User.objects.create_superuser(username='admin', email='admin@example.com', password='password')
        self.assertTrue(
            self.client.login(username='admin', password='password')
        )
        self.homepage = Page.objects.get(url_path='/home/').specific

    def test_submit_for_review_action(self):
        """Test that 'submit for review' appears in the page action menu"""
        response = self.client.get('/admin/pages/%d/edit/' % self.homepage.pk)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Submit for review")
        # check that JS is imported
        self.assertContains(response, "wagtail_review/js/submit.js")

    def test_create_review(self):
        response = self.client.get('/admin/wagtail_review/create_review/')
        self.assertEqual(response.status_code, 200)

    def test_user_autocomplete(self):
        response = self.client.get('/admin/wagtail_review/autocomplete_users/?q=homer')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['results'], [
            {'id': 2, 'full_name': 'Homer Simpson', 'username': 'homer'}
        ])

        response = self.client.get('/admin/wagtail_review/autocomplete_users/?q=pants')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['results'], [
            {'id': 1, 'full_name': 'Spongebob Squarepants', 'username': 'spongebob'}
        ])
