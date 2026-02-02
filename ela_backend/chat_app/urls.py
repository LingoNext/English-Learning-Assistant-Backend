# chat_app/urls.py
from django.urls import path
from .views import ConversationAllView, ConversationDetailView, ConversationView, MessageView

urlpatterns = [
    path('conversations/all/', ConversationAllView.as_view(), name='conversation-all'),
    path('conversation/', ConversationDetailView.as_view(), name='conversation-detail'),  # 單數，用於取得特定對話
    path('conversations/', ConversationView.as_view(), name='conversation'),  # 複數，用於建立和刪除對話
    path('messages/', MessageView.as_view(), name='message'),
]
