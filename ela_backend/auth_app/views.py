from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.hashers import make_password
from .serializers import (
    UserLoginSerializer,
    RegistrationConfirmSerializer,
    UserDetailSerializer,
    DeleteAccountSerializer
)
from django.conf import settings
from .rate_limiter import (
    email_rate_limit_v2,
    general_rate_limit,
    get_client_ip,
    get_device_id_from_request,
    get_or_create_device_id
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
    POST /auth/verification/send/ - 發送驗證碼
    """
    permission_classes = [AllowAny]

    @email_rate_limit_v2
    def post(self, request):
        # 從請求取得 email
        email = request.data.get('email')
        purpose = request.data.get('purpose')

        # 記錄客戶端 IP 用於日誌
        client_ip = get_client_ip(request)
        device_id = get_device_id_from_request(request)
        device_fingerprint = get_or_create_device_id(request)

        print(f"Verification code requested for {email} from IP {client_ip}, Device ID: {device_id}")

        if not email or not purpose:
            return Response({"message": "缺少必要參數", "data": None}, status=status.HTTP_400_BAD_REQUEST,
                            content_type='application/json; charset=utf-8')
        if purpose not in ['registration', 'password_reset']:
            return Response({"message": "目的參數錯誤", "data": None}, status=status.HTTP_400_BAD_REQUEST,
                            content_type='application/json; charset=utf-8')
        # 檢查 email 格式
        if "@" not in email or "." not in email.split("@")[-1]:
            return Response({"message": "無效的電子郵件地址", "data": None}, status=status.HTTP_400_BAD_REQUEST,
                            content_type='application/json; charset=utf-8')

        email_normalized = email.strip().lower()  # 去空格、統一小寫
        email_hash = hashlib.sha256(email_normalized.encode()).hexdigest()

        # 產生六位數驗證碼(時間敏感操作，不可用 random，改使用 secrets 模組)
        code = ''.join(str(secrets.randbelow(10)) for _ in range(6))

        # 將驗證碼存入快取，有效期五分鐘
        cache.set(f"verification_code_{email_hash}", code, timeout=300)

        if purpose == 'registration':
            action = "註冊"
        else:
            action = "重設密碼"

        subject = "帳號驗證碼通知"

        # 獲取裝置信息用於安全資訊
        user_agent = request.META.get('HTTP_USER_AGENT', '未知裝置')
        device_type = "行動裝置" if any(
            mobile in user_agent.lower() for mobile in ['mobile', 'android', 'iphone', 'ipad']) else "桌面裝置"

        # 簡化裝置資訊顯示
        device_info = f"裝置類型：{device_type}"
        if device_id:
            device_info += f"\n        裝置 ID：{device_id[:8]}****"  # 只顯示前8位，保護隱私
        else:
            device_info += f"\n        裝置指紋：{device_fingerprint[:8]}****"

        message = f"""
        您好，
        我們收到一筆帳號{action}請求，以下為您的驗證碼：

        ────────────────────
        驗證碼：{code}
        有效期限：5 分鐘
        ────────────────────

        請於有效期限內完成驗證。
        若超過時間，請重新發送驗證碼。

        【安全資訊】
        請求來源 IP：{client_ip}
        {device_info}
        若您未曾進行此操作，請忽略此郵件，將不會受到影響。

        ———
        英語學習小幫手 APP
        開發團隊：LingoNext

        國立臺中科技大學 資訊工程系
        2026 資訊與流通學院 大學部畢業專題

        專題展示頁面：
        https://english-learning-assistant.pages.dev/
        （建議使用手機 App 體驗完整功能）
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
                "to": [email.strip()],
                "subject": subject,
                "text": message,
            }
        )
        if response.status_code == 200:
            return Response({"message": "驗證碼已成功發送", "data": None}, status=status.HTTP_200_OK,
                            content_type='application/json; charset=utf-8')
        else:
            return Response({"message": "郵件發送失敗", "data": None}, status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content_type='application/json; charset=utf-8')


# -----------------------------
# 註冊確認
# -----------------------------
class RegistrationConfirm(APIView):
    """
    POST /auth/registration/confirm/ - 註冊確認
    """
    permission_classes = [AllowAny]

    @general_rate_limit(max_requests=10, time_window=300, action_type='registration_confirm')  # 5分鐘內最多10次註冊嘗試
    def post(self, request):
        serializer = RegistrationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["verification_code"]
        if not email or not code:
            return Response({
                "message": "缺少必要參數",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

        email_normalized = email.strip().lower()  # 去空格、統一小寫
        email_hash = hashlib.sha256(email_normalized.encode()).hexdigest()
        cached_code = cache.get(f"verification_code_{email_hash}")
        if cached_code != code:
            return Response({
                "message": "驗證碼錯誤或已失效",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

        # 檢查 email 是否已註冊
        if User.objects.filter(email=email).exists():
            return Response({
                "message": "此電子郵件已被註冊",
                "data": None
            }, status=status.HTTP_409_CONFLICT, content_type='application/json; charset=utf-8')

        # 建立用戶(預設從 email 提取 @ 前面的字串作為 name)
        name = email.split('@')[0]
        user = User(
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
        }, status=status.HTTP_201_CREATED, content_type='application/json; charset=utf-8')


# -----------------------------
# 登入
# -----------------------------
class LoginView(APIView):
    """
    POST /auth/login/ - 用戶登入
    """
    permission_classes = [AllowAny]

    @general_rate_limit(max_requests=5, time_window=300, action_type='login')  # 5分鐘內最多5次登入嘗試
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        if not email or not password:
            return Response({
                "message": "缺少必要參數",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')
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
            }, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')
        else:
            return Response({
                "message": "電子郵件或密碼錯誤",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json; charset=utf-8')


# -----------------------------
# Token 刷新
# -----------------------------
class TokenRefreshView(APIView):
    """
    POST /auth/token/refresh/ - 重新整理 Token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response({
                "message": "缺少必要參數",
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
    POST /auth/token/verify/ - 驗證 Token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("access_token")

        if not access_token:
            return Response({
                "message": "缺少必要參數",
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
    POST /auth/password/reset/confirm/ - 密碼重設確認
    """
    permission_classes = [AllowAny]

    @general_rate_limit(max_requests=3, time_window=600, action_type='password_reset')  # 10分鐘內最多3次密碼重置嘗試
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        code = request.data.get("verification_code")

        email_normalized = email.strip().lower()  # 去空格、統一小寫
        email_hash = hashlib.sha256(email_normalized.encode()).hexdigest()

        # 基本欄位檢查
        if not all([email, password, code]):
            return Response({
                "message": "缺少必要參數",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

        # 查找使用者
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "message": "用戶不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND, content_type='application/json; charset=utf-8')

        # 檢查驗證碼
        cached_code = cache.get(f"verification_code_{email_hash}")
        if cached_code != code:
            return Response({
                "message": "驗證碼錯誤或已失效",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json; charset=utf-8')

        # 修改密碼
        user.password = make_password(password)
        user.save()

        # 刪除已使用的驗證碼
        cache.delete(f"verification_code_{email_hash}")

        return Response({
            "message": "密碼重設成功",
            "data": None
        }, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')


# -----------------------------
# 刪除帳號
# -----------------------------
class DeleteAccount(APIView):
    """
    POST /auth/delete_account/ - 永久刪除帳號
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data["password"]
        if not password:
            return Response({
                "message": "缺少必要參數",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')
        if not request.user.check_password(password):
            return Response({
                "message": "密碼錯誤",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json; charset=utf-8')
        request.user.delete()
        return Response({
            "message": "帳號已成功刪除",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT, content_type='application/json; charset=utf-8')


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
        }, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')

    def put(self, request):
        new_name = request.data.get("new_name", "").strip()
        if not new_name:
            return Response({
                "message": "缺少必要參數",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')
        serializer = UserDetailSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "用戶資料更新成功",
                "data": serializer.data
            }, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response({
            "message": "資料驗證失敗",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')
