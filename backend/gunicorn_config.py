# Gunicorn configuration for production
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:" + str(os.getenv("PORT", "5001"))
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'user_management_system'

# Static files
static_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
static_url = '/static/'

# SSL
keyfile = None
certfile = None

