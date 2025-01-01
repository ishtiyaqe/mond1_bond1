from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'conflicts', ConflictViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('search-users-friendList/', search_users, name='search_users'),
    path('search-packages/', search_pakage, name='search_pakage'),
    path('search-coupon/<str:type>/<str:coupon>/', search_coupon, name='search_coupon'),
    path('daily_task/', DailyTasksView.as_view(), name='daily_task'),
    path('token_wallet/<int:user_id>/', token_wallets, name='token_wallet'),
    path('friend-request/send/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path('friend-list/', FriendListView.as_view(), name='firend_list'),
    path('friend-requests-list/', FriendRequestsListView.as_view(), name='firend_requests_list'),
    path('notes/', NoteViewSet.as_view(), name='note-list-create'),  
    path('notes/<int:pk>/', NoteViewSet.as_view()),
    path('notifications/', NotificationDetailView.as_view(), name='notification_list'),  
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification_detail'), 
    path('AssintoConflict/<int:pk>/', AssintoConflictView.as_view(), name='AssintoConflict'), 
    path("paypal/initiate/", InitiatePaymentView.as_view(), name="paypal_initiate"),
    path('friend-request/<str:token>/', ConfirmFriendRequestView.as_view(), name='confirm_friend_request'),
]

