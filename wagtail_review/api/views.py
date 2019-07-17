from datetime import timedelta

from rest_framework import generics, status, views
from rest_framework.response import Response
import jwt

from django.conf import settings
from django.db import transaction
from django.db.models import Case, F, Value, When
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from wagtail.core.models import PageRevision

from .. import models
from . import serializers


class ReviewTokenMixin:
    authentication_classes = []

    def process_review_token(self, data):
        self.user = get_object_or_404(models.User, id=data['usid'])
        self.page_revision = get_object_or_404(PageRevision.objects.select_related('page'), id=data['prid'])
        self.perms = self.user.page_perms(self.page_revision.page)
        self.share = self.perms.share

        if self.share is not None:
            self.share.log_access()

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        review_token = self.request.META.get('HTTP_X_REVIEW_TOKEN')
        data = jwt.decode(review_token, settings.SECRET_KEY, algorithms=['HS256'])
        self.process_review_token(data)

        return super().dispatch(*args, **kwargs)


class Home(ReviewTokenMixin, views.APIView):
    authentication_classes = []

    def get(self, request, format=None):
        return Response({
            'you': serializers.UserSerializer(self.user).data,
            'can_comment': self.user.page_perms(self.page_revision.page).can_comment(),
        })


class CommentList(ReviewTokenMixin, generics.ListCreateAPIView):
    serializer_class = serializers.CommentSerializer

    def post(self, *args, **kwargs):
        if self.perms.can_comment():
            return super().post(*args, **kwargs)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def get_queryset(self):
        return models.Comment.objects.filter(page_revision=self.page_revision)

    def perform_create(self, serializer):
        serializer.save(user=self.user, page_revision=self.page_revision)


class Comment(ReviewTokenMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CommentSerializer

    def update(self, *args, **kwargs):
        comment = self.get_object()
        if comment.user != self.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().update(*args, **kwargs)

    def destroy(self, *args, **kwargs):
        comment = self.get_object()
        if comment.user != self.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().destroy(*args, **kwargs)

    def get_queryset(self):
        return models.Comment.objects.filter(page_revision=self.page_revision)


class CommentResolved(ReviewTokenMixin, views.APIView):
    def put(self, *args, **kwargs):
        comment = get_object_or_404(models.Comment.objects.filter(page_revision=self.page_revision), id=kwargs['pk'])
        comment.resolved_at = timezone.now()
        comment.save(update_fields=['resolved_at'])
        return Response()

    def delete(self, *args, **kwargs):
        comment = get_object_or_404(models.Comment.objects.filter(page_revision=self.page_revision), id=kwargs['pk'])
        comment.resolved_at = None
        comment.save(update_fields=['resolved_at'])
        return Response()


class CommentReplyList(ReviewTokenMixin, generics.ListCreateAPIView):
    serializer_class = serializers.CommentReplySerializer

    def post(self, *args, **kwargs):
        if self.perms.can_comment():
            return super().post(*args, **kwargs)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def get_queryset(self):
        return models.CommentReply.objects.filter(comment_id=self.kwargs['pk']).order_by('created_at')

    def perform_create(self, serializer):
        # TODO: Make sure self.kwargs['comment_pk'] is on the current page revision
        serializer.save(user=self.user, comment_id=self.kwargs['pk'])


class CommentReply(ReviewTokenMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CommentReplySerializer

    def update(self, *args, **kwargs):
        reply = self.get_object()
        if reply.user != self.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().update(*args, **kwargs)

    def destroy(self, *args, **kwargs):
        reply = self.get_object()
        if reply.user != self.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().destroy(*args, **kwargs)

    def get_queryset(self):
        return models.CommentReply.objects.filter(comment_id=self.kwargs['comment_pk'])
