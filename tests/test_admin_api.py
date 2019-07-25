import unittest

from django.contrib.auth.models import User
from django.core import mail
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

import pytz
from dateutil.parser import parse as parse_date
from rest_framework.test import APIClient
from wagtail.core.models import Page

from wagtail_review.models import (
    Comment, CommentReply, ExternalReviewer, Reviewer, ReviewRequest, ReviewResponse, Share)
from wagtail_review.token import Token

from .factories import CommentFactory, CommentReplyFactory, ReviewerFactory, ShareFactory


class AdminAPITestCase(TestCase):
    fixtures = ['test.json']
    client_class = APIClient

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', email='admin@example.com', password='password')
        self.client.login(username='admin', password='password')

        self.page = Page.objects.get(id=2)
        self.page_revision = self.page.save_revision()
        self.other_page_revision = self.page.save_revision()

        self.other_page = Page.objects.get(id=1)
        self.other_page_page_revision = self.other_page.save_revision()


def check_share_api_representation(self, share, data):
    self.assertEqual(data['id'], share.id)
    self.assertEqual(data['user'], {
        'email': share.external_user.email,
    })
    self.assertEqual(parse_date(data['shared_at']), share.shared_at)
    self.assertEqual(parse_date(data['first_accessed_at']) if data['first_accessed_at'] else None, share.first_accessed_at)
    self.assertEqual(parse_date(data['last_accessed_at']) if data['last_accessed_at'] else None, share.last_accessed_at)
    self.assertEqual(parse_date(data['expires_at']) if data['expires_at'] else None, share.expires_at)


def check_comment_api_representation(self, comment, data):
    self.assertEqual(data['id'], comment.id)
    self.assertEqual(data['author'], {
        'id': comment.reviewer.id,
        'name': comment.reviewer.get_name()
    })
    self.assertEqual(data['quote'], comment.quote)
    self.assertEqual(data['text'], comment.text)
    self.assertEqual(parse_date(data['created_at']), comment.created_at)
    self.assertEqual(parse_date(data['updated_at']), comment.updated_at)
    self.assertIsNone(data['resolved_at'])
    self.assertEqual(data['content_path'], comment.content_path)
    self.assertEqual(data['start_xpath'], comment.start_xpath)
    self.assertEqual(data['start_offset'], comment.start_offset)
    self.assertEqual(data['end_xpath'], comment.end_xpath)
    self.assertEqual(data['end_offset'], comment.end_offset)
    self.assertEqual(data['replies'], [])


class TestSharesView(AdminAPITestCase):
    def test_get_shares(self):
        share_a = ShareFactory.create(page=self.page)
        share_b = ShareFactory.create(page=self.page, expires_at=timezone.now())
        share_other_page = ShareFactory.create(page=self.other_page)

        response = self.client.get(reverse('wagtail_review_admin:api:page_shares', args=[self.page.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        self.assertEqual(set(share['id'] for share in response.json()), {share_a.id, share_b.id})

        check_share_api_representation(self, share_a, response.json()[0])

    def test_post_new_share(self):
        post_data = {
            'email': "foo@bar.com",
        }

        response = self.client.post(reverse('wagtail_review_admin:api:page_shares', args=[self.page.id]), post_data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['Content-Type'], 'application/json')

        share = Share.objects.get()

        check_share_api_representation(self, share, response.json())

        self.assertEqual(share.external_user.email, 'foo@bar.com')
        self.assertEqual(share.page, self.page)
        self.assertEqual(share.shared_by, self.user)

        # The user should've been sent an invite email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].recipients(), ['foo@bar.com'])

    def test_post_new_share_already_shared_with_email(self):
        share = ShareFactory.create(page=self.page)

        post_data = {
            'email': share.external_user.email,
        }

        response = self.client.post(reverse('wagtail_review_admin:api:page_shares', args=[self.page.id]), post_data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json(), {
            'email': 'This page has already been shared with this email address'
        })


class TestCommentsView(AdminAPITestCase):
    def test_get_comments(self):
        comment_a = CommentFactory.create(page_revision=self.page_revision)
        comment_b = CommentFactory.create(page_revision=self.page_revision)
        comment_on_another_revision = CommentFactory.create(page_revision=self.other_page_revision)
        comment_on_another_page = CommentFactory.create(page_revision=self.other_page_page_revision)

        response = self.client.get(reverse('wagtail_review_admin:api:page_comments', args=[self.page.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        self.assertEqual(set(share['id'] for share in response.json()), {comment_a.id, comment_b.id, comment_on_another_revision.id})

        check_comment_api_representation(self, comment_on_another_revision, response.json()[0])
