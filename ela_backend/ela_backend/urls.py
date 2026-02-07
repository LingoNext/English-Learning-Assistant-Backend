# Main URL configuration for the ElA Backend project.
from django.urls import path, include
urlpatterns = [
    path("auth/", include("auth_app.urls"),name="auth_app"),
    path("chat/", include("chat_app.urls"), name="chat_app")
]

