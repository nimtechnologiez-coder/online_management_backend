import os

# Gunicorn configuration for large video uploads
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 600))
keepalive = 5
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
max_requests = 1000
max_requests_jitter = 50
