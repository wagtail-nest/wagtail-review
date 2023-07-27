from __future__ import absolute_import, unicode_literals

from django.urls import path
from django.views.generic import RedirectView
from wagtail_review.views import admin as admin_views

app_name = 'wagtail_review'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='wagtail_review_admin:dashboard')),
    path('create_review/', admin_views.create_review, name='create_review'),
    path('autocomplete_users/', admin_views.autocomplete_users, name='autocomplete_users'),
    path('reviews/', admin_views.DashboardView.as_view(), name='dashboard'),
    path('reviews/<int:pk>/', admin_views.AuditTrailView.as_view(), name='audit_trail'),
    path('reviews/<int:review_id>/view/', admin_views.view_review_page, name='view_review_page'),
    path('reviews/<int:review_id>/close/', admin_views.close_review, name='close_review'),
    path('reviews/<int:review_id>/close_and_publish/', admin_views.close_and_publish, name='close_and_publish'),
    path('reviews/<int:review_id>/reopen/', admin_views.reopen_review, name='reopen_review'),
]
