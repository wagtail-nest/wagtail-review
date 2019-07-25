from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.views.generic import RedirectView

from wagtail_review.admin_api import urls as api_urls
from wagtail_review.views import admin as admin_views

app_name = 'wagtail_review'

urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name='wagtail_review_admin:dashboard')),
    url(r'^create_review/$', admin_views.create_review, name='create_review'),
    url(r'^autocomplete_users/$', admin_views.autocomplete_users, name='autocomplete_users'),
    url(r'^reviews/$', admin_views.DashboardView.as_view(), name='dashboard'),
    url(r'^reviews/(?P<pk>\d+)/$', admin_views.AuditTrailView.as_view(), name='audit_trail'),
    url(r'^reviews/(?P<review_id>\d+)/close/$', admin_views.close_review, name='close_review'),
    url(r'^reviews/(?P<review_id>\d+)/close_and_publish/$', admin_views.close_and_publish, name='close_and_publish'),
    url(r'^reviews/(?P<review_id>\d+)/reopen/$', admin_views.reopen_review, name='reopen_review'),
    url(r'^api/', include(api_urls, namespace='api')),
]
