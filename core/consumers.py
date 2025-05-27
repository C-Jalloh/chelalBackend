import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'user_{self.user_id}_notifications'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # For now, just echo back
        await self.send(text_data=json.dumps({'message': 'Received'}))

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event['content']))

    @staticmethod
    async def notify_user(user_id, notification):
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        group_name = f'user_{user_id}_notifications'
        await channel_layer.group_send(
            group_name,
            {
                'type': 'send_notification',
                'content': notification
            }
        )
