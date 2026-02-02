from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("電子郵件必須提供")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    # email: 電子郵件，必填，唯一
    email = models.EmailField(unique=True)

    # 覆寫AbstractUser的first_name以符合規格（必填，預設值""）
    first_name = models.CharField(max_length=150, default="")

    # 以下欄位繼承自AbstractUser，符合規格要求：
    # last_name: 姓氏（string, 非必填, 預設""）
    # is_active: 帳號是否啟用（boolean, 非必填, 預設True）
    # is_staff: 是否為管理員（boolean, 非必填, 預設False）
    # is_superuser: 是否為超級管理員（boolean, 非必填, 預設False）
    # date_joined: 帳號註冊時間（datetime, 非必填, 自動生成）
    # last_login: 最後登入時間（datetime, 非必填, 自動更新）

    # created_at: 帳號建立時間（datetime, 非必填, 自動生成）
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # 空的，只需要 email 和 password

    objects = UserManager()

class VerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=50)  # e.g. "register", "password_reset"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} ({self.purpose})"