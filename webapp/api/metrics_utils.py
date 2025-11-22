# api/metrics_utils.py
import time
from .metrics import statsd

def record_api_metrics(metric_key):
    """Decorator to record API latency and count for specific endpoints."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                statsd.timing(f"csye6225.api.{metric_key}.latency_ms", elapsed_ms)
                statsd.incr(f"csye6225.api.{metric_key}.count")
        return wrapper
    return decorator
