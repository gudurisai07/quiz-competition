#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations (use quiz_project subfolder if needed)
# Since manage.py is in quiz_project, we need to cd or point to it
cd quiz_project
python manage.py collectstatic --no-input
python manage.py migrate
