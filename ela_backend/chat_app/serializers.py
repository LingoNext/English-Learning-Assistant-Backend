from rest_framework import serializers
from .models import Conversation, Message, Analysis

class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = ['grammar_errors', 'vocab_difficulty', 'misc', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "conversation", "content", "ai_response", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ConversationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True) 
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'created_at', 'updated_at', 'is_active', 'messages']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
