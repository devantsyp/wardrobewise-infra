import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.generic.base import RedirectView

logger = logging.getLogger(__name__)


def healthz(request):
    """Liveness + readiness check for uptime monitoring.

    Returns 200 only if the app can reach the database; 503 otherwise, so an
    external monitor catches a dead Postgres even while Django itself is up.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except DatabaseError:
        logger.exception('Health check failed: database unreachable')
        return JsonResponse({'status': 'error', 'database': 'unreachable'}, status=503)
    return JsonResponse({'status': 'ok', 'database': 'ok'})


class FaviconRedirect(RedirectView):
    """Browsers and crawlers request /favicon.ico directly; point them at the
    hashed static file. Resolved per request (not at import time) so a missing
    static manifest can only break this URL, never the whole site."""

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return static('favicon.ico')


def index(request):
    return render(request, 'core/index.html')
