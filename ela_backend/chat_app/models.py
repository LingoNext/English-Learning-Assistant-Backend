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
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_messages'
    )
    role = models.CharField(
        max_length=10,
        choices=(('user','User'), ('ai','AI')),
        default='user'
    )
    content = models.TextField(default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
