from django import template

register = template.Library()


@register.inclusion_tag('wagtail_review/annotate.html', takes_context=True)
def wagtailreview(context):
    request = context['request']
    token = getattr(request, 'wagtailreview_token', None)

    if token is not None:
        perms = getattr(request, 'wagtailreview_perms')
        review_request = getattr(request, 'wagtailreview_review_request', None)

        return {
            'allow_comments': perms.can_comment(),
            'allow_responses': review_request is not None and not review_request.is_closed,
            'token': token,
        }
    else:
        return {
            'allow_comments': False,
            'allow_responses': False,
            'token': None,
        }
