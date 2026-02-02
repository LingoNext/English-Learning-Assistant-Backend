from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

# 登入序列化器
class UserLoginSerializer(serializers.Serializer):
    """用於 /auth/login/ 端點的簡化序列化器"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

# 註冊確認序列化器
class RegistrationConfirmSerializer(serializers.Serializer):
    """用於 /auth/registration/confirm/ 端點的簡化序列化器"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    verification_code = serializers.CharField()

# 用戶資料序列化器
class UserDetailSerializer(serializers.ModelSerializer):
    """用於 /auth/user/ 端點的簡化序列化器"""
    name = serializers.CharField(source="first_name", required=False, allow_blank=True, read_only=True)
    new_name = serializers.CharField(source="first_name", required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = ["email", "name", "new_name"]
        read_only_fields = ["email"]

    def update(self, instance, validated_data):
        if 'first_name' in validated_data:
            instance.first_name = validated_data.get('first_name', instance.first_name)
            instance.save()
        return instance

# 刪除帳號序列化器
class DeleteAccountSerializer(serializers.Serializer):
    """用於 /auth/delete_account/ 端點的簡化序列化器"""
    password = serializers.CharField(write_only=True)
