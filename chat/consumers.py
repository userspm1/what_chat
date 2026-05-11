# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, UserProfile

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name       = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.set_online(True)
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'user_status', 'user_id': self.scope['user'].id, 'is_online': True}
        )

    async def disconnect(self, close_code):
        await self.set_online(False)
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'user_status', 'user_id': self.scope['user'].id, 'is_online': False}
        )
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data     = json.loads(text_data)
        user     = self.scope['user']
        msg_type = data.get('type', 'text')

        if msg_type == 'read_receipt':
            await self.mark_messages_read(self.room_name, user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'read_receipt', 'reader_id': user.id}
            )
            return

        # DELETE FOR ME
        if msg_type == 'delete_for_me':
            await self.delete_for_me(data.get('msg_id'), user)
            await self.send(text_data=json.dumps({
                'type':   'delete_for_me',
                'msg_id': data.get('msg_id'),
            }))
            return

        # DELETE FOR EVERYONE
        if msg_type == 'delete_for_everyone':
            success = await self.delete_for_everyone(data.get('msg_id'), user)
            if success:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'delete_for_everyone', 'msg_id': data.get('msg_id')}
                )
            return

        # NORMAL MESSAGE
        message  = data.get('message', '')
        file_url = data.get('file_url', '')
        saved    = await self.save_message(user, self.room_name, message, file_url, msg_type)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type':      'chat_message',
                'message':   message,
                'file_url':  file_url,
                'msg_type':  msg_type,
                'username':  user.username,
                'sender_id': user.id,
                'msg_id':    saved.id,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type':      'chat_message',
            'message':   event['message'],
            'file_url':  event.get('file_url', ''),
            'msg_type':  event.get('msg_type', 'text'),
            'username':  event['username'],
            'sender_id': event['sender_id'],
            'msg_id':    event.get('msg_id'),
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type':      'user_status',
            'user_id':   event['user_id'],
            'is_online': event['is_online'],
        }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type':      'read_receipt',
            'reader_id': event['reader_id'],
        }))

    async def delete_for_me(self, event):
        await self.send(text_data=json.dumps({
            'type':   'delete_for_me',
            'msg_id': event['msg_id'],
        }))

    async def delete_for_everyone(self, event):
        await self.send(text_data=json.dumps({
            'type':   'delete_for_everyone',
            'msg_id': event['msg_id'],
        }))

    @database_sync_to_async
    def save_message(self, user, room_name, content, file_url, msg_type):
        return Message.objects.create(
            room_name=room_name,
            sender=user,
            content=content,
            file_url=file_url,      # ← NOW SAVES FILE URL
            message_type=msg_type,
        )

    @database_sync_to_async
    def set_online(self, status):
        user = self.scope['user']
        UserProfile.objects.update_or_create(user=user, defaults={'is_online': status})

    @database_sync_to_async
    def mark_messages_read(self, room_name, user):
        Message.objects.filter(room_name=room_name, is_read=False).exclude(sender=user).update(is_read=True)

    @database_sync_to_async
    def delete_for_me(self, msg_id, user):
        # We just return the id — client hides it locally
        return msg_id

    @database_sync_to_async
    def delete_for_everyone(self, msg_id, user):
        try:
            msg = Message.objects.get(id=msg_id, sender=user)
            msg.deleted_for_everyone = True
            msg.content  = ''
            msg.file_url = ''
            msg.save()
            return True
        except Message.DoesNotExist:
            return False