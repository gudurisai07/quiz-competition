#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting Render Build Process..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
cd quiz_project
python manage.py collectstatic --no-input

echo "Build Process Complete!"
