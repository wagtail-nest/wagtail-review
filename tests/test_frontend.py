from django.contrib.auth.models import User
from django.test import TestCase

from wagtail.core.models import Page

from tests.models import SimplePage


class TestReviewView(TestCase):
    fixtures = ['test.json']
