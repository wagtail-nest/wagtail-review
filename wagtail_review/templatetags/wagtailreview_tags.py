from django import template

register = template.Library()


@register.inclusion_tag('wagtail_review/annotate.html', takes_context=True)
def wagtailreview(context):
    request = context['request']
    review_mode = getattr(request, 'wagtailreview_mode', None)
    reviewer = getattr(request, 'wagtailreview_reviewer', None)

    if review_mode == 'respond':
        return {
            'mode': review_mode,
            'reviewer': reviewer,
            'token': reviewer.response_token
        }

    elif review_mode == 'view':
        return {
            'mode': review_mode,
            'reviewer': reviewer,
            'url': reviewer.view_token
        }

    else:
        return {'mode': None}
