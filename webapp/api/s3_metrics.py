# api/s3_metrics.py
import time,os
import boto3
from .metrics import statsd
from django.conf import settings

s3_client = boto3.client("s3")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")

def timed_s3_call(func, op_name: str):
    """
    Measures and publishes S3 operation latency to CloudWatch via StatsD.
    Example:
        timed_s3_call(lambda: s3_client.put_object(...), "put_object")
    """
    start = time.perf_counter()
    try:
        return func()
    finally:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        statsd.timing(f"csye6225.s3.{op_name}.latency_ms", elapsed_ms)


def upload_image_to_s3(file_obj, key):
    """Uploads an image and records S3 upload latency metric."""
    bucket = settings.S3_BUCKET
    return timed_s3_call(
        lambda: s3_client.put_object(Bucket=bucket, Key=key, Body=file_obj),
        "upload"
    )
