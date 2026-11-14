"""Tiny cache-backed rate limiting shared by login, sign-up and click recording.

ponytail: uses Django's default cache (LocMem = per worker process, evictable). Configure a shared
CACHES backend (database or Redis) in production for limits that hold across workers.
"""
from django.conf import settings
from django.core.cache import cache


def client_ip(request):
    """The connecting client's address.

    X-Forwarded-For is client-controlled, so it is only read when TRUSTED_PROXY_COUNT proxies are known to sit in
    front of the app; then the entry appended by the outermost trusted proxy is used. Default: REMOTE_ADDR only.
    """
    proxies = getattr(settings, 'TRUSTED_PROXY_COUNT', 0)
    if proxies:
        hops = [h.strip() for h in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',') if h.strip()]
        if len(hops) >= proxies:
            return hops[-proxies]
    return request.META.get('REMOTE_ADDR', '')


def hits(key):
    return cache.get(key, 0)


def hit(key, window_seconds):
    """Increment a counter that expires window_seconds after its first hit; returns the new count."""
    cache.add(key, 0, window_seconds)
    try:
        return cache.incr(key)
    except ValueError:  # expired between add() and incr()
        cache.set(key, 1, window_seconds)
        return 1
