import threading
import time
import logging
from typing import Optional

from django.utils.deprecation import MiddlewareMixin

_logger = logging.getLogger(__name__)

_thread_locals = threading.local()


def set_request_context(user=None, ip_address=None, session_key=None):
    _thread_locals.user = user
    _thread_locals.ip_address = ip_address
    _thread_locals.session_key = session_key


def get_request_user():
    return getattr(_thread_locals, 'user', None)


def get_request_ip():
    return getattr(_thread_locals, 'ip_address', None)


def get_request_session_key():
    return getattr(_thread_locals, 'session_key', None)


class RequestContextMiddleware(MiddlewareMixin):
    """Capture client IP, session key, user, and request duration.
    Exposes them via thread-local helpers for signals/handlers to consume.
    """

    header_candidates = (
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP',
        'REMOTE_ADDR',
    )

    def _client_ip(self, request) -> Optional[str]:
        for h in self.header_candidates:
            if h in request.META:
                val = request.META[h]
                if h == 'HTTP_X_FORWARDED_FOR' and ',' in val:
                    # First IP in the list
                    val = val.split(',')[0].strip()
                return val
        return None

    def process_request(self, request):
        request._rt_start = time.perf_counter()
        ip = self._client_ip(request)
        session_key = getattr(request.session, 'session_key', None)
        set_request_context(getattr(request, 'user', None), ip, session_key)

    def process_response(self, request, response):
        try:
            duration_ms = None
            if hasattr(request, '_rt_start'):
                duration_ms = int((time.perf_counter() - request._rt_start) * 1000)
            user = getattr(request, 'user', None)
            ip = self._client_ip(request)
            path = getattr(request, 'path', '-')
            method = getattr(request, 'method', '-')
            status = getattr(response, 'status_code', '-')
            _logger.info(
                'request %s %s %s user=%s ip=%s duration_ms=%s',
                method, path, status,
                getattr(user, 'username', 'anon') if user else 'anon',
                ip,
                duration_ms,
            )
        finally:
            # Always clear thread locals after response to avoid leaks
            set_request_context(None, None, None)
        return response
