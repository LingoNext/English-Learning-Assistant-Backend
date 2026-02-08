"""
支援基於 IP 地址和裝置 ID 的請求頻率控制
"""
import time
import hashlib
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response


def get_client_ip(request):
    """
    獲取客戶端真實 IP 地址
    支援反向代理和負載均衡器的 IP 獲取
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_id_from_request(request):
    """
    從請求中獲取裝置 ID
    支援多種來源：Header、POST 數據、Cookie

    Args:
        request: Django 請求對象

    Returns:
        str: 裝置 ID 或 None
    """
    # 優先級：Header > POST 數據 > Cookie
    device_id = (
            request.META.get('HTTP_X_DEVICE_ID') or
            (request.data.get('device_id') if hasattr(request, 'data') else None) or
            request.POST.get('device_id') or
            request.COOKIES.get('device_id')
    )

    return device_id


def generate_device_fingerprint(request):
    """
    基於請求特徵生成裝置指紋

    Args:
        request: Django 請求對象

    Returns:
        str: 裝置指紋
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')

    # 組合指紋信息
    fingerprint_data = f"{user_agent}_{accept_language}_{accept_encoding}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]


def get_or_create_device_id(request):
    """
    獲取或創建裝置 ID
    優先使用明確提供的 device_id，否則生成指紋

    Args:
        request: Django 請求對象

    Returns:
        str: 裝置 ID
    """
    device_id = get_device_id_from_request(request)

    if not device_id:
        device_id = generate_device_fingerprint(request)

    return device_id


def create_rate_limit_key(ip_address, action_type):
    """
    創建速率限制的緩存鍵（舊版本，保持向後兼容）

    Args:
        ip_address: 客戶端 IP 地址
        action_type: 操作類型（如 'email_send'）

    Returns:
        str: 緩存鍵
    """
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    return f"rate_limit_{action_type}_{ip_hash}"


def create_enhanced_rate_limit_key(request, action_type):
    """
    創建增強版速率限制的緩存鍵
    結合用戶ID、裝置ID和IP地址的多層識別

    Args:
        request: Django 請求對象
        action_type: 操作類型（如 'email_send'）

    Returns:
        str: 緩存鍵
    """
    # 已登錄用戶：優先使用用戶 ID
    if hasattr(request, 'user') and request.user.is_authenticated:
        return f"rate_limit_{action_type}_user_{request.user.id}"

    # 未登錄用戶：使用裝置 ID
    device_id = get_or_create_device_id(request)
    if device_id:
        return f"rate_limit_{action_type}_device_{device_id}"

    # 降級到 IP（原有方式）
    ip_address = get_client_ip(request)
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    return f"rate_limit_{action_type}_ip_{ip_hash}"


class RateLimitExceeded(Exception):
    """速率限制異常"""

    def __init__(self, message, retry_after=None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


def check_rate_limit(request, action_type, max_requests, time_window):
    """
    增強版速率限制檢查
    基於用戶ID、裝置ID或IP地址進行限制

    Args:
        request: Django 請求對象
        action_type: 操作類型
        max_requests: 最大請求數
        time_window: 時間窗口（秒）

    Returns:
        dict: 包含是否允許、剩餘請求數、重置時間等信息

    Raises:
        RateLimitExceeded: 當超過速率限制時
    """
    cache_key = create_enhanced_rate_limit_key(request, action_type)

    # 使用滑動窗口算法
    current_time = int(time.time())

    # 獲取當前時間窗口內的請求記錄
    request_data = cache.get(cache_key, {
        'requests': [],
        'window_start': current_time
    })

    # 清理過期的請求記錄
    cutoff_time = current_time - time_window
    request_data['requests'] = [
        req_time for req_time in request_data['requests']
        if req_time > cutoff_time
    ]

    # 檢查是否超過限制
    current_requests = len(request_data['requests'])

    if current_requests >= max_requests:
        # 計算重置時間
        oldest_request = min(request_data['requests']) if request_data['requests'] else current_time
        retry_after = max(1, oldest_request + time_window - current_time)

        # 獲取識別類型用於錯誤消息
        if hasattr(request, 'user') and request.user.is_authenticated:
            limit_type = "用戶"
        elif get_device_id_from_request(request):
            limit_type = "裝置"
        else:
            limit_type = "IP地址"

        raise RateLimitExceeded(
            message=f"{limit_type}請求頻率過高，請 {retry_after} 秒後重試",
            retry_after=retry_after
        )

    # 記錄本次請求
    request_data['requests'].append(current_time)

    # 更新緩存，設置過期時間為時間窗口的兩倍以確保數據完整性
    cache.set(cache_key, request_data, timeout=time_window * 2)

    return {
        'allowed': True,
        'remaining': max_requests - len(request_data['requests']),
        'reset_time': current_time + time_window,
        'retry_after': 0
    }




def email_rate_limit_v2(view_func):
    """
    新版郵件發送專用速率限制裝飾器（使用 check_rate_limit）
    支援基於用戶ID、裝置ID和IP地址的多層識別
    - 10 秒內只能發送 1 次
    - 1 小時內最多 5 次請求
    """
    def decorator(self, request, *args, **kwargs):
        try:
            # 檢查 10 秒限制
            check_rate_limit(request, 'email_send_10s', max_requests=1, time_window=10)

            # 檢查 1 小時限制
            rate_info = check_rate_limit(request, 'email_send_1h', max_requests=5, time_window=3600)

            # 執行原始視圖函數
            response = view_func(self, request, *args, **kwargs)

            # 添加速率限制響應頭（使用較嚴格的限制）
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = '1/10s, 5/1h'
                response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(rate_info['reset_time'])

            return response

        except RateLimitExceeded as e:
            return Response({
                "message": e.message,
                "data": None,
                "rate_limit_info": {
                    "retry_after": e.retry_after,
                    "limits": "1 request per 10 seconds, 5 requests per hour"
                }
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            content_type='application/json; charset=utf-8',
            headers={
                'Retry-After': str(e.retry_after),
                'X-RateLimit-Limit': '1/10s, 5/1h',
                'X-RateLimit-Remaining': '0'
            })

    return decorator


def general_rate_limit(max_requests, time_window, action_type=None):
    """
    通用速率限制裝飾器
    支援基於用戶ID、裝置ID和IP地址的多層識別

    Args:
        max_requests: 最大請求數
        time_window: 時間窗口（秒）
        action_type: 操作類型，如果未指定則使用視圖函數名
    """

    def decorator(view_func):
        def wrapper(self, request, *args, **kwargs):
            nonlocal action_type
            if action_type is None:
                action_type = view_func.__name__

            try:
                # 檢查速率限制
                rate_info = check_rate_limit(request, action_type, max_requests, time_window)

                # 執行原始視圖函數
                response = view_func(self, request, *args, **kwargs)

                # 添加速率限制響應頭
                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = f'{max_requests}/{time_window}s'
                    response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                    response.headers['X-RateLimit-Reset'] = str(rate_info['reset_time'])

                return response

            except RateLimitExceeded as e:
                return Response({
                    "message": e.message,
                    "data": None,
                    "rate_limit_info": {
                        "retry_after": e.retry_after,
                        "limits": f"{max_requests} requests per {time_window} seconds"
                    }
                },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    content_type='application/json; charset=utf-8',
                    headers={
                        'Retry-After': str(e.retry_after),
                        'X-RateLimit-Limit': f'{max_requests}/{time_window}s',
                        'X-RateLimit-Remaining': '0'
                    })

        return wrapper

    return decorator
