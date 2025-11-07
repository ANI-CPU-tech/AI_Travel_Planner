# assistant/serializers.py
from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    user_email = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "model_name",
            "created_at",
            "updated_at",
            "user_email",
            "messages",
        ]


class ChatRequestSerializer(serializers.Serializer):
    """
    Handles validation for chatbot input.
    """
    conversation_id = serializers.IntegerField(required=False)
    message = serializers.CharField()
    model_name = serializers.CharField(required=False)
