from statsd import StatsClient
statsd = StatsClient(host='localhost', port=8125, prefix='csye6225')

import time
from django.db.backends.signals import connection_created

def instrument_db():
    def wrapper(sender, connection, **kwargs):
        original_execute = connection.cursor().execute

        def timed_execute(self, sql, params=None):
            start = time.perf_counter()
            try:
                return original_execute(self, sql, params)
            finally:
                duration = (time.perf_counter() - start) * 1000
                statsd.timing('db.query.time_ms', duration)

        connection.cursor().execute = timed_execute

    connection_created.connect(wrapper)

instrument_db()
