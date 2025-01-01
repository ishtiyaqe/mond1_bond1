from rest_framework import viewsets
from .models import CustomUser
from .serializers import UserSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView

from main.models import *

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)  # Logs the user in and creates a session
            return JsonResponse({'detail': 'Login successful'}, status=status.HTTP_200_OK)
        return JsonResponse({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)



class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

from django.contrib.auth import authenticate
from django.contrib.auth import authenticate, login

from rest_framework.settings import api_settings

from django.contrib.auth import get_user_model, login, logout
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import permission_classes, authentication_classes
from datetime import timedelta
from django.utils.timezone import now
from rest_framework import status, permissions, views
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from .serializers import *
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.decorators import login_required

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get the order and user for the current authenticated user
            order = Order.objects.filter(user=request.user).latest('created_at')  # Get the latest order
            user = CustomUser.objects.get(pk=request.user.pk)

            # Check subscription type and validity
            if order.order_type == 'monthly':
                if order.created_at >= now() - timedelta(days=30):
                    user.is_premium = True
            elif order.order_type == 'yearly':
                if order.created_at >= now() - timedelta(days=365):
                    user.is_premium = True
            else:
                user.is_premium = False

            # Save changes to the user instance
            user.save()

            # Serialize the user data
            serializer = UserSerializer(user)
            return JsonResponse({'user': serializer.data}, status=200)

        except Order.DoesNotExist:
            user = CustomUser.objects.get(pk=request.user.pk)
            user.is_premium = False
            # Save changes to the user instance
            user.save()
            serializer = UserSerializer(user)
            return JsonResponse({'user': serializer.data}, status=200)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User does not exist.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class UserLogout(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)




 
class MyAccountView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(self, request, format=None):
        user = request.user

        # Fetch all search queries associated with the current user
        # search_queries = SearchQuery.objects.filter(user=user)

        # Serialize the search queries
        search_query_data = []
        # for query in search_queries:
        #     search_query_data.append({
        #         'id': query.id,
        #         'query': query.query,
        #         'status': query.status,
        #         # 'product': ProductSerializer(query.product).data if query.product else None,
        #     })

        # Serialize the user data
        user_serializer = UserSerializer(user)

        # Return the serialized data
        return Response({
            'user': user_serializer.data,
            # 'search_queries': search_query_data,
        })

    def delete(self, request, format=None):
        user = request.user
        query_id = request.data.get('query_id')

        if not query_id:
            return Response({"error": "Query ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        # try:
        #     search_query = SearchQuery.objects.get(id=query_id, user=user)
        #     search_query.delete()
        #     return Response({"message": "Search query deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        # except SearchQuery.DoesNotExist:
        #     return Response({"error": "Search query not found"}, status=status.HTTP_404_NOT_FOUND)
        
  
    
  


from .validations import *

class UserRegister(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        clean_data = custom_validation(request.data)
        serializer = UserRegisterSerializer(data=clean_data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.create(clean_data)

   
            if user:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(status=status.HTTP_400_BAD_REQUEST)
    

class UserLogin(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = (SessionAuthentication,)

    def post(self, request):
        data = request.data
        username = data.get('username')
        password = data.get('password')
        serializer = UserLoginSerializer(data=data)

        if not username or not password:
            return Response({'error': 'Invalid input data'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request=request, username=username, password=password)

        if user is not None:
            login(request, user)
            print(request.user)
            return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
        else:
            error_message = 'User not found or incorrect password'
            return Response({'error': error_message}, status=status.HTTP_401_UNAUTHORIZED)
        


from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, TokenSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

class ObtainTokenView(generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        user = User.objects.filter(email=email).first()

        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            serializer = TokenSerializer(data={
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })
            serializer.is_valid()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)



from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.models import SocialAccount
from rest_framework.authtoken.models import Token

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

    def post(self, request, *args, **kwargs):
        # Perform Google login
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            # Google login successful, retrieve the user data
            token_key = response.data.get('key')
            if token_key:
                try:
                    # Query the SocialToken model to find the user associated with the provided key
                    social_token = Token.objects.get(key=token_key)
                    user = social_token.user

                    # Authenticate and log in the user
                    if user:
                        user = authenticate(request=request, username=user.username)
                        login(request, user)
                        return Response({'message': 'Login successful','key':token_key}, status=status.HTTP_200_OK)
                    else:
                        error_message = 'User not found'
                        return Response({'error': error_message}, status=status.HTTP_404_NOT_FOUND)
                except Token.DoesNotExist:
                    error_message = 'Social token does not exist'
                    return Response({'error': error_message}, status=status.HTTP_404_NOT_FOUND)
        return response


