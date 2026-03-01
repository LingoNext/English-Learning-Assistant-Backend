from rest_framework import serializers
from .models import Conversation, Message

# 對話列表序列化器
class ConversationListSerializer(serializers.ModelSerializer):
    """用於 GET /chat/conversations/all/ 端點的簡化序列化器"""
    conversation_id = serializers.IntegerField(source='id', read_only=True)
    count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['conversation_id', 'title', 'count', 'updated_at']

    def get_title(self, obj):
        """取得對話標題"""
        return obj.title

    def get_count(self, obj):
        """取得用戶問題（is_user=True）的數量"""
        return obj.messages.filter(is_user=True).count()
# 對話詳情序列化器
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["text", "is_user"]

# 對話詳情序列化器
class MessageDetailSerializer(serializers.ModelSerializer):
    """用於 POST /chat/conversation/ 端點的簡化序列化器"""
    title = serializers.CharField()
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["title", "messages"]