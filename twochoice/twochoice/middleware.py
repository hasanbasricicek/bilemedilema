import time

from django.conf import settings
from django.db import connection


class RequestProfilingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, 'DEBUG', False) or request.GET.get('profile') != '1':
            return self.get_response(request)

        start = time.perf_counter()
        start_queries = len(connection.queries)

        response = self.get_response(request)

        duration_ms = int(round((time.perf_counter() - start) * 1000.0))
        db_queries = max(0, len(connection.queries) - start_queries)

        try:
            response['X-Profile-Duration-Ms'] = str(duration_ms)
            response['X-Profile-DB-Queries'] = str(db_queries)
        except Exception:
            pass

        return response
