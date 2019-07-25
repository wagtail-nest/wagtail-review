from rest_framework import serializers

from .. import models
from ..api.serializers import CommentSerializer


class ExternalReviewerSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ExternalReviewer
        fields = ['email']


class NewShareSerializer(serializers.Serializer):
    email = serializers.EmailField()
    expires_at = serializers.DateTimeField(required=False)

    class Meta:
        fields = ['email', 'expires_at']


class ShareSerializer(serializers.ModelSerializer):
    user = ExternalReviewerSerializer(source='external_user')

    class Meta:
        model = models.Share
        fields = ['id', 'user', 'shared_at', 'first_accessed_at', 'last_accessed_at', 'expires_at']


class CommentSerializerWithFrontendURL(CommentSerializer):
    def get_reviewer(self):
        if 'reviewer' not in self.context:
            reviewer, created = models.Reviewer.objects.get_or_create(internal=self.context['request'].user)
            self.context['reviewer'] = reviewer

        return self.context['reviewer']

    def to_representation(self, comment):
        data = super().to_representation(comment)
        data['frontend_url'] = comment.get_frontend_url(self.get_reviewer())
        return data
