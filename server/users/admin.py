from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('username', 'email', 'is_verified', 'role',  'is_staff','is_premium')
    list_filter = ('is_verified', 'role', )
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'role',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff','is_premium', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(CustomUser, UserAdmin)
