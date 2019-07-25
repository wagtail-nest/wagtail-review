from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from wagtail.core.models import Page

from .. import models
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
