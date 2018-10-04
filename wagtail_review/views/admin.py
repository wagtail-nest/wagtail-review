from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView

import swapper

from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.views import generic
from wagtail.core.models import UserPagePermissionsProxy

from wagtail_review.forms import get_review_form_class, ReviewerFormSet


Review = swapper.load_model('wagtail_review', 'Review')
User = get_user_model()


def create_review(request):
    ReviewForm = get_review_form_class()

    if request.method == 'GET':
        form = ReviewForm(prefix='create_review')
        reviewer_formset = ReviewerFormSet(prefix='create_review_reviewers')
    else:
        form = ReviewForm(request.POST, prefix='create_review')
        reviewer_formset = ReviewerFormSet(request.POST, prefix='create_review_reviewers')

        form_is_valid = form.is_valid()
        reviewer_formset_is_valid = reviewer_formset.is_valid()

        if not (form_is_valid and reviewer_formset_is_valid):
            return render_modal_workflow(
                request, 'wagtail_review/create_review.html', None, {
                    'form': form,
                    'reviewer_formset': reviewer_formset,
                }, json_data={'step': 'form'}
            )
        else:
            return render_modal_workflow(
                request, None, None, {}, json_data={'step': 'done'}
            )

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


class DashboardView(generic.IndexView):
    template_name = 'wagtail_review/admin/dashboard.html'
    page_title = _("Review dashboard")
    context_object_name = 'pages'

    def get_queryset(self):
        return Review.get_pages_with_reviews_for_user(self.request.user).specific()


class AuditTrailView(DetailView):
    template_name = 'wagtail_review/admin/audit_trail.html'
    page_title = _("Audit trail")
    header_icon = 'doc-empty-inverse'
    context_object_name = 'page'

    def get_queryset(self):
        return Review.get_pages_with_reviews_for_user(self.request.user)

    def get_object(self):
        return super().get_object().specific

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = Review.objects.filter(
            page_revision__page=self.object
        ).order_by('created_at').select_related('submitter').prefetch_related('reviewers__responses')
        return context
