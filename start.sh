#!/bin/bash
set -e  # Exit on error

echo "========================================" >&2
echo "STARTING DEPLOYMENT SCRIPT" >&2
echo "========================================" >&2

# Run database migrations
echo "Running migrations..." >&2
python manage.py migrate --noinput 2>&1

# Collect static files
echo "Collecting static files..." >&2
python manage.py collectstatic --noinput 2>&1

# Start gunicorn with error logging
echo "Starting server..." >&2
exec gunicorn retirement_planner.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    --capture-output
