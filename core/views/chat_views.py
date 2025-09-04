from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..models import Conversation, Message, MessageAttachment, ConversationParticipant
from ..serializers.chat_serializers import (
    ConversationListSerializer,
    MessageCreateSerializer,
    MessageSerializer, 
    ConversationParticipantSerializer,
    MessageAttachmentSerializer,
    ConversationCreateSerializer,
    ConversationDetailSerializer,
    ConversationParticipantSerializer,
    BulkMessageReadSerializer,
    MessageSearchSerializer,
    ChatStatsSerializer,
    OfferMessageSerializer,
    MeetupRequestSerializer,
    
)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    Users can view their conversations, create new ones, and manage participants.
    """
    serializer_class = ConversationListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return conversations where the user is a participant"""
        return Conversation.objects.filter(
            participants=self.request.user
        ).annotate(
            last_message_timestamp=Max('messages__created_at')
        ).order_by('-last_message_timestamp')

    def create(self, request, *args, **kwargs):
        """Create a new conversation with participants"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create conversation
        conversation = serializer.save()
        
        # Add current user as participant
        ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=request.user,
            defaults={'joined_at': timezone.now()}
        )
        
        # Add other participants if specified
        participant_ids = request.data.get('participant_ids', [])
        for user_id in participant_ids:
            try:
                from ..models import StudentUser
                user = StudentUser.objects.get(id=user_id)
                ConversationParticipant.objects.get_or_create(
                    conversation=conversation,
                    user=user,
                    defaults={'joined_at': timezone.now()}
                )
            except StudentUser.DoesNotExist:
                continue
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)    

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get messages for a specific conversation"""
        conversation = self.get_object()
        
        # Check if user is participant
        if not conversation.participants.filter(user=request.user).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
        
        # Pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to a conversation"""
        conversation = self.get_object()
        
        # Check if user is participant
        if not conversation.participants.filter(user=request.user).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create message
        message_data = request.data.copy()
        message_data['conversation'] = conversation.id
        message_data['sender'] = request.user.id
        
        serializer = MessageSerializer(data=message_data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        
        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save()
        
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to the conversation"""
        conversation = self.get_object()
        
        # Check if current user is participant (basic permission check)
        if not conversation.participants.filter(user=request.user).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from ..models import StudentUser
            user = StudentUser.objects.get(id=user_id)
            
            participant, created = ConversationParticipant.objects.get_or_create(
                conversation=conversation,
                user=user,
                defaults={'joined_at': timezone.now()}
            )
            
            if created:
                return Response(
                    {'message': 'Participant added successfully'}, 
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'message': 'User is already a participant'}, 
                    status=status.HTTP_200_OK
                )
                
        except StudentUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def leave_conversation(self, request, pk=None):
        """Leave a conversation"""
        conversation = self.get_object()
        
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=request.user
            )
            participant.left_at = timezone.now()
            participant.save()
            
            return Response({'message': 'Left conversation successfully'})
            
        except ConversationParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this conversation'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages.
    Users can view, create, update, and delete their messages.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
        conversation__participants=self.request.user
    ).order_by('created_at')

    def create(self, request, *args, **kwargs):
        """Create a new message"""
        # Ensure sender is current user
        data = request.data.copy()
        data['sender'] = request.user.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user is participant in the conversation
        conversation_id = data.get('conversation')
        if not Conversation.objects.filter(
            id=conversation_id, 
            participants__user=request.user
        ).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message = serializer.save()
        
        # Update conversation timestamp
        message.conversation.updated_at = timezone.now()
        message.conversation.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a message (only sender can edit)"""
        message = self.get_object()
        
        if message.sender != request.user:
            return Response(
                {'error': 'You can only edit your own messages'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow editing content and message_type
        allowed_fields = ['content', 'message_type']
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = self.get_serializer(message, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete a message (only sender can delete)"""
        message = self.get_object()
        
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read"""
        message = self.get_object()
        
        # Check if user is participant in the conversation
        if not message.conversation.participants.filter(user=request.user).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update read status (you might want to implement a separate ReadReceipt model)
        # For now, we'll use a simple approach
        message.is_read = True
        message.save()
        
        return Response({'message': 'Message marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread messages for the user"""
        # This is a simplified version - in production you'd want a proper read receipt system
        unread_messages = Message.objects.filter(
            conversation__participants__user=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        
        return Response({'unread_count': unread_messages})


class MessageAttachmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing message attachments.
    """
    serializer_class = MessageAttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return attachments from messages in conversations where user is participant"""
        return MessageAttachment.objects.filter(
            message__conversation__participants=self.request.user
        )

    def create(self, request, *args, **kwargs):
        """Create a new attachment"""
        message_id = request.data.get('message')
        
        # Verify user can add attachments to this message
        try:
            message = Message.objects.get(
                id=message_id,
                conversation__participants=request.user
            )
        except Message.DoesNotExist:
            return Response(
                {'error': 'Message not found or you do not have permission'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    # Additional utility views #
class ConversationSearchView(viewsets.ViewSet):
    """
    Search and filter conversations
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Search conversations by participant name or recent messages"""
        query = request.query_params.get('q', '')
        
        # conversations where current user is a participant
        conversations = Conversation.objects.filter(
            participants=request.user
        )
        
        if query:
            conversations = conversations.filter(
                Q(participants__first_name__icontains=query) |
                Q(participants__last_name__icontains=query) |
                Q(messages__content__icontains=query)
            ).distinct()
        
        conversations = conversations.annotate(
            last_message_timestamp=Max('messages__created_at')
        ).order_by('-last_message_timestamp')
        
        serializer = ConversationListSerializer(conversations, many=True, context={'request': request})
        return Response(serializer.data)
