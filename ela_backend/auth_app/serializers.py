from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


# 登入序列化器
class UserLoginSerializer(serializers.Serializer):
    """用於 POST /auth/login/ 端點的簡化序列化器"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# 註冊確認序列化器
class RegistrationConfirmSerializer(serializers.Serializer):
    """用於 POST /auth/registration/confirm/ 端點的簡化序列化器"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    verification_code = serializers.CharField()

    def validate_password(self, value):
        validate_password(value)
        return value


# 用戶資料序列化器
class UserDetailSerializer(serializers.ModelSerializer):
    """用於 GET、PUT /auth/user/ 端點的簡化序列化器"""
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