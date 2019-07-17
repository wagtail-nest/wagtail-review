from __future__ import absolute_import, unicode_literals

from django.conf.urls import url, include
from wagtail_review.views import frontend
from wagtail_review.api import urls as api_urls

app_name = 'wagtail_review'

urlpatterns = [
    url(r'^view/(\d+)/(\w+)/$', frontend.view, name='view'),
    url(r'^respond/(\d+)/(\w+)/$', frontend.respond, name='respond'),
    url(r'^api/', include(api_urls, namespace='api')),
]
