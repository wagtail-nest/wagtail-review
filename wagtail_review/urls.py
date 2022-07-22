from __future__ import absolute_import, unicode_literals

from django.urls import re_path
from wagtail_review.views import frontend, annotations_api

app_name = 'wagtail_review'

urlpatterns = [
    re_path(r'^view/(\d+)/(\w+)/$', frontend.view, name='view'),
    re_path(r'^respond/(\d+)/(\w+)/$', frontend.respond, name='respond'),
    re_path(r'^api/$', annotations_api.root, name='annotations_api_root'),
    re_path(r'^api/search/$', annotations_api.search, name='annotations_api_search'),
    re_path(r'^api/annotations/$', annotations_api.index, name='annotations_api_index'),
    re_path(r'^api/annotations/(\d+)/$', annotations_api.item, name='annotations_api_item'),
]
