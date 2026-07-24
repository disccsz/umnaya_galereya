from prometheus_client import Counter, Histogram

photos_uploaded_total = Counter(
    "photos_uploaded_total", "Total photos uploaded",
)

http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration",
    ["method", "path", "status_code"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0),
)

storage_upload_errors_total = Counter(
    "storage_upload_errors_total", "MinIO upload errors",
    ["error_code"],
)

kafka_publish_errors_total = Counter(
    "kafka_publish_errors_total", "Kafka publish errors",
    ["topic"],
)
