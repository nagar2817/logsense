#!/bin/sh
set -eu

APP_MODULE="app.core.celery_app.celery_app"
QUEUE="default"
LOG_LEVEL="info"
CONCURRENCY="2"
HOSTNAME="worker@%h"

exec celery \
  -A "$APP_MODULE" \
  worker \
  -Q "$QUEUE" \
  --loglevel "$LOG_LEVEL" \
  --concurrency "$CONCURRENCY" \
  --hostname "$HOSTNAME"
