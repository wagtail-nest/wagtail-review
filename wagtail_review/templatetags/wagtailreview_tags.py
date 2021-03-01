from django import template

from wagtail_review.forms import ResponseForm

register = template.Library()


@register.inclusion_tag('wagtail_review/annotate.html', takes_context=True)
def wagtailreview(context):
    request = context['request']
    review_mode = getattr(request, 'wagtailreview_mode', None)
    reviewer = getattr(request, 'wagtailreview_reviewer', None)

    if review_mode == 'respond' or review_mode == 'comment':
        return {
            'mode': review_mode,
            'allow_annotations': (reviewer.review.status != 'closed'),
            'show_closed': (reviewer.review.status == 'closed'),
            'allow_responses': (review_mode == 'respond' and reviewer.review.status != 'closed'),
            'reviewer': reviewer,
            'token': reviewer.response_token,
            'response_form': ResponseForm()
        }
    elif review_mode == 'view':
        return {
            'mode': review_mode,
            'show_closed': False,
            'allow_annotations': False,
            'allow_responses': False,
            'reviewer': reviewer,
            'token': reviewer.view_token
        }

    else:
        return {'mode': None}
