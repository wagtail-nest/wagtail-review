from django import template
from django.contrib.contenttypes.models import ContentType
from wagtail.models import Page

import swapper

from wagtail_review.text import user_display_name

Review = swapper.load_model('wagtail_review', 'Review')

register = template.Library()


@register.simple_tag
def page_has_open_review(page):
    return bool(Review.objects.filter(
        page_revision__object_id=str(page.pk), page_revision__base_content_type=ContentType.objects.get_for_model(Page), status='open'
    ))


register.filter(user_display_name)
