import os
import django

# Django setup must run before importing any components that import models or settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rag_app.settings")
django.setup()

from chat.main import app
