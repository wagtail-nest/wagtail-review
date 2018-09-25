from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse

from wagtail.admin.modal_workflow import render_modal_workflow

from wagtail_review.forms import get_review_form_class, ReviewerFormSet


User = get_user_model()


def create_review(request):
    ReviewForm = get_review_form_class()

    form = ReviewForm(prefix='create_review')
    reviewer_formset = ReviewerFormSet(prefix='create_review_reviewers')

    return render_modal_workflow(
        request, 'wagtail_review/create_review.html', None, {
            'form': form,
            'reviewer_formset': reviewer_formset,
        }, json_data={'step': 'form'}
    )


def autocomplete_users(request):
    q = request.GET.get('q', '')

    terms = q.split()
    if terms:
        conditions = Q()

        model_fields = [f.name for f in User._meta.get_fields()]

        for term in terms:
            if 'username' in model_fields:
                conditions |= Q(username__icontains=term)

            if 'first_name' in model_fields:
                conditions |= Q(first_name__icontains=term)

            if 'last_name' in model_fields:
                conditions |= Q(last_name__icontains=term)

            if 'email' in model_fields:
                conditions |= Q(email__icontains=term)

        users = User.objects.filter(conditions)
    else:
        users = User.objects.none()

    result_data = [
        {
            'id': user.pk,
            'full_name': user.get_full_name(),
            'username': user.get_username(),
        }
        for user in users
    ]

    return JsonResponse({'results': result_data})
