from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from wagtail_review.views import frontend, annotations_api

app_name = 'wagtail_review'

urlpatterns = [
    url(r'^view/(\d+)/(\w+)/$', frontend.view, name='view'),
    url(r'^respond/(\d+)/(\w+)/$', frontend.respond, name='respond'),
    url(r'^api/$', annotations_api.root, name='annotations_api_root'),
    url(r'^api/search/$', annotations_api.search, name='annotations_api_search'),
    url(r'^api/annotations/$', annotations_api.index, name='annotations_api_index'),
    url(r'^api/annotations/(\d+)/$', annotations_api.item, name='annotations_api_item'),
]
