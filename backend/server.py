"""ASGI entry point for the Django Sagarmatha College ERP.

Supervisor runs `uvicorn server:app` in this directory; we expose the Django
ASGI application here so the same code base serves both the `/api/*` ingress
route (port 8001) and the rest of the app via the proxy on port 3000.
"""
import os
import sys
from pathlib import Path

# Make the project root importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "college_management_system.settings")
os.environ.setdefault("ALLOWED_HOSTS", "*")
os.environ.setdefault("DEBUG", "True")

from django.core.asgi import get_asgi_application  # noqa: E402

app = get_asgi_application()
