from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic.detail import DetailView

import swapper

from wagtail import VERSION as WAGTAIL_VERSION
from wagtail.admin import messages
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.views import generic

from wagtail_review.forms import get_review_form_class, ReviewerFormSet
from wagtail_review.models import Reviewer
from wagtail_review.text import user_display_name


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
            'full_name': user_display_name(user),
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
        return Review.get_pages_with_reviews_for_user(self.request.user)


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
        context['page_permissions'] = self.object.permissions_for_user(self.request.user)

        return context


def view_review_page(request, review_id=None):
    review = get_object_or_404(Review, id=review_id)

    # find a reviewer record corresponding to the current user
    # (the submitter of the review should always have one)
    try:
        reviewer = review.reviewers.get(user=request.user)
    except Reviewer.DoesNotExist:
        # current user is not participating in the review;
        # if they have edit access to the page, give them the submitter's
        # read-only credentials so that they can see annotations

        page = review.page_revision.as_page_object()
        perms = page.permissions_for_user(request.user)

        if not (perms.can_edit() or perms.can_publish()):
            raise PermissionDenied

        try:
            reviewer = review.reviewers.get(user=review.submitter)
        except Reviewer.DoesNotExist:
            raise PermissionDenied

    page = review.page_revision.as_page_object()
    if reviewer.user == request.user:
        review_mode = 'comment'
    else:
        review_mode = 'view'

    if WAGTAIL_VERSION < (2, 7):
        dummy_request = page.dummy_request(request)
        dummy_request.wagtailreview_reviewer = reviewer
        dummy_request.wagtailreview_mode = review_mode
        return page.serve_preview(dummy_request, page.default_preview_mode)
    else:
        return page.make_preview_request(
            original_request=request,
            extra_request_attrs={
                'wagtailreview_reviewer': reviewer,
                'wagtailreview_mode': review_mode,
            }
        )


@require_POST
def close_review(request, review_id=None):
    review = get_object_or_404(Review, id=review_id)
    page = review.page_revision.as_page_object()
    perms = page.permissions_for_user(request.user)

    if not (perms.can_edit() or perms.can_publish()):
        raise PermissionDenied

    review.status = 'closed'
    review.save()

    messages.success(request, _("The review has been closed."))

    return redirect('wagtail_review_admin:audit_trail', page.id)


@require_POST
def close_and_publish(request, review_id=None):
    review = get_object_or_404(Review, id=review_id)
    page = review.page_revision.as_page_object()
    perms = page.permissions_for_user(request.user)
    if not perms.can_publish():
        raise PermissionDenied

    review.status = 'closed'
    review.save()
    review.page_revision.publish()

    messages.success(request, _("The review has been closed and the page published."))

    return redirect('wagtail_review_admin:audit_trail', page.id)


@require_POST
def reopen_review(request, review_id=None):
    review = get_object_or_404(Review, id=review_id)
    page = review.page_revision.as_page_object()
    perms = page.permissions_for_user(request.user)

    if not (perms.can_edit() or perms.can_publish()):
        raise PermissionDenied

    review.status = 'open'
    review.save()

    messages.success(request, _("The review has been reopened."))

    return redirect('wagtail_review_admin:audit_trail', page.id)
