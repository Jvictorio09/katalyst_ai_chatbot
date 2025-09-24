from django.urls import path
from . import views

urlpatterns = [
    path("", views.katalyst_page, name="katalyst_page"),
    path("api/chatbot/", views.chatbot_api, name="chatbot_api"),
    path("api/chatbot/suggestions/", views.chat_suggestions_api, name="chat_suggestions_api"),
]
