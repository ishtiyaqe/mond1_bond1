from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import *
from .openai import *
from main.serializers import *
from django.http import JsonResponse
from django.db.models import Q, F,Subquery, OuterRef, Value
from django.db.models.functions import Concat 
from django.contrib.auth import get_user_model, authenticate
from rest_framework.decorators import api_view
User = get_user_model()
from rest_framework.permissions import IsAuthenticated
import threading
from django.http import JsonResponse
from .paypal_utils import create_paypal_order
from decimal import Decimal




class InitiatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # Get the amount from the request data
            amount = request.data.get("amount")
            coupon = request.data.get("coupon")
            od_type = request.data.get("order_type")
            if not amount:
                return Response({"error": "Amount is required"}, status=400)
            
            # Create a PayPal order
            payment = create_paypal_order(float(amount))
            approval_url = next(link for link in payment.links if link.rel == "approval_url")

            # Initialize discount variables
            discount_amount = 0
            affiliate_instance = None
            if approval_url:
                order_amounts = amount
                # Check if coupon code is provided and valid
                if coupon:
                    affiliate_instance = affiliate.objects.get(affiliate_code=coupon)
                    order_amounts = amount  # Apply discount
                
                # Create the order
                order = Order.objects.create(
                    user=request.user,
                    promo_code = coupon,
                    order_type = od_type,
                    status = 'completed',
                    total_amount=order_amounts,
                    payment_id=payment.id  # Store the PayPal payment ID in the order
                )
                
                # Create the payment
                payment = Payment.objects.create(
                    order=order,
                    payment_method='paypal',
                    payment_id=payment.id,
                    amount=order_amounts
                )
                if affiliate_instance:
                    # Calculate commission (40% of the discount amount)
                    commission_amount = Decimal(order_amounts ) * Decimal(0.40)

                    # Create affiliate earning record
                    affiliate_earning.objects.create(
                        affiliate_account_id=affiliate_instance.id,
                        order=order,
                        order_amunt=order_amounts,
                        comision_amunt=commission_amount
                    )
                   
               
                    affiliate_instance.total_order += 1
                    affiliate_instance.total_amunt = Decimal(affiliate_instance.total_amunt) + commission_amount
                    affiliate_instance.save()
            
            # Return the approval URL
            return Response({"approval_url": approval_url.href}, status=200)
        
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        



@api_view(['GET', 'POST', 'PUT'])
def token_wallets(request, user_id):
    try:
        user = User.objects.get(id=user_id)  # Fetch user by user_id
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # Get the user's token wallet
        wallet = tokenWallet.objects.filter(user=user).first()  # Assuming 1 wallet per user
        if wallet:
            serializer = TokenWalletSerializer(wallet)
            return Response(serializer.data)
        else:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        # Create a new token wallet for the user
        data = {'user': user.id, 'token': request.data.get('token', 0)}  # Default to 0 if no token is provided
        serializer = TokenWalletSerializer(data=data)
        if serializer.is_valid():
            serializer.save()  # Save the new wallet
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        # Update the user's token balance
        wallet = tokenWallet.objects.filter(user=user).first()
        if wallet:
            # Update the wallet's token balance
            wallet.token = request.data.get('token', wallet.token)
            wallet.save()
            return Response({"message": "Wallet updated", "token": wallet.token})
        else:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

class DailyTasksView(generics.CreateAPIView):
    def get(self, request, *args, **kwargs):
        queryset = DailyTask.objects.all()  # Get all DailyTask objects
        serializer = DailyTaskSerializer(queryset, many=True)  # Correct usage of many=True
        return Response(
            serializer.data,  # Serialize the queryset data
            status=status.HTTP_200_OK  # Use 200 OK for GET requests, not 201
        )


class ConflictViewSet(viewsets.ModelViewSet):
    queryset = Conflict.objects.all().order_by('-created_at')
    serializer_class = ConflictSerializer

    def create(self, request, *args, **kwargs):
        # Print the user for debugging
        print(request.user)

        # Add the user to the request data before validation
        data = request.data.copy()
        data['user'] = request.user.id  # Assuming you have a user field in the Conflict model
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        try:
            if data['assign_to']:
                pass
        except:
            tred = threading.Thread(target=process_assessment, args=(serializer.data['id'],))
            tred.start()
        Notification.objects.create(
            user = request.user,
            title = "New Conflict Created",
            message = f'New Conflict created name: {data['title']}'

        )
       
            
        

        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )

    def list(self, request, *args, **kwargs):
        # Custom list method to return simplified party data for friend selection
        user = request.user
        friends = FriendsList.objects.filter(user=user, confirmed=True)
        print(friends)
        friend_details = []  # Use a list to store friend details

        for friend_request in friends:
            # Retrieve the last conflict for each friend
            last_conflict = Conflict.objects.filter(user=friend_request.friend).order_by('-updated_at').first()
            
            friend_details.append({
                'id': friend_request.friend.id,
                'username': friend_request.friend.username,
                'full_name': friend_request.friend.first_name + ' ' + friend_request.friend.last_name,
                'last_conflict': last_conflict.title if last_conflict else None,
                'last_conflict_date': last_conflict.updated_at if last_conflict else None
            })

        return Response(friend_details)



def search_coupon(request,type, coupon):
    try:
        main_price = 0
        p= Packages.objects.last()
        if type == 'monthly':
            main_price = p.monthly_amount
        elif type == 'yearly':
            main_price = p.yearly_amount
        else:
            return JsonResponse({'error': 'Order Type Required.'}, status=400)

        a = affiliate.objects.get(affiliate_code=coupon)
        a.total_clicks += 1
        a.save()
        customer_commission = Decimal(a.customer_comission or '0.00')
        discount_amount = (customer_commission / 100) * Decimal(main_price)
        discount_price = Decimal(main_price)-discount_amount
        context = {
            'message': 'Coupon Code Valid.',
            'discounted_price': discount_price,
        }
        return JsonResponse({'data': context}, status=200)
    except:
        return JsonResponse({'error': 'Invalid Coupon Code'}, status=400)

def search_pakage(request):
    a = Packages.objects.last()
    seralizer = PackagesSerializer(a)
    return JsonResponse({'results': seralizer.data})

def search_users(request):
    query = request.GET.get('query', '').strip()
    if not query:
        return JsonResponse({'error': 'No query provided'}, status=400)
    
    current_user = request.user
    # Search users and annotate additional fields
    users = FriendsList.objects.filter(
        Q(friend__isnull=False),
        Q(friend__username__icontains=query) | Q(friend__email__icontains=query),
        ~Q(friend=current_user), # Exclude the logged-in user
        confirmed=True
    ).annotate(
        friend_name=Concat('friend__first_name', Value(' '), 'friend__last_name'),  # Concatenate first_name and last_name
        name=Concat('user__first_name', Value(' '), 'user__last_name')  # Concatenate user first_name and last_name
    ).values(
        'id', 'name', 'friend_name'
    )

    # Prepare results for JSON response, deduplicate by using a set
    seen = set()
    results = []
    for item in users:
        unique_key = (item['name'], item['friend_name'])
        if unique_key not in seen:
            seen.add(unique_key)
            results.append({
                'id': item['id'],
                'name': item['name'],
                'friend_name': item['friend_name'],
            })

    return JsonResponse({'results': results})



class FriendRequestsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Debugging: Log the username
        print(f"Request user: {user.username}")

        # Filter for all friend requests where the current user is the friend and request is not confirmed
        pending_friend_requests = FriendsList.objects.filter(
            friend=user,
            confirmed=False
        )

        # Debugging: Check if any records are returned from the query
        print(f"Pending friend requests query: {pending_friend_requests.query}")
        print(f"Pending friend requests count: {pending_friend_requests.count()}")

        # Prepare the list of friend request details
        friend_details = [
            {
                'id': friend_request.user.id,
                'username': friend_request.user.username,
                'name': f"{friend_request.user.first_name} {friend_request.user.last_name}"
            }
            for friend_request in pending_friend_requests
        ]

        # Output the friend details for debugging
        print(f"Friend requests list: {friend_details}")

        # Return the friend requests as the response
        return Response({"detail": friend_details}, status=status.HTTP_200_OK)
    
    def post(self, request):
        user = request.user
        friend_id = request.data.get("friend_id")

        if not friend_id:
            return Response({"error": "Friend ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find the friend request to confirm
            friend_request = FriendsList.objects.get(
                friend=user,
                user_id=friend_id,
                confirmed=False
            )
        except FriendsList.DoesNotExist:
            return Response(
                {"error": "Friend request not found or already confirmed."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Confirm the friend request
        friend_request.confirmed = True
        friend_request.save()

        return Response(
            {"detail": f"Friend request from {friend_request.user.username} has been confirmed."},
            status=status.HTTP_200_OK
        )


class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        query = request.GET.get('query', '').strip()  # Get the query parameter
        
        # Get all confirmed friends of the user
        friends_user = SingleFriendList.objects.filter(
            Q(friend1=user) | Q(friend2=user),
        )

        if query:
            # Filter friends based on the query (search in username, email, or full name)
            friends = friends_user.filter(
                Q(friend1__username__icontains=query) |
                Q(friend1__email__icontains=query) |
                Q(friend1__first_name__icontains=query) |
                Q(friend1__last_name__icontains=query) |
                Q(friend2__username__icontains=query) |
                Q(friend2__email__icontains=query) |
                Q(friend2__first_name__icontains=query) |
                Q(friend2__last_name__icontains=query)
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
        filtered_data = [item for item in friend_details if item['username'] != request.user.username]
        
        return Response({"detail": filtered_data}, status=status.HTTP_200_OK)


class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        print(user)
        friend_email = request.data.get('email')

        # Assuming you have a way to fetch the user by email
        friend = get_object_or_404(User, email=friend_email)
        if friend == user:
            return Response({"detail": "Can't send friend request to your self."}, status=status.HTTP_400_BAD_REQUEST)
        friend_request, created = FriendsList.objects.get_or_create(user=user, friend=friend)
        if not created:
            return Response({"detail": "Friend request already sent"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a friend request link
        link = f"http://localhost:3000/friend-request/{friend_request.token}"

        # Send email
        send_mail(
            subject="Friend Request",
            message=f"Click the link to add {user.username} as a friend: {link}",
            from_email="yourapp@example.com",
            recipient_list=[friend_email],
        )
        return Response({"detail": "Friend request sent"}, status=status.HTTP_200_OK)


class ConfirmFriendRequestView(APIView):
    def get(self, request, token):
        # Fetch the friend request using the token
        friend_request = get_object_or_404(FriendsList, token=token)

        # Update the confirmed field to True
        friend_request.confirmed = True
        friend_request.save()

        # Optional: Add additional logic for mutual friendships, notifications, etc.

        return Response({"detail": "Friend request confirmed successfully"})



class NoteViewSet(APIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all notes for the logged-in user
        notes = Note.objects.filter(user=request.user)
        serializer = self.serializer_class(notes, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Create a new note for the logged-in user
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            serializer = self.serializer_class(note, data=request.data, partial=False)  # Set partial=True if you want to update only part of the note
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
        

    def delete(self, request, pk=None):
        # Delete a specific note by ID
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            note.delete()
            return Response({"message": "Note deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)


class AssintoConflictView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            print(request.data.get('assign_description'))
            # Retrieve the conflict object
            conflict = Conflict.objects.get(pk=pk)

            # Update the fields from the request data
            conflict.assign_description = request.data.get('assign_description', conflict.assign_description)
            conflict.status = request.data.get('status', conflict.status)
            conflict.save()

            tred = threading.Thread(target=process_assessment, args=(pk,))
            tred.start()

            # Serialize and return the updated conflict
            serializer = ConflictSerializer(conflict)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Conflict.DoesNotExist:
            return Response({"detail": "Conflict not found."}, status=status.HTTP_404_NOT_FOUND)

class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            notification = Notification.objects.filter(user=request.user)
            serializer = NotificationSerializer(notification, many=True)
            return Response(serializer.data)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk)
            notification.delete()
            return Response({"detail": "Deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    # PUT: Update the 'read' status of a specific notification
    def put(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)  # Ensure user owns the notification
            notification.read = request.data.get('read', notification.read)  # Update 'read' field based on the request data
            notification.save()

            # Serialize and return the updated notification
            serializer = NotificationSerializer(notification)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

















