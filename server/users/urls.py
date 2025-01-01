from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('user/', ProtectedView.as_view(), name='user'),
    path('auth/logout/', UserLogout.as_view(), name='user-logout'),
    path('myaccount/', MyAccountView.as_view(), name='my-account'),
    path('signup/' , UserRegister.as_view() , name="signup"),
    path('login/' , UserLogin.as_view() , name="login"),
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', ObtainTokenView.as_view(), name='token_obtain'),
    path('auth/google/', GoogleLogin.as_view(), name='google-login'),  
]
