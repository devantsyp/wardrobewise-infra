#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Download Tailwind CLI binary and build CSS
python manage.py tailwind download_cli
python manage.py tailwind build

# Remove Tailwind source CSS before collectstatic — WhiteNoise cannot resolve
# @import "tailwindcss" (v4 syntax) and will fail with MissingFileError
rm -rf assets/src/

# Collect static files (AFTER Tailwind build so compiled CSS is included)
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate
