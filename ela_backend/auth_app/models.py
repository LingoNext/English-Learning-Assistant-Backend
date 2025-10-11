from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    level = models.CharField(max_length=4, default="A2")
    created_at = models.DateTimeField(auto_now_add=True)
    
class VerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=50)  # e.g. "register", "password_reset"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} ({self.purpose})"