Dynamic Client Registration
===========================

Support for Dynamic Client Registration (`RFC 7591
<https://www.rfc-editor.org/rfc/rfc7591>`_) can be turned on via
``IDP_OIDC_DCR_ENABLED``.  Once enabled, clients can register themselves by
POSTing their metadata to ``/identity/o/api/clients``.

Whether or not creating clients requires authorization is configurable via
``IDP_OIDC_DCR_REQUIRES_INITIAL_ACCESS_TOKEN``, which is ``True`` by default.
When authorization is enabled, the bearer token from the ``Authorization: Bearer
<token>`` header will be used to lookup a token
(``allauth.idp.oidc.models.Token``) of type ``Token.Type.INITIAL_ACCESS_TOKEN``.

The DCR specification does not specify anything about the lifetime of the
initial access token, neither does the allauth implementation. If you want to
enforce specific rules, such as limiting the number of times the token can
be used, you can inspect and manipulate the token in the
``validate_client_registration()`` adapter hook.
