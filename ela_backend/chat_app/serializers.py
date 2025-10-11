from rest_framework import serializers
from .models import Conversation, Message, Analysis

class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = ['grammar_errors', 'vocab_difficulty', 'misc', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    analysis = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "conversation", "user", "role", "content", "metadata", "created_at", "analysis"]

    def get_analysis(self, obj):
        try:
            analysis = obj.analysis
            return AnalysisSerializer(analysis).data
        except Analysis.DoesNotExist:
            return {
                "grammar_errors": [],
                "vocab_difficulty": [],
                "misc": {
                    "confidence": 0,
                    "processing_time": 0
                }
            }

class ConversationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True) 

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'created_at', 'updated_at', 'is_active']

    def get_last_message_preview(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return last_msg.content[:50] + ('...' if len(last_msg.content) > 50 else '')
        return ''
