from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    NotAuthenticated,
    PermissionDenied,
    ValidationError
)
from rest_framework_simplejwt.exceptions import (
    InvalidToken,
    TokenError,
    AuthenticationFailed
)
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {
                "message": "server_error",
                "errors": {
                    "detail": str(exc)
                },
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type="application/json; charset=utf-8"
        )

    if isinstance(exc, ValidationError):
        return Response(
            {
                "message": "validation_error",
                "errors": response.data,
                "status_code": response.status_code
            },
            status=response.status_code,
            content_type="application/json; charset=utf-8"
        )

    if isinstance(exc, NotAuthenticated):
        return Response(
            {
                "message": "not_authenticated",
                "errors": {
                    "detail": "未提供認證"
                },
                "status_code": 401
            },
            status=401,
            content_type="application/json; charset=utf-8"
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {
                "message": "permission_denied",
                "errors": {
                    "detail": str(exc.detail)
                },
                "status_code": 403
            },
            status=403,
            content_type="application/json; charset=utf-8"
        )

    if isinstance(exc, (InvalidToken, TokenError)):
        return Response(
            {
                "message": "invalid_token",
                "errors": {
                    "detail": "Token 無效或過期"
                },
                "status_code": 401
            },
            status=401,
            content_type="application/json; charset=utf-8"
        )

    if isinstance(exc, AuthenticationFailed):
        detail_str = str(getattr(exc, "detail", ""))

        # account disabled special case
        if "inactive" in detail_str.lower() or "停用" in detail_str:
            return Response(
                {
                    "message": "account_disabled",
                    "errors": {
                        "detail": "此帳號已被停用"
                    },
                    "status_code": 403
                },
                status=403,
                content_type="application/json; charset=utf-8"
            )

        return Response(
            {
                "message": "authentication_failed",
                "errors": {
                    "detail": detail_str
                },
                "status_code": 401
            },
            status=401,
            content_type="application/json; charset=utf-8"
        )

    return Response(
        {
            "message": "error",
            "errors": response.data,
            "status_code": response.status_code
        },
        status=response.status_code,
        content_type="application/json; charset=utf-8"
    )