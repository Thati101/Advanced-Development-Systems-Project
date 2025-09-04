from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, permissions
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer

User = get_user_model()

# List all chats for logged-in user
class ChatListView(generics.ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(participants=self.request.user).order_by('-created_at')

# Start a new chat or get existing chat between two users
class StartChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        other_user_id = request.data.get('user_id')
        other_user = get_object_or_404(User, id=other_user_id)

        # Check if chat already exists between users
        chat = Chat.objects.filter(participants=request.user).filter(participants=other_user).first()
        if not chat:
            chat = Chat.objects.create()
            chat.participants.add(request.user, other_user)

        serializer = ChatSerializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# List messages for a chat
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        chat = get_object_or_404(Chat, id=chat_id, participants=self.request.user)
        return chat.messages.order_by('timestamp')

# Send a message in a chat
class SendMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
        text = request.data.get('text', '')
        if not text.strip():
            return Response({"error": "Message cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(chat=chat, sender=request.user, text=text)
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

