from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from wagtail_review.views import frontend

app_name = 'wagtail_review'

urlpatterns = [
    url(r'^view/(\d+)/([\.\-\_\w]+)/$', frontend.view, name='view'),
    url(r'^respond/(\d+)/([\.\-\_\w]+)/$', frontend.respond, name='respond'),
]
