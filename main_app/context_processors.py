from django.conf import settings


def firebase_settings(request):
    """Expose non-secret firebase config values to templates.

    Do NOT expose server-only secrets (like FCM server key) here.
    """
    return {
        "FIREBASE_CONFIG": getattr(settings, "FIREBASE_CONFIG", {}),
    }
