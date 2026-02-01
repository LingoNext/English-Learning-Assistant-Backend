from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.hashers import make_password
from .serializers import (
    UserLoginSerializer,
    RegistrationConfirmSerializer,
    UserDetailSerializer,
    DeleteAccountSerializer
)
from django.conf import settings
from .rate_limiter import (
    email_rate_limit,
    get_client_ip
)
import requests
import secrets
import hashlib

User = get_user_model()

# -----------------------------
# 發送驗證碼
# -----------------------------
class SendVerificationCode(APIView):
    """
    POST /auth/verification/send/
    發送驗證碼（實際發送 email）
    """
    permission_classes = [AllowAny]

    @email_rate_limit
    def post(self, request):
        # 從請求取得 email
        email = request.data.get('email')
        if not email:
            return Response({"message": "需要郵件","data":None}, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')

        email_normalized = email.strip().lower()  # 去空格、統一小寫
        email_hash = hashlib.sha256(email_normalized.encode()).hexdigest()

        # 記錄客戶端 IP 用於日誌
        client_ip = get_client_ip(request)
        print(f"Verification code requested for {email_normalized} from IP {client_ip}")

        # 產生六位數驗證碼(時間敏感操作，不可用 random，改使用 secrets 模組)
        code = ''.join(str(secrets.randbelow(10)) for _ in range(6))

        # 將驗證碼存入快取，有效期五分鐘
        cache.set(f"verification_code_{email_hash}", code, timeout=300)

        subject = "專題程式的驗證碼"
        message = f"""您好：

        您的驗證碼為：{code}
        請於五分鐘內完成註冊。

        若您並未進行註冊，請直接忽略此郵件，無需進行任何操作。

        英語學習小幫手 APP
        國立臺中科技大學 CSIE
        2026 資訊與流通學院 大學部畢業專題
        開發團隊：LingoNext

        網頁版專題展示(使用手機 APP 更佳)：
        https://english-learning-assistant.pages.dev/
        """

        # 使用 Resend API 發送郵件
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {getattr(settings, 'SEND_EMAIL_API_KEY', None)}",
                "Content-Type": "application/json"
            },
            json={
                "from": getattr(settings, 'FROM_EMAIL', None),
                "to": [email.strip()],# 只處理空格，但保持原本大小寫
                "subject": subject,
                "text": message,
            }
        )
        if response.status_code == 200:
            return Response({"message": "驗證碼已成功發送","data": None}, status=status.HTTP_200_OK,
                            content_type='application/json; charset=utf-8')
        else:
            return Response({"message": "郵件發送失敗","data": None}, status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content_type='application/json; charset=utf-8')

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

        email_normalized = email.strip().lower()  # 去空格、統一小寫
        email_hash = hashlib.sha256(email_normalized.encode()).hexdigest()
        cached_code = cache.get(f"verification_code_{email_hash}")
        if cached_code != code:
            return Response({
                "message": "驗證碼錯誤或已失效",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')

        # 檢查 email 是否已註冊
        if User.objects.filter(email=email).exists():
            return Response({
                "message": "此電子郵件已被註冊",
                "data": None
            }, status=status.HTTP_409_CONFLICT,content_type='application/json; charset=utf-8')

        # 建立用戶(預設從 email 提取 @ 前面的字串作為 name)
        name = email.split('@')[0]
        user = User(
            username=email,
            email=email,
            first_name=name
        )
        user.set_password(serializer.validated_data["password"])
        user.save()

        # 刪除已使用的驗證碼
        cache.delete(f"verification_code_{email_hash}")

        return Response({
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
        if not email or not password:
            return Response({
                "message": "缺少必要欄位",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')
        # 使用 Django authenticate 驗證
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # 產生 JWT Token
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "登入成功",
                "data": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh)
                }
            }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')
        else:
            return Response({
                "message": "電子郵件或密碼錯誤",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED,content_type='application/json; charset=utf-8')


# -----------------------------
# Token 刷新
# -----------------------------
class TokenRefreshView(APIView):
    """
    POST /auth/token/refresh/
    重新整理 Token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response({
                "message": "缺少 refresh_token 欄位",
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

        try:
            # 驗證並刷新 token
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)

            return Response({
                "data": {
                    "access_token": new_access_token
                }
            }, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')

        except TokenError:
            return Response({
                "message": "Token 無效或已過期",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json; charset=utf-8')


# -----------------------------
# Token 驗證
# -----------------------------
class TokenVerifyView(APIView):
    """
    POST /auth/token/verify/
    驗證 Token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("access_token")

        if not access_token:
            return Response({
                "message": "缺少 access_token 欄位",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

        try:
            # 驗證 access token
            AccessToken(access_token)

            return Response({
                "message": "Token 有效",
            }, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')

        except TokenError:
            return Response({
                "message": "Token 無效或已過期",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json; charset=utf-8')


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

        email_normalized = email.strip().lower()  # 去空格、統一小寫
        email_hash = hashlib.sha256(email_normalized.encode()).hexdigest()

        # 基本欄位檢查
        if not all([email, password, code]):
            return Response({
                "message": "缺少必要欄位",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')

        # 查找使用者
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "message": "用戶不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND,content_type='application/json; charset=utf-8')

        # 檢查驗證碼
        cached_code = cache.get(f"verification_code_{email_hash}")
        if cached_code != code:
            return Response({
                "message": "驗證碼錯誤或已失效",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED,content_type='application/json; charset=utf-8')

        # 修改密碼
        user.password = make_password(password)
        user.save()

        # 刪除已使用的驗證碼
        cache.delete(f"verification_code_{email_hash}")

        return Response({
            "message": "密碼重設成功",
            "data": None
        }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')

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
        if not password:
            return Response({
                "message": "密碼為必填欄位",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')
        if not request.user.check_password(password):
            return Response({
                "message": "密碼錯誤",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED,content_type='application/json; charset=utf-8')
        request.user.delete()
        return Response({
            "message": "帳號已成功刪除",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT,content_type='application/json; charset=utf-8')

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
            "message": "用戶資料取得成功",
            "data": serializer.data
        }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')

    def put(self, request):
        new_name = request.data.get("new_name", "").strip()
        if not new_name:
            return Response({
                "message": "缺少必要欄位",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')
        serializer = UserDetailSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "用戶資料更新成功",
                "data": serializer.data
            }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')
        return Response({
            "message": "資料驗證失敗",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST,content_type='application/json; charset=utf-8')