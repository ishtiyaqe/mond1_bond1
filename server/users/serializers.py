from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError

UserModel = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserModel
		fields = '__all__'
	def create(self, clean_data):
		user_obj = UserModel.objects.create_user(username=clean_data['username'], email=clean_data['email'], password=clean_data['password'],first_name=clean_data.get('first_name', ''),last_name=clean_data.get('last_name', ''))
		user_obj.username = clean_data['username']
		user_obj.save()
		return user_obj



class UserLoginSerializer(serializers.Serializer):
	email = serializers.EmailField()
	password = serializers.CharField()
	##
	def check_user(self, clean_data):
		user = authenticate(username=clean_data['email'], password=clean_data['password'])
		if not user:
			raise ValidationError('user not found')
		return user
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('id', 'username', 'password', 'email','role','is_premium')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = UserModel.objects.create_user(**validated_data)
        return user

class TokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()

