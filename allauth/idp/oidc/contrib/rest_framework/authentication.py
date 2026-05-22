from __future__ import annotations

from django.http import HttpRequest

from rest_framework.authentication import BaseAuthentication

from allauth.idp.oidc.internal.oauthlib.server import get_server
from allauth.idp.oidc.internal.oauthlib.utils import extract_params, get_context


class TokenAuthentication(BaseAuthentication):
    """
    Use the OIDC access token to authenticate the request.
    """

    def authenticate(self, request: HttpRequest):
        server = get_server()
        orequest = extract_params(request)
        valid, ctx = server.verify_request(*orequest, scopes=[])
        if not valid:
            return None
        access_token = get_context(ctx).access_token
        return ctx.user, access_token
