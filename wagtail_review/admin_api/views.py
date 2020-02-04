from django.core.validators import validate_email
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from wagtail.core.models import Page

from .. import models
from ..utils import normalize_email
from . import serializers


class FooAuth(SessionAuthentication):
    # TODO: Make it work with CSRF
    def enforce_csrf(self, request):
        return


class AdminAPIViewMixin:
    authentication_classes = [FooAuth]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class PageShares(AdminAPIViewMixin, generics.ListCreateAPIView):
    serializer_class = serializers.ShareSerializer

    def get_queryset(self):
        page = get_object_or_404(Page, pk=self.kwargs['pk'])
        return models.Share.objects.filter(page=page).order_by('shared_at')

    def create(self, *args, **kwargs):
        page = get_object_or_404(Page, pk=kwargs['pk'])

        serializer = serializers.NewShareSerializer(None, self.request.data)
        serializer.is_valid(raise_exception=True)

        # Look for an external user with the email address
        external_user, created = models.ExternalReviewer.objects.get_or_create(email=serializer.data['email'])

        if models.Share.objects.filter(page=page, external_user=external_user).exists():
            raise ValidationError({'email': "This page has already been shared with this email address"})

        share = models.Share.objects.create(
            page=page,
            external_user=external_user,
            shared_by=self.request.user,
            expires_at=serializer.data.get('expires_at'),
            can_comment=True,
        )

        share.send_share_email()

        serializer = serializers.ShareSerializer(share)

        return Response(serializer.data, status=201)  # FIXME


class PageComments(AdminAPIViewMixin, generics.ListAPIView):
    serializer_class = serializers.CommentSerializerWithFrontendURL

    def get_queryset(self):
        page = get_object_or_404(Page, pk=self.kwargs['pk'])
        return models.Comment.objects.filter(page_revision__page=page).order_by('-created_at')


class UsersListing(AdminAPIViewMixin, generics.ListAPIView):
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        User = self.serializer_class.Meta.model
        users = User.objects.filter(is_active=True)

        terms = self.request.GET.get('search', '').split()
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

            users = users.filter(conditions)

        return users


class GetOrCreateReviewer(AdminAPIViewMixin, generics.CreateAPIView):
    def create(self, *args, **kwargs):
        if 'email' in self.request.data:
            validate_email(self.request.data['email'])

            external_reviewer, created = models.ExternalReviewer.objects.get_or_create(
                email=normalize_email(self.request.data['email'])
            )
            reviewer, created = models.Reviewer.objects.get_or_create(external=external_reviewer)
        elif 'user_id' in self.request.data:
            # TODO: Make sure only users who are active can be chosen
            reviewer, created = models.Reviewer.objects.get_or_create(internal_id=self.request.data['user_id'])
        else:
            raise ValidationError("request must include either an 'email' or a 'user_id'")

        if created:
            status = 201
        else:
            status = 200

        serializer = serializers.ReviewerSerializer(reviewer)
        return Response(serializer.data, status=status)
