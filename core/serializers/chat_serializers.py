from rest_framework import serializers
from django.db import transaction
from ..models import Conversation, Message, MessageAttachment, ConversationParticipant
from .user_serializers import StudentUserListSerializer
from .product_serializers import ProductListSerializer


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for conversation list view"""
    participants_info = StudentUserListSerializer(source='participants', many=True, read_only=True)
    related_product_info = ProductListSerializer(source='related_product', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'participants_info', 'related_product_info',
            'is_active', 'created_at', 'updated_at', 'last_message_at',
            'last_message', 'unread_count', 'other_participant'
        ]

    def get_last_message(self, obj):
        """Get the last message in conversation"""
        last_msg = obj.get_last_message()
        if last_msg:
            return {
                'id': last_msg.id,
                'content': last_msg.content[:100] + '...' if len(last_msg.content) > 100 else last_msg.content,
                'message_type': last_msg.message_type,
                'sender': last_msg.sender.username,
                'created_at': last_msg.created_at,
                'is_read': last_msg.is_read
            }
        return None

    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count_for_user(request.user)
        return 0

    def get_other_participant(self, obj):
        """Get the other participant in conversation (for 1-on-1 chats)"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            other = obj.get_other_participant(request.user)
            if other:
                return StudentUserListSerializer(other, context=self.context).data
        return None


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages"""
    sender_info = StudentUserListSerializer(source='sender', read_only=True)
    attachments = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    is_own_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'sender_info',
            'message_type', 'content', 'image', 'image_url',
            'metadata', 'is_read', 'is_edited', 'is_deleted',
            'created_at', 'updated_at', 'read_at', 'attachments',
            'is_own_message'
        ]
        read_only_fields = [
            'id', 'sender', 'sender_info', 'created_at', 'updated_at',
            'is_own_message'
        ]

    def get_attachments(self, obj):
        """Get message attachments"""
        return MessageAttachmentSerializer(
            obj.attachments.all(),
            many=True,
            context=self.context
        ).data

    def get_image_url(self, obj):
        """Get full URL for message image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_is_own_message(self, obj):
        """Check if message belongs to current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender == request.user
        return False


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""
    
    class Meta:
        model = Message
        fields = [
            'conversation', 'message_type', 'content',
            'image', 'metadata'
        ]

    def validate_content(self, value):
        """Validate message content"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value.strip()

    def validate(self, attrs):
        """Validate message creation"""
        conversation = attrs.get('conversation')
        request = self.context.get('request')
        
        if request and request.user.is_authenticated:
            # Check if user is participant in conversation
            if not conversation.participants.filter(id=request.user.id).exists():
                raise serializers.ValidationError({
                    'conversation': 'You are not a participant in this conversation'
                })
            
            # Check if conversation is active
            if not conversation.is_active:
                raise serializers.ValidationError({
                    'conversation': 'This conversation is no longer active'
                })
        
        return attrs

    def create(self, validated_data):
        """Create message with sender"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['sender'] = request.user
        return super().create(validated_data)


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for message attachments"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'file', 'file_url', 'file_name',
            'file_size', 'file_type', 'created_at'
        ]

    def get_file_url(self, obj):
        """Get full URL for attachment"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating conversations"""
    initial_message = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Optional initial message"
    )
    
    class Meta:
        model = Conversation
        fields = [
            'related_product', 'title', 'initial_message'
        ]

    def validate_related_product(self, value):
        """Validate product access"""
        if value and value.status != 'active':
            raise serializers.ValidationError(
                "Cannot create conversation for inactive product"
            )
        return value

    def create(self, validated_data):
        """Create conversation with participants"""
        initial_message = validated_data.pop('initial_message', None)
        request = self.context.get('request')
        
        if not (request and request.user.is_authenticated):
            raise serializers.ValidationError("Authentication required")
        
        current_user = request.user
        related_product = validated_data.get('related_product')
        
        # If there's a related product, add the product owner as participant
        if related_product:
            if related_product.seller == current_user:
                raise serializers.ValidationError({
                    'related_product': 'You cannot create a conversation about your own product'
                })
            
            # Check if conversation already exists
            existing_conversation = Conversation.objects.filter(
                participants=current_user,
                related_product=related_product
            ).filter(participants=related_product.seller).first()
            
            if existing_conversation:
                return existing_conversation
        
        with transaction.atomic():
            # Create conversation
            conversation = Conversation.objects.create(**validated_data)
            
            # Add current user as participant
            conversation.participants.add(current_user)
            
            # Add product seller as participant if applicable
            if related_product:
                conversation.participants.add(related_product.seller)
            
            # Create participant settings
            for participant in conversation.participants.all():
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user=participant
                )
            
            # Create initial message if provided
            if initial_message:
                Message.objects.create(
                    conversation=conversation,
                    sender=current_user,
                    content=initial_message,
                    message_type='product_inquiry' if related_product else 'text'
                )
        
        return conversation


class ConversationParticipantSerializer(serializers.ModelSerializer):
    """Serializer for conversation participant settings"""
    user_info = StudentUserListSerializer(source='user', read_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = [
            'id', 'conversation', 'user', 'user_info',
            'is_muted', 'is_archived', 'is_blocked',
            'last_read_at', 'joined_at'
        ]
        read_only_fields = ['id', 'conversation', 'user', 'joined_at']


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Detailed conversation serializer with messages"""
    participants_info = StudentUserListSerializer(source='participants', many=True, read_only=True)
    related_product_info = ProductListSerializer(source='related_product', read_only=True)
    messages = serializers.SerializerMethodField()
    participant_settings = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'participants_info', 'related_product_info',
            'is_active', 'created_at', 'updated_at', 'last_message_at',
            'messages', 'participant_settings', 'unread_count'
        ]

    def get_messages(self, obj):
        """Get conversation messages (limited for performance)"""
        # Get latest 50 messages by default
        messages = obj.messages.filter(
            is_deleted=False
        ).order_by('-created_at')[:50]
        
        return MessageSerializer(
            reversed(list(messages)),  # Reverse to show oldest first
            many=True,
            context=self.context
        ).data

    def get_participant_settings(self, obj):
        """Get current user's participant settings"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                settings = obj.participant_settings.get(user=request.user)
                return ConversationParticipantSerializer(settings, context=self.context).data
            except ConversationParticipant.DoesNotExist:
                pass
        return None

    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count_for_user(request.user)
        return 0


class BulkMessageReadSerializer(serializers.Serializer):
    """Serializer for marking multiple messages as read"""
    message_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of message IDs to mark as read"
    )

    def validate_message_ids(self, value):
        """Validate message IDs"""
        if not value:
            raise serializers.ValidationError("At least one message ID is required")
        return value


class MessageSearchSerializer(serializers.Serializer):
    """Serializer for message search parameters"""
    q = serializers.CharField(required=False, help_text="Search query")
    message_type = serializers.ChoiceField(
        choices=Message.MESSAGE_TYPES,
        required=False,
        help_text="Filter by message type"
    )
    sender = serializers.IntegerField(required=False, help_text="Sender user ID")
    date_from = serializers.DateTimeField(required=False, help_text="Messages from this date")
    date_to = serializers.DateTimeField(required=False, help_text="Messages until this date")
    has_image = serializers.BooleanField(required=False, help_text="Messages with images only")
    is_read = serializers.BooleanField(required=False, help_text="Filter by read status")


class ChatStatsSerializer(serializers.Serializer):
    """Serializer for chat statistics"""
    total_conversations = serializers.IntegerField()
    active_conversations = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    unread_messages = serializers.IntegerField()
    messages_sent = serializers.IntegerField()
    messages_received = serializers.IntegerField()


class OfferMessageSerializer(serializers.Serializer):
    """Serializer for price offer messages"""
    conversation_id = serializers.IntegerField()
    offer_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    message = serializers.CharField(max_length=500, required=False)
    
    def validate_offer_amount(self, value):
        """Validate offer amount"""
        if value <= 0:
            raise serializers.ValidationError("Offer amount must be greater than 0")
        return value

    def create(self, validated_data):
        """Create offer message"""
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            raise serializers.ValidationError("Authentication required")
        
        conversation_id = validated_data['conversation_id']
        offer_amount = validated_data['offer_amount']
        message_text = validated_data.get('message', f"I'd like to offer R{offer_amount} for this item.")
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            raise serializers.ValidationError("Conversation not found")
        
        # Check if user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            raise serializers.ValidationError("You are not a participant in this conversation")
        
        # Create offer message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_text,
            message_type='price_offer',
            metadata={'offer_amount': float(offer_amount)}
        )
        
        return MessageSerializer(message, context=self.context).data


class MeetupRequestSerializer(serializers.Serializer):
    """Serializer for meetup request messages"""
    conversation_id = serializers.IntegerField()
    location = serializers.CharField(max_length=200)
    suggested_time = serializers.DateTimeField()
    message = serializers.CharField(max_length=500, required=False)
    
    def create(self, validated_data):
        """Create meetup request message"""
        request = self.context.get('request')
        if not (request and request.user.is_authenticated):
            raise serializers.ValidationError("Authentication required")
        
        conversation_id = validated_data['conversation_id']
        location = validated_data['location']
        suggested_time = validated_data['suggested_time']
        message_text = validated_data.get('message', f"Let's meet at {location}")
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            raise serializers.ValidationError("Conversation not found")
        
        # Check if user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            raise serializers.ValidationError("You are not a participant in this conversation")
        
        # Create meetup message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_text,
            message_type='meeting_request',
            metadata={
                'location': location,
                'suggested_time': suggested_time.isoformat()
            }
        )
        
        return MessageSerializer(message, context=self.context).data