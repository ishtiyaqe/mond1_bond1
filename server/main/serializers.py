from rest_framework import serializers
from .models import *


class TokenWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = tokenWallet
        fields = '__all__'  # We will allow the user and token fields to be exposed

class FriendListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendsList
        fields = '__all__'



class PackagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Packages
        fields ='__all__'


class DailyTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyTask
        fields ='__all__'

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ['name', 'role', 'avatar', 'last_conflict']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']  # Adjust fields as necessary

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message',  'read', 'created_at']

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'user', 'title', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ConflictSerializer(serializers.ModelSerializer):
    parties = PartySerializer(many=True, required=False)

    class Meta:
        model = Conflict
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Extract parties data and remove it from validated_data
        parties_data = validated_data.pop('parties', [])
        # Create the conflict object
        conflict = Conflict.objects.create(**validated_data)

        # Send notification if 'assin_to' exists
        assin_to_user = validated_data.get('assin_to')
        if assin_to_user:
            Notification.objects.create(
                user=assin_to_user,
                title=f"New Conflict Created By {self.context['request'].user.first_name} {self.context['request'].user.last_name}",
                message=f'New Conflict created with title: {validated_data["title"]}'
            )

        # Create the related Party objects
        for party_data in parties_data:
            Party.objects.create(conflict=conflict, **party_data)

        return conflict
