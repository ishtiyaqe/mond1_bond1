import json
import jwt
import random
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from .models import *
from asgiref.sync import sync_to_async
from django.db.models import Q





PIN_TIMEOUT = 1 * 60  # 1 minutes in seconds



class UserStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs'].get('room_id', None)
        self.user = None
        self.pin = None

        try:
            query_string = self.scope.get('query_string').decode()
            token = query_string.split('=')[1]

            self.user = await self.authenticate_user(token)

            if self.user:
                self.pin = self.generate_pin()
                print(f"Sent pin to user: {self.pin}")
                await self.accept()

                await self.send(json.dumps({'pin': self.pin}))

                if self.room_id:
                    await self.channel_layer.group_add(self.room_id, self.channel_name)

                # Start the keep-alive ping mechanism
                asyncio.create_task(self.keep_alive())

            else:
                await self.close(code=4001)
        except Exception as e:
            print(f"Connection failed: {e}")
            await self.close(code=4001)

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected: {close_code}")
        if self.room_id:
            await self.channel_layer.group_discard(self.room_id, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            self.pin_sent_time = timezone.now()
            # Handle incoming ping (pong will be sent back)
            if data.get('type') == 'ping':
                await self.send(json.dumps({'type': 'pong'}))
                await self.set_user_online(self.user)
                await self.set_friend_online(self.user)
                await self.send(json.dumps({'status': 'online'}))
                friend_details = await self.get_friend_details(self.user)
                await self.send(json.dumps({'type': 'friend_details', 'friends': friend_details}))
                conflict_details = await self.conflict_details(self.user)
                await self.send(json.dumps({'type': 'conflict_list', 'conflicts': conflict_details}))
                return
            
        

            received_pin = data.get('pin')
            if str(received_pin) == str(self.pin):
                print(f"User {self.user.email} verified successfully.")
                await self.set_user_online(self.user)
                await self.set_friend_online(self.user)
                await self.send(json.dumps({'status': 'online'}))
                friend_details = await self.get_friend_details(self.user)
                await self.send(json.dumps({'type': 'friend_details', 'friends': friend_details}))
                conflict_details = await self.conflict_details(self.user)
                await self.send(json.dumps({'type': 'conflict_list', 'conflicts': conflict_details}))
            else:
                print(f"Incorrect PIN from user {self.user.email}")
                await self.send(json.dumps({'status': 'incorrect_pin'}))
                friend_details = await self.get_friend_details(self.user)
                await self.send(json.dumps({'type': 'friend_details', 'friends': friend_details}))
                conflict_details = await self.conflict_details(self.user)
                await self.send(json.dumps({'type': 'conflict_list', 'conflicts': conflict_details}))

            # If PIN is not received within the timeout, set user to offline
            await self.wait_for_pin_or_timeout()
        except Exception as e:
            await self.send(json.dumps({'error': str(e)}))

    async def wait_for_pin_or_timeout(self):
        # Wait for PIN verification or timeout
        while True:
            time_elapsed = (timezone.now() - self.pin_sent_time).total_seconds()
            
            if time_elapsed > PIN_TIMEOUT:
                # Timeout reached, set user and friend to offline
                print(f"User {self.user.email} has not verified PIN in time, setting to offline.")
                await self.set_user_offline(self.user)
                await self.set_friend_offline(self.user)

                # Send offline status to user
                await self.send(json.dumps({'status': 'offline'}))
                break

            await asyncio.sleep(1)  # Check every second for timeout

    @sync_to_async
    def set_user_online(self, user):
        friends = FriendsList.objects.filter(user=user)
        for friendship in friends:
            friendship.user_online = True  # Set the current user online
            friendship.save()

    @sync_to_async
    def set_friend_online(self, user):
        friends = FriendsList.objects.filter(friend=user)
        for friendship in friends:
            friendship.friend_online = True  # Set the friend online
            friendship.save()

    @sync_to_async
    def set_user_offline(self, user):
        friends = FriendsList.objects.filter(user=user)
        for friendship in friends:
            friendship.user_online = False  # Set the current user offline
            friendship.save()

    @sync_to_async
    def set_friend_offline(self, user):
        friends = FriendsList.objects.filter(friend=user)
        for friendship in friends:
            friendship.friend_online = False  # Set the friend offline
            friendship.save()
   
    async def conflict_details(self, user):
        # Call a synchronous function to get friend details
        conflict_details = await sync_to_async(self.fetch_conflict_details)(user)
        return conflict_details
    
    async def get_friend_details(self, user):
        # Call a synchronous function to get friend details
        friend_details = await sync_to_async(self.fetch_friend_details)(user)
        return friend_details

    async def keep_alive(self):
        while True:
            try:
                # Send a "ping" message to the client every 30 seconds
                await self.send(json.dumps({'type': 'ping'}))
                await asyncio.sleep(30)  # Send ping every 30 seconds
            except asyncio.CancelledError:
                break  # If the connection is closed, stop sending ping messages

    @database_sync_to_async
    def authenticate_user(self, token):
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token.get('user_id')

            if not user_id:
                raise AuthenticationFailed('Invalid token: user_id missing')

            User = get_user_model()
            return User.objects.get(id=user_id)
        except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist, AuthenticationFailed):
            return None
    
    def fetch_conflict_details(self, user):
        conflicts = Conflict.objects.filter(
            Q(user=user) | Q(assign_to=user)
        )
        conflict_details = []  # List to store friend details
  
        for con in conflicts:
            conflict_details.append({
                'id': con.id,
                'user': con.user.username if con.user else None,
                'title': con.title,
                'assign_to': con.assign_to.username if con.assign_to else None,
                'description': con.description,
                'assign_description': con.assign_description if con.assign_description else None,
                'impact': con.impact if con.impact else None,
                'responsibility': con.responsibility if con.responsibility else None,
                'factors': con.factors if con.factors else None,
                'nextSteps': con.nextSteps if con.nextSteps else None,
                'contextualOverview': con.contextualOverview if con.contextualOverview else None,
                'primaryIssues': con.primaryIssues if con.primaryIssues else None,
                'perspectives': con.perspectives if con.perspectives else None,
                'accountability': con.accountability if con.accountability else None,
                'improvements': con.improvements if con.improvements else None,
                'actionPlan': con.actionPlan if con.actionPlan else None,
                'resources': con.resources if con.resources else None,
                'premium_tools': con.premium_tools if con.premium_tools else None,
                'status': con.status,
                'updated_at': con.updated_at.isoformat() if con.updated_at else None  # Convert to ISO string
            })

        
        return conflict_details

    
    def fetch_friend_details(self, user):
        friends_user = SingleFriendList.objects.filter(
            Q(friend1=user) | Q(friend2=user),
        )

      

        friend_details = []  # List to store friend details
 
        for friend_request in friends_user:
            # Retrieve the last conflict for each friend
            last_conflict = Conflict.objects.filter(user=friend_request.friend1).order_by('-updated_at').first()
            last_conflict1 = Conflict.objects.filter(user=friend_request.friend2).order_by('-updated_at').first()
       
            friend_details.append({
                'id': friend_request.friend1.id,
                'username': friend_request.friend1.username,
                'name': friend_request.friend1.first_name + ' ' + friend_request.friend1.last_name,
                'last_conflict': last_conflict.title if last_conflict else None,
                'last_conflict_date': last_conflict.updated_at.isoformat() if last_conflict else None
            })
            friend_details.append({
                'id': friend_request.friend2.id,
                'username': friend_request.friend2.username,
                'name': friend_request.friend2.first_name + ' ' + friend_request.friend2.last_name,
                'last_conflict': last_conflict1.title if last_conflict1 else None,
                'last_conflict_date': last_conflict1.updated_at.isoformat() if last_conflict1 else None
            })
        filtered_data = [item for item in friend_details if item['username'] != user.username]
        print(f'Friend list: {filtered_data}')
        
        return filtered_data

    
    def generate_pin(self):
        return random.randint(1000, 9999)


