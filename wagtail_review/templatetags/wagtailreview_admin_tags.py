from django import template

import swapper

Review = swapper.load_model('wagtail_review', 'Review')

register = template.Library()


@register.simple_tag
def page_has_open_review(page):
    return bool(Review.objects.filter(page_revision__page=page, status='open'))
