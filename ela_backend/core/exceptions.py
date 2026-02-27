# core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # 先確認 response 再存取屬性
    if response is None:
        return response

    response.content_type = 'application/json; charset=utf-8'

    # 帳號被封鎖：優先用 exception code 判斷，若沒有 code 再退回文字比對
    if isinstance(exc, AuthenticationFailed):
        exc_code = getattr(exc, 'code', None)
        exc_detail = getattr(exc, 'detail', None)
        detail_str = str(exc_detail) if exc_detail is not None else ''

        if exc_code == 'user_inactive' or '停用' in detail_str or 'inactive' in detail_str.lower():
            response.data = {"message": "此帳號已被停用"}
            response.status_code = 403
            return response

    # 未提供認證
    if isinstance(exc, NotAuthenticated):
        response.data = {"message": "未提供認證"}
        response.status_code = 401
        return response

    # 權限不足
    if isinstance(exc, PermissionDenied):
        response.data = {"message": str(exc.detail)}
        response.status_code = 403
        return response

    # Token 無效或過期
    if isinstance(exc, (InvalidToken, TokenError)):
        response.data = {"message": "Token 無效或過期"}
        response.status_code = 401
        return response

    return response
