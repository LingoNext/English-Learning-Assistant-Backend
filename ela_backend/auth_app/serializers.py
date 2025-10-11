from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

# 登入序列化器
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

# 註冊確認序列化器
class RegistrationConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    verification_code = serializers.CharField()
    name = serializers.CharField()

# 用戶資料序列化器
class UserDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name")

    class Meta:
        model = User
        fields = ["id", "email", "name"]

# 刪除帳號序列化器
class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
