from wagtail.admin.modal_workflow import render_modal_workflow

from wagtail_review.forms import get_review_form_class


def create_review(request):
    ReviewForm = get_review_form_class()

    form = ReviewForm(prefix='create_review')

    return render_modal_workflow(
        request, 'wagtail_review/create_review.html', None, {
            'form': form
        }, json_data=None
    )
