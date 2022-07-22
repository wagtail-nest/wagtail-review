from __future__ import absolute_import, unicode_literals

from django.conf.urls import include
from django.urls import re_path

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.core import urls as wagtail_urls

from wagtail_review import urls as wagtailreview_urls


urlpatterns = [
    re_path(r'^admin/', include(wagtailadmin_urls)),
    re_path(r'^review/', include(wagtailreview_urls)),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    re_path(r'', include(wagtail_urls)),
]
