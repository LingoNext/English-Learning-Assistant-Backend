# chat_app/models.py
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Conversation {self.id} by {self.user}"


class Message(models.Model):
    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField(help_text="用戶訊息內容")
    ai_response = models.TextField(blank=True, null=True, help_text="AI 回覆內容")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='generating',
        help_text="訊息處理狀態"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Message {self.id} in Conversation {self.conversation.id}"


class Analysis(models.Model):
    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name='analysis'
    )
    grammar_errors = models.JSONField(default=list, blank=True)
    vocab_difficulty = models.JSONField(default=list, blank=True)
    misc = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for Message {self.message.id}"
