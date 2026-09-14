Username Matching
=================

Comparison Rules
----------------

Usernames are compared after applying Python's ``str.lower()``. Thus, ``admin``
and ``ADMIN`` identify the same account, whereas ``admin`` and ``ádmin`` do not.
No other Unicode normalization is applied. Preserving username casing
(``ACCOUNT_PRESERVE_USERNAME_CASING = True``) only affects storage and display,
not authentication.

Ensure you use ``allauth.account.auth_backends.AuthenticationBackend`` for
authentication. Django's ``ModelBackend`` and custom authentication backends may
rely solely on database matching and thereby apply different equality
rules. Custom backends should apply the same comparison before checking the
password.


Database Collations
-------------------

The username column should use a collation compatible with the equality rules
above: case-insensitive, but accent-sensitive. If the database uses broader
rules, as is the case with accent-insensitive collations, it may consider
otherwise distinct usernames equal. Such database matches are filtered during
authentication, and colliding usernames are rejected during registration.
Consequently, usernames such as ``admin`` and ``ádmin`` cannot coexist when the
database itself considers them equal.

A typical PostgreSQL setup is compatible with these requirements. MySQL and
MariaDB require more attention because commonly used default collations are
accent-insensitive.  Choose an accent-sensitive collation if usernames that
differ only by accents must be able to coexist.
