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
    def get_reviewer(self):
        if 'reviewer' not in self.context:
            reviewer, created = models.Reviewer.objects.get_or_create(user=self.context['request'].user)
            self.context['reviewer'] = reviewer

        return self.context['reviewer']

    def get_frontend_url(self, comment):
        return "FOO"
        #review_token = get_review_token(self.get_reviewer(), comment.page_revision)
        #return comment.page_revision.page.specific.get_url(is_draft=True) + '&review_token=' + review_token.decode('utf-8') + '&comment=' + str(comment.id)

    def to_representation(self, comment):
        data = super().to_representation(comment)
        data['frontend_url'] = self.get_frontend_url(comment)
        return data
