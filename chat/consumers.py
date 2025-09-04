import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('text')
        sender_id = data.get('sender_id')

        sender = await User.objects.filter(id=sender_id).afirst()
        sender_name = sender.username if sender else 'Unknown'

        msg_data = {
            'text': message,
            'sender': sender_name,
            'timestamp': str(data.get('timestamp', None))
        }

        # Send to WebSocket group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': msg_data
            }
        )

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))
