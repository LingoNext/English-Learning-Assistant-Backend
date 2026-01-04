from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "conversation", "text", "is_user", "timestamp"]
        read_only_fields = ["id", "timestamp"]


class ConversationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True) 
    messages = MessageSerializer(many=True, read_only=True)
    first_user_question = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'created_at', 'updated_at', 'messages', 'first_user_question']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_first_user_question(self, obj):
        """取得用戶的第一個問題"""
        first_message = obj.messages.filter(is_user=True).first()
        return first_message.text if first_message else ""
