# chat_app/urls.py
from django.urls import path
from .views import ConversationAllView, ConversationDetailView, ConversationView, MessageView

urlpatterns = [
    path('conversations/all/', ConversationAllView.as_view(), name='conversation-all'),
    path('conversation/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/', ConversationView.as_view(), name='conversation'),
    path('messages/', MessageView.as_view(), name='message'),
]
