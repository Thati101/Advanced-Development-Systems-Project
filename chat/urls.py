from django.urls import path
from .views import ChatListView, StartChatView, MessageListView, SendMessageView

urlpatterns = [
    path('chats/', ChatListView.as_view(), name='chat-list'),
    path('chats/start/', StartChatView.as_view(), name='start-chat'),
    path('chats/<int:chat_id>/messages/', MessageListView.as_view(), name='message-list'),
    path('chats/<int:chat_id>/send/', SendMessageView.as_view(), name='send-message'),
]
