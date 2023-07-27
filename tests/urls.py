from __future__ import absolute_import, unicode_literals

from django.conf.urls import include
from django.urls import path

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls

from wagtail_review import urls as wagtailreview_urls


urlpatterns = [
    path(r'admin/', include(wagtailadmin_urls)),
    path(r'review/', include(wagtailreview_urls)),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    path('', include(wagtail_urls)),
]
