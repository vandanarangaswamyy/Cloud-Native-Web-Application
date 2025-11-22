# api/db_timing.py
import time
from django.db import connection
from .metrics import statsd

class DBTimingWrapper:
    """Wrap every SQL execution and record timing + count metrics."""
    def __init__(self, execute, sql, params, many, context):
        self.execute = execute
        self.sql = sql
        self.params = params
        self.many = many
        self.context = context

    def __call__(self, *args, **kwargs):
        start = time.perf_counter()
        try:
            return self.execute(*args, **kwargs)
        finally:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            # Track query latency in milliseconds
            statsd.timing("db.query.latency_ms", elapsed_ms)
            # Increment query count
            statsd.incr("db.query.count")

# Hook the wrapper once at app startup
connection.execute_wrapper(DBTimingWrapper)
