from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

from wagtail_review.api import urls as api_urls
from wagtail_review.views import frontend

app_name = 'wagtail_review'

urlpatterns = [
    url(r'^review/([\w\.\-\_]+)/$', frontend.review, name='review'),
    url(r'^api/', include(api_urls, namespace='api')),
]
