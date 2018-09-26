from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from wagtail_review.views import admin as admin_views

app_name = 'wagtail_review'

urlpatterns = [
    url(r'^create_review/$', admin_views.create_review, name='create_review'),
    url(r'^autocomplete_users/$', admin_views.autocomplete_users, name='autocomplete_users'),
]
