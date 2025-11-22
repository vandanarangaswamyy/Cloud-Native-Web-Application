import logging
import time
from django.utils.deprecation import MiddlewareMixin
from .metrics import statsd


# -----------------------------
# Metrics Middleware
# -----------------------------
class MetricsMiddleware(MiddlewareMixin):
    """
    Emits latency and count metrics for each endpoint to CloudWatch via StatsD.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.start_time = time.perf_counter()

    def process_response(self, request, response):
        if hasattr(request, "start_time"):
            latency = (time.perf_counter() - request.start_time) * 1000
            path = request.path.lower().rstrip('/')
            method = request.method.upper()

            # Normalize path for metric names
            if path == "/healthz":
                metric_name = "healthz"
            elif path.startswith("/v1/user"):
                metric_name = "user"
            elif path.startswith("/v1/product"):
                metric_name = "product"
            else:
                metric_name = path.strip('/').replace('/', '_') or "root"

            statsd.timing(f"csye6225.api.{metric_name}.latency_ms", latency)
            statsd.incr(f"csye6225.api.{metric_name}.count")

        return response


# -----------------------------
# Logging Middleware
# -----------------------------
logger = logging.getLogger("webapp")

class RequestLoggingMiddleware:
    """
    Logs INFO, WARNING, and ERROR messages depending on HTTP response code.
    INFO: 2xx–3xx  |  WARNING: 4xx  |  ERROR: 5xx
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        method = request.method
        path = request.path
        status = response.status_code

        message = f"{method} {path} -> {status} ({elapsed_ms} ms)"

        if 200 <= status < 400:
            logger.info(message)
        elif status in (400, 403):
            logger.error(message)  # Auth failures = security events
        elif 400 <= status < 500:
            logger.warning(message)
        elif 500 <= status < 600:
            logger.error(message)

        # Optional: emit metrics for response codes
        statsd.incr(f"csye6225.http.{status}")
        statsd.timing(f"csye6225.http.{status}.latency_ms", elapsed_ms)

        return response