#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for postgres..."
# This is a simple loop to wait for the DB port to be open
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Run migrations
echo "Applying migrations..."
python manage.py migrate --noinput --settings=task_hive.settings.prod

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=task_hive.settings.prod

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn task_hive.wsgi:application --bind 0.0.0.0:8000 --workers 3
