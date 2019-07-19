from django import template

register = template.Library()


@register.inclusion_tag('wagtail_review/annotate.html', takes_context=True)
def wagtailreview(context):
    request = context['request']
    review_mode = getattr(request, 'wagtailreview_mode', None)
    reviewer = getattr(request, 'wagtailreview_reviewer', None)

    if review_mode == 'respond' or review_mode == 'comment':
        review_request = reviewer.review.into_review_request()

        return {
            'mode': review_mode,
            'allow_comments': (reviewer.review.status != 'closed'),
            'show_closed': (reviewer.review.status == 'closed'),
            'allow_responses': (review_mode == 'respond' and reviewer.review.status != 'closed'),
            'reviewer': reviewer,
            'token': reviewer.into_user().get_review_token(reviewer.review.page_revision_id, review_request_id=review_request.id if review_mode == 'respond' else None),
        }
    elif review_mode == 'view':
        return {
            'mode': review_mode,
            'show_closed': False,
            'allow_comments': False,
            'allow_responses': False,
            'reviewer': reviewer,
            'token': reviewer.into_user().get_review_token(reviewer.review.page_revision_id),
        }

    else:
        return {'mode': None}
