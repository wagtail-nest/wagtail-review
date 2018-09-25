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
        response_json = json.loads(response.content)
        self.assertEqual(response_json['step'], 'form')

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

    def test_validate_reviewers_required(self):
        # reject a completely empty formset
        response = self.client.post('/admin/wagtail_review/create_review/', {
            'create_review_reviewers-TOTAL_FORMS': 0,
            'create_review_reviewers-INITIAL_FORMS': 0,
            'create_review_reviewers-MIN_NUM_FORMS': 0,
            'create_review_reviewers-MAX_NUM_FORMS': 1000,
        })
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json['step'], 'form')
        self.assertFormsetError(response, 'reviewer_formset', None, None, "Please select one or more reviewers.")

        # reject a formset with only deleted items
        response = self.client.post('/admin/wagtail_review/create_review/', {
            'create_review_reviewers-TOTAL_FORMS': 1,
            'create_review_reviewers-INITIAL_FORMS': 0,
            'create_review_reviewers-MIN_NUM_FORMS': 0,
            'create_review_reviewers-MAX_NUM_FORMS': 1000,

            'create_review_reviewers-0-user': '',
            'create_review_reviewers-0-email': 'someone@example.com',
            'create_review_reviewers-0-DELETE': '1',
        })
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json['step'], 'form')
        self.assertFormsetError(response, 'reviewer_formset', None, None, "Please select one or more reviewers.")

    def test_validate_ok(self):
        response = self.client.post('/admin/wagtail_review/create_review/', {
            'create_review_reviewers-TOTAL_FORMS': 1,
            'create_review_reviewers-INITIAL_FORMS': 0,
            'create_review_reviewers-MIN_NUM_FORMS': 0,
            'create_review_reviewers-MAX_NUM_FORMS': 1000,

            'create_review_reviewers-0-user': '',
            'create_review_reviewers-0-email': 'someone@example.com',
            'create_review_reviewers-0-DELETE': '',
        })
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json['step'], 'done')
