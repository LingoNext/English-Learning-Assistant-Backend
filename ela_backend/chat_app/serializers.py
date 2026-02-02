from rest_framework import serializers
from .models import Conversation, Message

class ConversationListSerializer(serializers.ModelSerializer):
    """用於 /chat/conversations/all/ 端點的簡化序列化器"""
    conversation_id = serializers.IntegerField(source='id', read_only=True)
    first_user_question = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['conversation_id', 'first_user_question', 'count', 'updated_at']

    def get_first_user_question(self, obj):
        """取得用戶的第一個問題（前40個字元）"""
        first_message = obj.messages.filter(is_user=True).first()
        if first_message and first_message.text:
            return first_message.text[:40]
        return ""

    def get_count(self, obj):
        """取得用戶問題（is_user=True）的數量"""
        return obj.messages.filter(is_user=True).count()


class MessageListSerializer(serializers.ModelSerializer):
    """用於取得特定對話訊息的簡化序列化器"""
    class Meta:
        model = Message
        fields = ["text", "is_user"]
