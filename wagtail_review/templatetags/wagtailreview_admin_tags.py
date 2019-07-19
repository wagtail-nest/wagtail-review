from django import template

from ..models import ReviewRequest

register = template.Library()


@register.simple_tag
def page_has_open_review(page):
    return ReviewRequest.objects.filter(page_revision__page=page).open().exists()
