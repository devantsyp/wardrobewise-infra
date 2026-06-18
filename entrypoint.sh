#!/bin/sh
set -e

python manage.py migrate --no-input
exec gunicorn laundry_advisor.wsgi:application --bind 0.0.0.0:8000 --workers 2
