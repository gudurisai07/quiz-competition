#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting Render Start Process..."

cd quiz_project

echo "Running Database Migrations..."
# This guarantees tables exist, whether using PostgreSQL or fallback SQLite
python manage.py migrate

echo "Starting Gunicorn Server..."
gunicorn quiz_project.wsgi:application
