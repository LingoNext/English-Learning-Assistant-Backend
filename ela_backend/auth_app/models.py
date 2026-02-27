from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("電子郵件必須提供")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    # email: 電子郵件，必填，唯一
    username = None
    last_name= None

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    # data_joined: 用戶註冊時間，自動設置為當前時間

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

class VerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=50)  # e.g. "register", "password_reset"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} ({self.purpose})"