from __future__ import annotations

from django.http import HttpRequest

from ninja.security.base import AuthBase

from allauth.idp.oidc.internal.oauthlib.server import get_server
from allauth.idp.oidc.internal.oauthlib.utils import extract_params, get_context
from allauth.idp.oidc.internal.scope import is_scope_granted


class TokenAuth(AuthBase):
    """
    Use the OIDC access token to authenticate and the scopes attached to the
    token to authorize the request.
    """

    openapi_type: str = "apiKey"
    scope = None

    def __init__(self, scope: str | list | dict) -> None:
        """The scope passed can either be:

        - a single scope (``str``),
        - a list of scopes, all of which should be granted.
        - a list of scope lists. Your token should match at least all scopes of one of the scope lists.
        - A dictionary, with the request method (e.g. ``GET``) as key, and one
          of the scope values from the previous bullet. The scopes to match are
          then dynamically selected based on the request.
        """
        super().__init__()
        self.scope = scope

    def __call__(self, request: HttpRequest):
        server = get_server()
        orequest = extract_params(request)
        valid, ctx = server.verify_request(*orequest, scopes=[])
        if not valid:
            return None
        access_token = get_context(ctx).access_token
        if not is_scope_granted(self.scope, access_token, request.method):
            return None
        if access_token and access_token.user:
            request.user = access_token.user
        return access_token
