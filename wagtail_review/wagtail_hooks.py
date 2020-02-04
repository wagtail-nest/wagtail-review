from django.conf import settings
from django.conf.urls import include, url
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from wagtail.admin.action_menu import ActionMenuItem
from wagtail.core import hooks

from .admin_api import urls as api_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    admin_urls = [
        url(r'^api/', include(api_urls, namespace='api')),
    ]

    return [
        url(r'^wagtail_review/', include((admin_urls, 'wagtail_review_admin'), namespace='wagtail_review_admin')),
    ]


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        'wagtail_review/js/wagtail-review-admin.js',
    ]
    js_includes = format_html_join(
        '\n',
        '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes


# Inject code into the action menu that tells the UI which page is being viewed
# This isn't actually a menu item. It's the only way to inject code into the Wagtail
# editor where we also have the page ID
class GuacamoleMenuItem(ActionMenuItem):
    def render_html(self, request, context):
        return mark_safe(f"<script>window.wagtailPageId = {context['page'].id};</script>")


@hooks.register('register_page_action_menu_item')
def register_guacamole_menu_item():
    return GuacamoleMenuItem(order=10)
