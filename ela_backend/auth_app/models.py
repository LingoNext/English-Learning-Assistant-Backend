from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("電子郵件是必需的")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractUser):
    level = models.CharField(max_length=4, default="A2")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

class VerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=50)  # e.g. "register", "password_reset"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} ({self.purpose})"