# chat_app/urls.py
from django.urls import path
from .views import ConversationAllView, ConversationView, MessageView

urlpatterns = [
    path('conversations/all/', ConversationAllView.as_view(), name='conversation-all'),
    path('conversations/', ConversationView.as_view(), name='conversation'),
    path('messages/', MessageView.as_view(), name='message'),
]
