import time
import threading
import os

# Simple in-memory rate limiter (per provider+account)
_counters = {}
_lock = threading.Lock()
WINDOW = 60  # seconds
DEFAULT_LIMIT = int(os.environ.get('RATE_LIMIT_PER_MIN', '30'))


def allow_send(provider, account_id, count=1):
    """Return True if `count` messages can be sent now for (provider,account_id)."""
    key = (provider, account_id)
    now = time.time()
    with _lock:
        arr = _counters.get(key, [])
        # drop old
        arr = [t for t in arr if now - t < WINDOW]
        # sum current
        if len(arr) + count > DEFAULT_LIMIT:
            return False
        # record timestamps for the new sends
        arr.extend([now] * count)
        _counters[key] = arr
        return True


def remaining_quota(provider, account_id):
    key = (provider, account_id)
    now = time.time()
    with _lock:
        arr = _counters.get(key, [])
        arr = [t for t in arr if now - t < WINDOW]
        return max(0, DEFAULT_LIMIT - len(arr))
