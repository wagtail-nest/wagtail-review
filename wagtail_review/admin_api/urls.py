from django.conf.urls import url

from . import views

app_name = 'wagtail_review_admin_api'
urlpatterns = [
    url(r'^page/(?P<pk>\d+)/shares/$', views.PageShares.as_view(), name='page_shares'),
    url(r'^page/(?P<pk>\d+)/comments/$', views.PageComments.as_view(), name='page_comments'),
]
