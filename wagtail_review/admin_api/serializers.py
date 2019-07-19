from rest_framework import serializers

from ..api.serializers import CommentSerializer

from .. import models


class ExternalUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ExternalUser
        fields = ['email']


class NewShareSerializer(serializers.Serializer):
    email = serializers.EmailField()
    expires_at = serializers.DateTimeField(required=False)

    class Meta:
        fields = ['email', 'expires_at']


class ShareSerializer(serializers.ModelSerializer):
    user = ExternalUserSerializer(source='external_user')

    class Meta:
        model = models.Share
        fields = ['id', 'user', 'shared_by', 'shared_at', 'first_accessed_at', 'last_accessed_at', 'expires_at']


class CommentSerializerWithFrontendURL(CommentSerializer):
    def get_user(self):
        if 'wagtailreview_user' not in self.context:
            user, created = models.User.objects.get_or_create(internal=self.context['request'].user)
            self.context['wagtailreview_user'] = user

        return self.context['wagtailreview_user']

    def to_representation(self, comment):
        data = super().to_representation(comment)
        data['frontend_url'] = comment.get_frontend_url(self.get_user())
        return data
