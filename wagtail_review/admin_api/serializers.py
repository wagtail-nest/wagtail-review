from django.contrib.auth import get_user_model
from rest_framework import serializers

from .. import models
from ..api.serializers import CommentSerializer


class UsernameField(serializers.ReadOnlyField):
    def to_representation(self, user):
        if hasattr(user, 'get_full_name'):
            full_name = user.get_full_name()
            if full_name:
                return full_name

        return user.get_username()


class UserSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='pk')
    name = UsernameField(source="*")

    class Meta:
        model = get_user_model()
        fields = ['id', 'name']


class ExternalReviewerSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ExternalReviewer
        fields = ['email']


class ReviewerSerializer(serializers.ModelSerializer):
    internal = UserSerializer()
    external = ExternalReviewerSerializer()

    class Meta:
        model = models.Reviewer
        fields = ['id', 'internal', 'external']


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
