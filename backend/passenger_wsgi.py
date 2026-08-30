"""cPanel/Passenger entry point.

Passenger's Python support expects a WSGI callable named `application`.
FastAPI is ASGI, so it's wrapped with a2wsgi rather than served directly.
"""

from a2wsgi import ASGIMiddleware

from main import app as _asgi_app

application = ASGIMiddleware(_asgi_app)
