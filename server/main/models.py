from django.db import models
import random
from django.contrib.auth import get_user_model, authenticate
User = get_user_model()
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
import uuid
from django.dispatch import receiver
from django.db.models.signals import pre_save




class tokenWallet(models.Model):
    user = models.OneToOneField(User, related_name='tokenWallet', on_delete=models.CASCADE)
    token = models.IntegerField(max_length=224, default=0)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    def __str__(self):
        return f" {self.token}"
    

def generate_random_token():
    return get_random_string(length=64)

class FriendsList(models.Model):
    user = models.ForeignKey(User, related_name='friend_requests_sent', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friend_requests_received', on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)  # Confirmation field
    user_online = models.BooleanField(default=False)  # Field for user's online status
    friend_online = models.BooleanField(default=False)  # Field for friend's online status
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_random_token,  # Use the named function
        null=True
    )

    def __str__(self):
        return f"{self.user.username} -> {self.friend.username} ({'Confirmed' if self.confirmed else 'Pending'})"
    
    def save(self, *args, **kwargs):
        # Ensure that the instance is saved before additional operations
        super().save(*args, **kwargs)

        # Check if the relationship is confirmed
        if self.confirmed:
            # Check if there is already a SingleFriendList entry for the pair of users
            if not SingleFriendList.objects.filter(
                friend1__in=[self.user, self.friend],
                friend2__in=[self.user, self.friend]
            ).exists():
                # Create a new SingleFriendList entry
                SingleFriendList.objects.create(
                    friend1=min(self.user, self.friend, key=lambda u: u.id),
                    friend2=max(self.user, self.friend, key=lambda u: u.id)
                )

    def last_online_time(self):
        if self.friend_online:
            time_diff = timezone.now() - self.updated_at
            # Calculate how many minutes ago, and if it's more than 60, show in hours
            if time_diff < timedelta(minutes=60):
                return f"{time_diff.seconds // 60} minutes ago"
            elif time_diff < timedelta(hours=24):
                return f"{time_diff.seconds // 3600} hours ago"
            else:
                return f"{time_diff.days} days ago"
        else:
            return "Offline"

class SingleFriendList(models.Model):
    friend1 = models.ForeignKey(User, related_name='single_friendlist_friend1', on_delete=models.CASCADE)
    friend2 = models.ForeignKey(User, related_name='single_friendlist_friend2', on_delete=models.CASCADE)

    def __str__(self):
        return f"Friend1: {self.friend1.username}, Friend2: {self.friend2.username}"

class Notification(models.Model):
    user = models.ForeignKey(User, related_name='notification', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.title

class Packages(models.Model):
    monthly_amount = models.CharField(max_length=100)
    yearly_amount = models.CharField(max_length=100)

class Order(models.Model):
    user = models.OneToOneField(User, related_name='Order', on_delete=models.CASCADE,null=True)
    promo_code = models.CharField(max_length=100,null=True, blank=True)
    total_amount = models.CharField(max_length=100,null=True)
    payment_id = models.CharField(max_length=100,null=True)
    order_type = models.CharField(
        max_length=20, 
        choices=[
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='monthly'
    )
    status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.user.username} - {self.order_type} - {self.status} -  {self.promo_code}"


class affiliate(models.Model):
    user = models.ForeignKey(User, related_name='affiliate', on_delete=models.CASCADE)
    affiliate_code = models.CharField(max_length=255, unique=True, blank=True)  # Ensure unique and allow blank
    total_amunt = models.CharField(max_length=20, default=0)  # Use DecimalField for monetary values
    total_order = models.IntegerField(default=0)  # Use DecimalField for monetary values
    paypal_address = models.CharField(max_length=255)
    total_clicks = models.IntegerField(default=0, blank=True, null=True)  # Ensure default value is 0
    his_comission = models.CharField(max_length=255, blank=True, null=True)
    customer_comission = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}"


@receiver(pre_save, sender=affiliate)
def generate_unique_affiliate_code(sender, instance, **kwargs):
    if not instance.affiliate_code:  # Only generate if the field is blank
        instance.affiliate_code = str(uuid.uuid4())[:8]  # Generate a unique code
        while affiliate.objects.filter(affiliate_code=instance.affiliate_code).exists():
            instance.affiliate_code = str(uuid.uuid4())[:8]  # Ensure uniquenes\
                
class affiliate_earning(models.Model):
    PAID = 'paid'
    UNPAID = 'unpaid'
    STATUS_CHOICES = [
        (PAID, 'Paid'),
        (UNPAID, 'Unpaid'),
    ]

    affiliate_account = models.ForeignKey(affiliate, to_field="id", on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    order_amunt = models.CharField(max_length=255)
    comision_amunt = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=UNPAID,
    )

    def __str__(self):
        return f"{self.affiliate_account} - {self.order} - {self.status}"



class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)




class Conflict(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(User, related_name='conflict', on_delete=models.CASCADE, null=True)
    assign_to = models.ForeignKey(User, related_name='conflict_assigned_to', on_delete=models.CASCADE, null=True)
    description = models.TextField()
    assign_description = models.TextField(null=True, blank=True)
    impact = models.JSONField(null=True, blank=True)  # Changed to JSONField
    responsibility = models.JSONField(null=True, blank=True)  # Changed to JSONField
    factors = models.JSONField(null=True, blank=True)  # Changed to JSONField
    nextSteps = models.JSONField(null=True, blank=True)  # Changed to JSONField
    contextualOverview = models.TextField(null=True, blank=True)
    primaryIssues = models.JSONField(null=True, blank=True)  # Changed to JSONField
    perspectives = models.JSONField(null=True, blank=True)  # Changed to JSONField
    accountability = models.JSONField(null=True, blank=True)  # Changed to JSONField
    improvements = models.JSONField(null=True, blank=True)  # Changed to JSONField
    actionPlan = models.JSONField(null=True, blank=True)  # Changed to JSONField
    resources = models.JSONField(null=True, blank=True)  # Changed to JSONField
    premium_tools = models.JSONField(null=True, blank=True)  # Changed to JSONField
    status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class Party(models.Model):
    conflict = models.ForeignKey(
        Conflict, 
        related_name='parties', 
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    role = models.CharField(
        max_length=20, 
        choices=[
            ('initiator', 'Initiator'),
            ('participant', 'Participant')
        ]
    )
    avatar = models.CharField(max_length=10, blank=True, null=True)
    last_conflict = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.conflict.title}"

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class DailyTask(models.Model):
    DAY_CHOICES = [(i, f"Day {i}") for i in range(1, 6)]  # Days 1 to 5
    ICON_CHOICES = [
        ('Star', 'Star'),
        ('Heart', 'Heart'),
        ('Sparkles', 'Sparkles'),
        ('Award', 'Award'),
        ('Gift', 'Gift')
    ]
    COLOR_CHOICES = [
        ('from-amber-500 to-yellow-500', 'from-amber-500 to-yellow-500'),
        ('from-pink-500 to-rose-500', 'from-pink-500 to-rose-500'),
        ('from-violet-500 to-purple-500', 'from-violet-500 to-purple-500'),
        ('from-blue-500 to-indigo-500', 'from-blue-500 to-indigo-500'),
        ('from-emerald-500 to-green-500', 'from-emerald-500 to-green-500')
    ]

    id = models.AutoField(primary_key=True)
    day = models.PositiveSmallIntegerField(choices=DAY_CHOICES, default=1)
    title = models.CharField(max_length=255)
    points = models.PositiveIntegerField(default=0)
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='Star')  # Using CharField for icon names
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=50, choices=COLOR_CHOICES, default='from-amber-500 to-yellow-500')

    def save(self, *args, **kwargs):
        # Randomly assign points between 1 and 5
        self.points = random.randint(1, 5)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (Day {self.day})"








