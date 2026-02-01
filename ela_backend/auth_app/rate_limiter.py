"""
支援基於 IP 地址的請求頻率控制
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


def create_rate_limit_key(ip_address, action_type):
    """
    創建速率限制的緩存鍵

    Args:
        ip_address: 客戶端 IP 地址
        action_type: 操作類型（如 'email_send'）

    Returns:
        str: 緩存鍵
    """
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    return f"rate_limit_{action_type}_{ip_hash}"


class RateLimitExceeded(Exception):
    """速率限制異常"""
    def __init__(self, message, retry_after=None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


def check_rate_limit(ip_address, action_type, max_requests, time_window):
    """
    檢查是否超過速率限制

    Args:
        ip_address: 客戶端 IP 地址
        action_type: 操作類型
        max_requests: 最大請求數
        time_window: 時間窗口（秒）

    Returns:
        dict: 包含是否允許、剩餘請求數、重置時間等信息

    Raises:
        RateLimitExceeded: 當超過速率限制時
    """
    cache_key = create_rate_limit_key(ip_address, action_type)

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

        raise RateLimitExceeded(
            message=f"請求頻率過高，請 {retry_after} 秒後重試",
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


def email_rate_limit(view_func):
    """
    郵件發送專用速率限制裝飾器
    - 10 秒內只能發送 1 次
    - 1 小時內最多 5 次請求
    """
    def decorator(self, request, *args, **kwargs):
        try:
            ip_address = get_client_ip(request)

            # 檢查 10 秒限制
            check_rate_limit(ip_address, 'email_send_10s', max_requests=1, time_window=10)

            # 檢查 1 小時限制
            rate_info = check_rate_limit(ip_address, 'email_send_1h', max_requests=5, time_window=3600)

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
