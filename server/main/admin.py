from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(Conflict)
class ConflictAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in Conflict._meta.fields]


@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in DailyTask._meta.fields]



@admin.register(Packages)
class PackagesAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in Packages._meta.fields]



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in Order._meta.fields]



@admin.register(affiliate)
class affiliateAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in affiliate._meta.fields]



@admin.register(SingleFriendList)
class SingleFriendListAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in SingleFriendList._meta.fields]




@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in Payment._meta.fields]




@admin.register(affiliate_earning)
class affiliate_earningAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in affiliate_earning._meta.fields]




@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in Notification._meta.fields]


@admin.register(tokenWallet)
class tokenWalletAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in tokenWallet._meta.fields]



@admin.register(FriendsList)
class FriendsListAdmin(admin.ModelAdmin):
    list_display =  [field.name for field in FriendsList._meta.fields]





