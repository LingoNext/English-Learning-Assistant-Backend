# llm_app/urls.py
from django.urls import path
from .views import VisualView, ChatView,VocabView
urlpatterns = [
    path("analyze/", VisualView.as_view(), name="llm_analyze"),
    path("chat/", ChatView.as_view(), name="llm_chat"),
    path("vocab/", VocabView.as_view(), name="llm_vocab"),
]
