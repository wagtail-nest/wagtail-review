from __future__ import absolute_import, unicode_literals

from django.urls import path
from wagtail_review.views import frontend, annotations_api

app_name = 'wagtail_review'

urlpatterns = [
    path('view/<int:reviewer_id>/<slug:token>/', frontend.view, name='view'),
    path('respond/<int:reviewer_id>/<slug:token>/', frontend.respond, name='respond'),
    path('api/', annotations_api.root, name='annotations_api_root'),
    path('api/search/', annotations_api.search, name='annotations_api_search'),
    path('api/annotations/', annotations_api.index, name='annotations_api_index'),
    path('api/annotations/<int:id>/', annotations_api.item, name='annotations_api_item'),
]
