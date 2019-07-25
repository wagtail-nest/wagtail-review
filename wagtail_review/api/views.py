from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, views
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .. import models
from ..token import Token
from . import serializers


class ReviewTokenMixin:
    authentication_classes = []

    def process_review_token(self, token):
        try:
            self.reviewer = token.reviewer
            self.page_revision = token.page_revision
        except (models.Reviewer.DoesNotExist, models.PageRevision.DoesNotExist):
            raise Http404

        self.perms = self.reviewer.page_perms(self.page_revision.page)
        self.share = self.perms.share

        if self.share is not None:
            self.share.log_access()

        if token.review_request_id:
            try:
                self.review_request = token.review_request
            except models.ReviewRequest.DoesNotExist:
                raise Http404

            if self.review_request.is_closed:
                self.review_request = None
        else:
            self.review_request = None

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        if self.request.method != 'OPTIONS':
            token = Token.decode(self.request.META.get('HTTP_X_REVIEW_TOKEN'))
            self.process_review_token(token)

        return super().dispatch(*args, **kwargs)


class Home(ReviewTokenMixin, views.APIView):
    authentication_classes = []

    def get(self, request, format=None):
        return Response({
            'you': serializers.ReviewerSerializer(self.reviewer).data,
            'can_comment': self.reviewer.page_perms(self.page_revision.page).can_comment(),
            'can_review': self.review_request is not None,
        })


class CommentList(ReviewTokenMixin, generics.ListCreateAPIView):
    serializer_class = serializers.CommentSerializer

    def post(self, *args, **kwargs):
        if not self.perms.can_comment():
            raise PermissionDenied()

        return super().post(*args, **kwargs)

    def get_queryset(self):
        return models.Comment.objects.filter(page_revision=self.page_revision)

    def perform_create(self, serializer):
        serializer.save(reviewer=self.reviewer, page_revision=self.page_revision)


class Comment(ReviewTokenMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CommentSerializer

    def update(self, *args, **kwargs):
        comment = self.get_object()
        if comment.reviewer != self.reviewer:
            raise PermissionDenied()

        return super().update(*args, **kwargs)

    def destroy(self, *args, **kwargs):
        comment = self.get_object()
        if comment.reviewer != self.reviewer:
            raise PermissionDenied()

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
        if not self.perms.can_comment():
            raise PermissionDenied()

        return super().post(*args, **kwargs)

    def get_queryset(self):
        return models.CommentReply.objects.filter(comment_id=self.kwargs['pk']).order_by('created_at')

    def perform_create(self, serializer):
        # TODO: Make sure self.kwargs['comment_pk'] is on the current page revision
        serializer.save(reviewer=self.reviewer, comment_id=self.kwargs['pk'])


class CommentReply(ReviewTokenMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CommentReplySerializer

    def update(self, *args, **kwargs):
        reply = self.get_object()
        if reply.reviewer != self.reviewer:
            raise PermissionDenied()

        return super().update(*args, **kwargs)

    def destroy(self, *args, **kwargs):
        reply = self.get_object()
        if reply.reviewer != self.reviewer:
            raise PermissionDenied()

        return super().destroy(*args, **kwargs)

    def get_queryset(self):
        return models.CommentReply.objects.filter(comment_id=self.kwargs['comment_pk'])


class Respond(ReviewTokenMixin, generics.CreateAPIView):
    queryset = models.ReviewResponse.objects.all()
    serializer_class = serializers.NewReviewResponseSerializer

    def post(self, *args, **kwargs):
        if self.review_request is None or self.review_request.is_closed:
            raise PermissionDenied()

        return super().post(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.reviewer, request=self.review_request)
