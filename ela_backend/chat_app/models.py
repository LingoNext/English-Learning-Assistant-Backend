# chat_app/models.py
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    # user_id 參考 Django 內建的 User 模型
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_conversations'
    )
    # 對話標題
    title = models.CharField(max_length=50, blank=True, help_text="對話標題")
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True)
    # 最後更新時間
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} by {self.user}"

    class Meta:
        ordering = ['-updated_at']


class Message(models.Model):
    # conversation_id 參考 Conversation 模型
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    # 訊息內容
    text = models.TextField(max_length=500,help_text="訊息內容")
    # 是否為用戶訊息
    is_user = models.BooleanField(default=True, help_text="是否為用戶訊息")

    # 時間戳記
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id} in Conversation {self.conversation.id}"

    class Meta:
        ordering = ['timestamp']

