from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.hashers import make_password
from .serializers import (
    UserLoginSerializer,
    RegistrationConfirmSerializer,
    UserDetailSerializer,
    DeleteAccountSerializer
)

User = get_user_model()

# -----------------------------
# 發送驗證碼 (不實作 email 發送功能，僅用 cache 模擬)
# -----------------------------
class SendVerificationCode(APIView):
    """
    POST /auth/verification/send/
    發送驗證碼（僅模擬，不實際發送email）
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({
                "status": "error",
                "message": "Email is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        import random
        code = str(random.randint(100000, 999999))
        cache.set(f"verification_code_{email}", code, timeout=300)
        print(f"Verification code for {email}: {code}")  # 測試用（實際應發送email）

        return Response({
            "status": "success",
            "message": "驗證碼已發送，有效時間為5分鐘",
            "data": None
        }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')


# -----------------------------
# 註冊確認
# -----------------------------
class RegistrationConfirm(APIView):
    """
    POST /auth/registration/confirm/
    註冊確認
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["verification_code"]

        # 檢查驗證碼
        cached_code = cache.get(f"verification_code_{email}")
        if cached_code != code:
            return Response({
                "status": "error",
                "message": "驗證碼錯誤或已失效",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')

        # 檢查email是否已註冊
        if User.objects.filter(email=email).exists():
            return Response({
                "status": "error",
                "message": "此電子郵件已被註冊",
                "data": None
            }, status=status.HTTP_409_CONFLICT,content_type='application/json; charset=utf-8')

        # 建立用戶
        # 從 email 提取 @ 前面的字串作為 name
        name = email.split('@')[0]
        user = User.objects.create_user(
            username=email,
            email=email,
            password=serializer.validated_data["password"],
            first_name=name
        )

        # 刪除已使用的驗證碼
        cache.delete(f"verification_code_{email}")

        return Response({
            "status": "success",
            "message": "註冊成功",
            "data": None
        }, status=status.HTTP_201_CREATED,content_type='application/json; charset=utf-8')


# -----------------------------
# 登入
# -----------------------------
class LoginView(APIView):
    """
    POST /auth/login/
    用戶登入
    """
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
                "status": "success",
                "message": "登入成功",
                "data": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh)
                }
            }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')
        else:
            return Response({
                "status": "error",
                "message": "電子郵件或密碼錯誤",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED,content_type='application/json; charset=utf-8')


# -----------------------------
# 密碼重設
# -----------------------------
class PasswordResetConfirmView(APIView):
    """
    POST /auth/password/reset/confirm/
    密碼重設確認
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        code = request.data.get("verification_code")

        # 基本欄位檢查
        if not all([email, password, code]):
            return Response({
                "status": "error",
                "message": "缺少必要欄位",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')

        # 查找使用者
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "status": "error",
                "message": "用戶不存在",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')

        # 檢查驗證碼
        cached_code = cache.get(f"verification_code_{email}")
        if cached_code != code:
            return Response({
                "status": "error",
                "message": "驗證碼錯誤或已失效",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')

        # 修改密碼
        user.password = make_password(password)
        user.save()

        # 刪除已使用的驗證碼
        cache.delete(f"verification_code_{email}")

        return Response({
            "status": "success",
            "message": "密碼重設成功",
            "data": None
        }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')


# -----------------------------
# 用戶資料
# -----------------------------
class UserDetail(APIView):
    """
    GET /auth/user/ - 取得用戶資料
    PUT /auth/user/ - 更新用戶資料
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response({
            "status": "success",
            "message": "用戶資料取得成功",
            "data": serializer.data
        }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')

    def put(self, request):
        serializer = UserDetailSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "用戶資料更新成功",
                "data": serializer.data
            }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')
        return Response({
            "status": "error",
            "message": "資料驗證失敗",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')


# -----------------------------
# 刪除帳號
# -----------------------------
class DeleteAccount(APIView):
    """
    POST /auth/delete_account/
    永久刪除帳號
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data["password"]
        if not request.user.check_password(password):
            return Response({
                "status": "error",
                "message": "密碼錯誤",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED,content_type='application/json; charset=utf-8')

        request.user.delete()
        return Response({
            "status": "success",
            "message": "帳號已成功刪除",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT,content_type='application/json; charset=utf-8')

