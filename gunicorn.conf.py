"""Gunicorn configuration for Render deployment."""

import multiprocessing

# Use gthread worker so a single worker can handle multiple
# concurrent requests (crucial on Render free tier where
# WEB_CONCURRENCY is forced to 1).
worker_class = "gthread"
threads = 4

# Timeout: Render's health-check + cold starts need headroom.
timeout = 120
graceful_timeout = 30

# Keep-alive helps when behind Render's reverse proxy.
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
