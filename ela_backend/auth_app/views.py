from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth import authenticate
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import make_password
from .models import VerificationCode
from .serializers import (
    UserLoginSerializer,
    RegistrationConfirmSerializer,
    UserDetailSerializer,
    DeleteAccountSerializer
)

User = get_user_model()

# -----------------------------
# 發送驗證碼
# -----------------------------
class SendVerificationCode(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        import random
        code = str(random.randint(100000, 999999))
        cache.set(f"verification_code_{email}", code, timeout=300)
        print(f"Verification code for {email}: {code}")  # 測試用
        return Response({"message": "Verification code sent"}, status=status.HTTP_200_OK)

# -----------------------------
# 註冊確認
# -----------------------------
class RegistrationConfirm(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegistrationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["verification_code"]
        cached_code = cache.get(f"verification_code_{email}")
        if cached_code != code:
            return Response({"error": "Invalid verification code"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_409_CONFLICT)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data["name"]
        )
        return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)

# -----------------------------
# 登入
# -----------------------------
class LoginView(APIView):
   permission_classes = [AllowAny]
   def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        # 使用 Django authenticate 驗證
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # 產生 JWT Token
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login successful",
                "data": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh)
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "Invalid email or password"
            }, status=status.HTTP_401_UNAUTHORIZED)

# -----------------------------
# 用戶資料
# -----------------------------
class UserDetail(APIView):
    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserDetailSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# -----------------------------
# 刪除帳號
# -----------------------------
class DeleteAccount(APIView):
    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data["password"]
        if not request.user.check_password(password):
            return Response({"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)
        request.user.delete()
        return Response({"message": "Account deleted"}, status=status.HTTP_204_NO_CONTENT)

class PasswordResetConfirmView(APIView):
    """
    POST /auth/password/reset/confirm/
    Body: { "email": "...", "password": "...", "verification_code": "..." }
    """

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        code = request.data.get("verification_code")

        # 基本欄位檢查
        if not all([email, password, code]):
            return Response({"error": "缺少必要欄位"}, status=status.HTTP_400_BAD_REQUEST)

        # 查找使用者
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "用戶不存在"}, status=status.HTTP_400_BAD_REQUEST)

        # 驗證碼比對
        try:
            record = VerificationCode.objects.get(email=email, code=code, purpose="password_reset")
        except VerificationCode.DoesNotExist:
            return Response({"error": "驗證碼錯誤或已失效"}, status=status.HTTP_400_BAD_REQUEST)

        # 修改密碼
        user.password = make_password(password)
        user.save()

        # 驗證碼作廢（避免重用）
        record.delete()

        return Response({"message": "密碼重設成功"}, status=status.HTTP_200_OK)