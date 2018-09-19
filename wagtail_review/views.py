from wagtail.admin.modal_workflow import render_modal_workflow


def create_review(request):
    return render_modal_workflow(
        request, 'wagtail_review/create_review.html', None, {}, json_data=None
    )
