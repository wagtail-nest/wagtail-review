from __future__ import absolute_import, unicode_literals

from django.urls import re_path
from django.views.generic import RedirectView
from wagtail_review.views import admin as admin_views

app_name = 'wagtail_review'

urlpatterns = [
    re_path(r'^$', RedirectView.as_view(pattern_name='wagtail_review_admin:dashboard')),
    re_path(r'^create_review/$', admin_views.create_review, name='create_review'),
    re_path(r'^autocomplete_users/$', admin_views.autocomplete_users, name='autocomplete_users'),
    re_path(r'^reviews/$', admin_views.DashboardView.as_view(), name='dashboard'),
    re_path(r'^reviews/(?P<pk>\d+)/$', admin_views.AuditTrailView.as_view(), name='audit_trail'),
    re_path(r'^reviews/(?P<review_id>\d+)/view/$', admin_views.view_review_page, name='view_review_page'),
    re_path(r'^reviews/(?P<review_id>\d+)/close/$', admin_views.close_review, name='close_review'),
    re_path(r'^reviews/(?P<review_id>\d+)/close_and_publish/$', admin_views.close_and_publish, name='close_and_publish'),
    re_path(r'^reviews/(?P<review_id>\d+)/reopen/$', admin_views.reopen_review, name='reopen_review'),
]
