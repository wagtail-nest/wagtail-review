from django import template

register = template.Library()


@register.inclusion_tag('wagtail_review/annotate.html', takes_context=True)
def wagtailreview(context):
    request = context['request']

    return {
        'request': request,
        'mode': getattr(request, 'wagtailreview_mode', None),
    }
