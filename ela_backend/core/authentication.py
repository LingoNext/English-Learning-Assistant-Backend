# core/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

class ActiveJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        覆寫 Simple JWT get_user()，當帳號停用時返回自訂訊息
        """
        user = super().get_user(validated_token)
        if not user.is_active:
            raise AuthenticationFailed("此帳號已被停用", code="user_inactive")
        return user