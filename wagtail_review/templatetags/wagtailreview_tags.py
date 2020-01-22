from django import template

register = template.Library()


@register.inclusion_tag('wagtail_review/annotate.html', takes_context=True)
def wagtailreview(context):
    request = context['request']
    token = getattr(request, 'wagtailreview_token', None)

    if token is not None:
        perms = getattr(request, 'wagtailreview_perms')
        task_state = getattr(request, 'wagtailreview_task_state', None)

        return {
            'allow_comments': perms.can_comment(),
            'allow_responses': task_state is not None,
            'token': token,
        }
    else:
        return {
            'allow_comments': False,
            'allow_responses': False,
            'token': None,
        }
