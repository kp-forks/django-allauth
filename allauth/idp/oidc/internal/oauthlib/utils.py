from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from urllib.parse import urlparse, urlunparse

from django.core.exceptions import PermissionDenied
from django.forms import Form
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from oauthlib.common import Request, quote, urlencode, urlencoded
from oauthlib.oauth2.rfc6749.errors import OAuth2Error

from allauth.account import app_settings as account_settings


if TYPE_CHECKING:
    from allauth.idp.oidc.models import Client, Token


def get_uri(request: HttpRequest) -> str:
    """
    Django considers "safe" some characters that aren't so for oauthlib.
    We have to search for them and properly escape.
    """
    parsed = list(urlparse(request.get_full_path()))
    query = parsed[4]
    encoded_query = quote(query, safe="".join(urlencoded))
    parsed[4] = encoded_query
    return urlunparse(parsed)


def extract_params(request: HttpRequest) -> tuple[str, str, str, dict[str, str]]:
    uri = get_uri(request)
    body: str = urlencode(request.POST.items())
    headers = extract_headers(request)
    if request.method is None:
        raise ValueError(request.method)
    return uri, request.method, body, headers


def extract_headers(request: HttpRequest) -> dict[str, str]:
    """
    You need to define extract_params and make sure it does not include file
    like objects waiting for input. In Django this is request.META['wsgi.input']
    and request.META['wsgi.errors']
    """
    headers = request.META.copy()
    headers.pop("wsgi.input", None)
    headers.pop("wsgi.errors", None)
    if "HTTP_AUTHORIZATION" in headers:
        headers["Authorization"] = headers["HTTP_AUTHORIZATION"]
    if "HTTP_ORIGIN" in headers:
        headers["Origin"] = headers["HTTP_ORIGIN"]
    if "CONTENT_TYPE" in headers:
        headers["Content-Type"] = headers["CONTENT_TYPE"]
    return headers


def convert_response(headers, body, status) -> HttpResponse:
    response: HttpResponse
    if isinstance(body, dict):
        response = JsonResponse(body, status=status)
    else:
        response = HttpResponse(content=body, status=status)
    for k, v in headers.items():
        response[k] = v
    return response


def respond_html_error(
    request: HttpRequest,
    *,
    error: OAuth2Error | None = None,
    form: Form | None = None,
) -> HttpResponse:
    context = {"error": error, "error_form": form}
    return render(
        request,
        f"idp/oidc/error.{account_settings.TEMPLATE_EXTENSION}",
        context,
    )


def respond_json_error(request: HttpRequest, error: OAuth2Error) -> HttpResponse:
    response = HttpResponse(
        error.json, status=error.status_code, content_type="application/json"
    )
    for k, v in error.headers.items():
        response[k] = v
    return response


@dataclass
class ValidationContext:
    email: str | None = None
    access_token: Token | None = None
    refresh_token: Token | None = None
    clients: dict[str, Client | None] = field(default_factory=dict)
    codes: dict[tuple[str, str], dict | None] = field(default_factory=dict)


def get_context(request: Request) -> ValidationContext:
    """
    oathlib documents `Request` as:

    > A malleable representation of a signable HTTP request

    Within allauth, as part of request validation, we need to collect various state.
    When assigning using `request.foo = ...`, we are at risk of mixing `foo` as a local
    state variable vs a `?foo="bar"` get parameter. Therefore, we put our own variables
    in a separate validation context.
    """
    key = "_allauth_context"
    ctx = getattr(request, key, None)
    if key in request._params or (
        ctx is not None and not isinstance(ctx, ValidationContext)
    ):
        raise PermissionDenied
    if ctx is None:
        ctx = ValidationContext()
        setattr(request, key, ctx)
    return ctx
