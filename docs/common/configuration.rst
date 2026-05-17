Configuration
=============

Available settings:

``ALLAUTH_DEFAULT_AUTO_FIELD``
  Can be set to configure the primary key of all models. For
  example: ``"hashid_field.HashidAutoField"``.

``ALLAUTH_RATE_LIMIT_IPV6_PREFIX`` (default: ``64``)
  For rate limiting purposes, IPv6 addresses are truncated to their network
  prefix to prevent attackers from bypassing rate limits by rotating through
  addresses within their allocated prefix. This setting controls the prefix
  length. The default of 64 corresponds to a standard /64 subnet.

``ALLAUTH_USER_CODE_FORMAT`` (default: ``{"numeric": False, "dashed": True, length: 8}``)
  Controls the format of user-facing verification codes (e.g. email
  verification, phone verification, login codes).
