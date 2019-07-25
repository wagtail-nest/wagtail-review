import json

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from wagtail.core.models import Page

from wagtail_review.models import ReviewRequest

from .factories import ReviewRequestFactory


class TestCreateReview(TestCase):
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

    def test_validate_assignees_required(self):
        # reject a completely empty formset
        response = self.client.post('/admin/wagtail_review/create_review/', {
            'create_review_assignees-TOTAL_FORMS': 0,
            'create_review_assignees-INITIAL_FORMS': 0,
            'create_review_assignees-MIN_NUM_FORMS': 0,
            'create_review_assignees-MAX_NUM_FORMS': 1000,
        })
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json['step'], 'form')
        self.assertFormsetError(response, 'reviewer_formset', None, None, "Please select one or more reviewers.")

    def test_validate_assignees_required_when_all_deleted(self):
        # reject a formset with only deleted items
        response = self.client.post('/admin/wagtail_review/create_review/', {
            'create_review_assignees-TOTAL_FORMS': 1,
            'create_review_assignees-INITIAL_FORMS': 0,
            'create_review_assignees-MIN_NUM_FORMS': 0,
            'create_review_assignees-MAX_NUM_FORMS': 1000,

            'create_review_assignees-0-user': '',
            'create_review_assignees-0-email': 'someone@example.com',
            'create_review_assignees-0-DELETE': '1',
        })
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json['step'], 'form')
        self.assertFormsetError(response, 'reviewer_formset', None, None, "Please select one or more reviewers.")

    def test_validate_ok(self):
        response = self.client.post('/admin/wagtail_review/create_review/', {
            'create_review_assignees-TOTAL_FORMS': 1,
            'create_review_assignees-INITIAL_FORMS': 0,
            'create_review_assignees-MIN_NUM_FORMS': 0,
            'create_review_assignees-MAX_NUM_FORMS': 1000,

            'create_review_assignees-0-user': '',
            'create_review_assignees-0-email': 'someone@example.com',
            'create_review_assignees-0-DELETE': '',
        })
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json['step'], 'done')

    def test_post_edit_form(self):
        response = self.client.post('/admin/pages/2/edit/', {
            'title': "Home submitted",
            'slug': 'title',

            'create_review_assignees-TOTAL_FORMS': 2,
            'create_review_assignees-INITIAL_FORMS': 0,
            'create_review_assignees-MIN_NUM_FORMS': 0,
            'create_review_assignees-MAX_NUM_FORMS': 1000,

            'create_review_assignees-0-user': '',
            'create_review_assignees-0-email': 'someone@example.com',
            'create_review_assignees-0-DELETE': '',

            'create_review_assignees-1-user': User.objects.get(username='spongebob').pk,
            'create_review_assignees-1-email': '',
            'create_review_assignees-1-DELETE': '',

            'action-submit-for-review': '1',
        })

        self.assertRedirects(response, '/admin/pages/1/')

        revision = self.homepage.get_latest_revision()
        review = ReviewRequest.objects.get(page_revision=revision)
        self.assertEqual(review.assignees.count(), 2)

        reviewer_emails = set(reviewer.get_email() for reviewer in review.assignees.all())
        self.assertEqual(reviewer_emails, {'someone@example.com', 'spongebob@example.com'})

        self.assertEqual(len(mail.outbox), 2)
        email_recipients = set(email.to[0] for email in mail.outbox)
        self.assertEqual(email_recipients, {'someone@example.com', 'spongebob@example.com'})

    def test_post_create_form(self):
        response = self.client.post('/admin/pages/add/tests/simplepage/2/', {
            'title': "Subpage submitted",
            'slug': 'subpage-submitted',

            'create_review_assignees-TOTAL_FORMS': 2,
            'create_review_assignees-INITIAL_FORMS': 0,
            'create_review_assignees-MIN_NUM_FORMS': 0,
            'create_review_assignees-MAX_NUM_FORMS': 1000,

            'create_review_assignees-0-user': '',
            'create_review_assignees-0-email': 'someone@example.com',
            'create_review_assignees-0-DELETE': '',

            'create_review_assignees-1-user': User.objects.get(username='spongebob').pk,
            'create_review_assignees-1-email': '',
            'create_review_assignees-1-DELETE': '',

            'action-submit-for-review': '1',
        })

        self.assertRedirects(response, '/admin/pages/2/')

        revision = Page.objects.get(slug='subpage-submitted').get_latest_revision()
        review = ReviewRequest.objects.get(page_revision=revision)
        self.assertEqual(review.assignees.count(), 2)

        reviewer_emails = set(reviewer.get_email() for reviewer in review.assignees.all())
        self.assertEqual(reviewer_emails, {'someone@example.com', 'spongebob@example.com'})

        self.assertEqual(len(mail.outbox), 2)
        email_recipients = set(email.to[0] for email in mail.outbox)
        self.assertEqual(email_recipients, {'someone@example.com', 'spongebob@example.com'})


class TestAuditTrail(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='admin@example.com', password='password')
        self.client.login(username='admin', password='password')
        self.homepage = Page.objects.get(url_path='/home/').specific

        self.page_revision = self.homepage.save_revision()
        self.review_request = ReviewRequestFactory.create(page_revision=self.page_revision, submitted_by=self.user)

    def test_get_dashboard(self):
        response = self.client.get(reverse('wagtail_review_admin:dashboard'))

        self.assertEqual(response.status_code, 200)

    def test_get_audit_trail(self):
        response = self.client.get(reverse('wagtail_review_admin:audit_trail', args=[self.homepage.id]))

        self.assertEqual(response.status_code, 200)

    def test_close_review(self):
        self.assertFalse(self.review_request.is_closed)

        response = self.client.post(reverse('wagtail_review_admin:close_review', args=[self.review_request.id]))
        self.assertRedirects(response, reverse('wagtail_review_admin:audit_trail', args=[self.homepage.id]))

        # The review should be closed
        self.review_request.refresh_from_db()
        self.assertTrue(self.review_request.is_closed)

        # The revision shouldn't have been published
        self.homepage.refresh_from_db()
        self.assertNotEqual(self.homepage.live_revision, self.page_revision)

    def test_close_and_publish_review(self):
        self.assertFalse(self.review_request.is_closed)

        response = self.client.post(reverse('wagtail_review_admin:close_and_publish', args=[self.review_request.id]))
        self.assertRedirects(response, reverse('wagtail_review_admin:audit_trail', args=[self.homepage.id]))

        # The review should be closed
        self.review_request.refresh_from_db()
        self.assertTrue(self.review_request.is_closed)

        # The revision should have been published
        self.homepage.refresh_from_db()
        self.assertEqual(self.homepage.live_revision, self.page_revision)

    def test_reopen_review(self):
        self.review_request.is_closed = True
        self.review_request.save()

        response = self.client.post(reverse('wagtail_review_admin:reopen_review', args=[self.review_request.id]))
        self.assertRedirects(response, reverse('wagtail_review_admin:audit_trail', args=[self.homepage.id]))

        # The review should be open again
        self.review_request.refresh_from_db()
        self.assertFalse(self.review_request.is_closed)
