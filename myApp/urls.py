from django.urls import path
from . import views

urlpatterns = [
    path("", views.katalyst_page, name="katalyst_page"),
    path("api/chatbot/", views.chatbot_api, name="chatbot_api"),
    path("api/chatbot/suggestions/", views.chat_suggestions_api, name="chat_suggestions_api"),


    path("avatar-2d", views.avatar_2d, name="avatar_2d"),
    path("avatar-3d", views.avatar_3d, name="avatar_3d"),
    path("api/stt", views.api_stt, name="api_stt"),
    path("api/chat", views.api_chat, name="api_chat"),
    path("api/tts", views.api_tts, name="api_tts"),
]
