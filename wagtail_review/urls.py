from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

from . import views
from .api import urls as api_urls

app_name = 'wagtail_review'

urlpatterns = [
    url(r'^review/([\w\.\-\_]+)/$', views.review, name='review'),
    url(r'^api/', include(api_urls, namespace='api')),
]
