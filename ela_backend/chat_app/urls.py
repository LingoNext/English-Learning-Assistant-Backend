# chat_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, MessageListView, ChatMessageCreateView

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
    path('conversations/<int:pk>/messages/', MessageListView.as_view(), name='conversation-messages'),
    path('conversations/<int:pk>/chat/', ChatMessageCreateView.as_view(), name='conversation-chat'),
]
