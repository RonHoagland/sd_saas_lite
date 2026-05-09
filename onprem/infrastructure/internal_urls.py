# infrastructure/internal_urls.py
# Stabilize-only scope marker:
# Internal API routing surface is intentionally frozen as a placeholder in this
# phase. Middleware-level auth and path wiring remain active, but endpoint
# implementation is deferred until an explicit contract/build phase.

from django.urls import path

urlpatterns: list = []
