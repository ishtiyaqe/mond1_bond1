from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
   
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    role = models.CharField(max_length=100, choices=(('admin', 'Admin'), ('user', 'User')), default='user')
    

    def __str__(self):
        return self.username