"""
WSGI config for quiz_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')

# Automatically run migrations when deployed on Render
if os.environ.get('RENDER'):
    try:
        from django.core.management import call_command
        import traceback
        print("Running automatic database migrations on Render startup...")
        call_command('migrate', interactive=False)
        print("Running automatic collectstatic on Render startup...")
        call_command('collectstatic', interactive=False, clear=False)
        print("Startup processes completed successfully.")
    except Exception as e:
        print(f"Failed to run automatic startup processes: {e}")
        traceback.print_exc()

application = get_wsgi_application()
