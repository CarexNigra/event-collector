#!/bin/bash

# NOTE: This is a program that opens a process to host "app.py" server, 
# and listn to the port 8000 for the messages sent via curl

gunicorn --config config/gunicorn.py \
    --bind 0.0.0.0:8000 api.api:app \
    --timeout "${GUNICORN_TIMEOUT}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT}" \
    --workers "${GUNICORN_WORKERS}" \
    --max-requests "${GUNICORN_MAX_REQUESTS}" \
    --keep-alive "${GUNICORN_KEEP_ALIVE}" \
    --worker-class uvicorn.workers.UvicornWorker 