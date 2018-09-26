from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from wagtail_review.views import frontend as views

app_name = 'wagtail_review'

urlpatterns = [
    url(r'^view/(\d+)/(\w+)/$', views.view, name='view'),
    url(r'^respond/(\d+)/(\w+)/$', views.respond, name='respond'),
]
