from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from wagtail_review import views

app_name = 'wagtail_review'

urlpatterns = [
    url(r'^create_review/$', views.create_review, name='create_review'),
]
