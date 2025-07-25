import importlib
import json
import os
import random
import re
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock, PropertyMock, patch

from django.contrib.auth import get_user_model
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import clear_url_caches, set_urlconf

import pytest

from allauth.account.models import EmailAddress
from allauth.account.utils import user_email, user_pk_to_url_str, user_username
from allauth.core import context
from allauth.socialaccount.internal import statekit
from allauth.socialaccount.providers.base.constants import AuthProcess


def pytest_collection_modifyitems(config, items):
    if config.getoption("--ds") == "tests.projects.headless_only.settings":
        removed_items = []
        for item in items:
            if not item.location[0].startswith("tests/apps/headless"):
                removed_items.append(item)
        for item in removed_items:
            items.remove(item)


@pytest.fixture
def user(user_factory):
    return user_factory()


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def password_factory():
    def f():
        return str(uuid.uuid4())

    return f


@pytest.fixture
def user_password(password_factory):
    return password_factory()


@pytest.fixture
def email_verified():
    return True


@pytest.fixture
def user_factory(email_factory, db, user_password, email_verified):
    def factory(
        email=None,
        username=None,
        commit=True,
        with_email=True,
        email_verified=email_verified,
        password=None,
        phone=None,
        phone_verified=False,
        with_emailaddress=True,
        with_totp=False,
    ):
        from allauth.account.adapter import get_adapter

        if not username:
            username = uuid.uuid4().hex

        if not email and with_email:
            email = email_factory(username=username)

        User = get_user_model()
        user = User()
        if password == "!":  # nosec
            user.password = password
        else:
            user.set_password(user_password if password is None else password)
        user_username(user, username)
        user_email(user, email or "")
        if commit:
            user.save()
            if email and with_emailaddress:
                EmailAddress.objects.create(
                    user=user,
                    email=email.lower(),
                    verified=email_verified,
                    primary=True,
                )
        if with_totp:
            from allauth.mfa.totp.internal import auth

            auth.TOTP.activate(user, auth.generate_totp_secret())
        if phone:
            get_adapter().set_phone(user, phone, phone_verified)
        return user

    return factory


@pytest.fixture
def email_factory():
    def factory(username=None, email=None, mixed_case=False):
        if email is None:
            if not username:
                username = uuid.uuid4().hex
            email = f"{username}@{uuid.uuid4().hex}.org"
        if mixed_case:
            email = "".join(
                [random.choice([c.upper(), c.lower()]) for c in email]  # nosec
            )
        else:
            email = email.lower()
        return email

    return factory


@pytest.fixture
def reauthentication_bypass():
    @contextmanager
    def f():
        with patch(
            "allauth.account.internal.flows.reauthentication.did_recently_authenticate"
        ) as m:
            m.return_value = True
            yield

    return f


@pytest.fixture
def webauthn_authentication_bypass():
    @contextmanager
    def f(authenticator):
        from fido2.utils import websafe_encode

        from allauth.mfa.adapter import get_adapter

        with patch(
            "allauth.mfa.webauthn.internal.auth.WebAuthn.authenticator_data",
            new_callable=PropertyMock,
        ) as ad_m:
            with patch("fido2.server.Fido2Server.authenticate_begin") as ab_m:
                ab_m.return_value = ({}, {"state": "dummy"})
                with patch("fido2.server.Fido2Server.authenticate_complete") as ac_m:
                    with patch(
                        "allauth.mfa.webauthn.internal.auth.parse_authentication_response"
                    ) as m:
                        user_handle = (
                            get_adapter().get_public_key_credential_user_entity(
                                authenticator.user
                            )["id"]
                        )
                        authenticator_data = Mock()
                        authenticator_data.credential_data.credential_id = (
                            "credential_id"
                        )
                        ad_m.return_value = authenticator_data
                        m.return_value = Mock()
                        binding = Mock()
                        binding.credential_id = "credential_id"
                        ac_m.return_value = binding
                        yield json.dumps(
                            {"response": {"userHandle": websafe_encode(user_handle)}}
                        )

    return f


@pytest.fixture
def webauthn_registration_bypass():
    @contextmanager
    def f(user, passwordless):
        with patch("fido2.server.Fido2Server.register_complete") as rc_m:
            with patch(
                "allauth.mfa.webauthn.internal.auth.parse_registration_response"
            ) as m:
                m.return_value = Mock()

                class FakeAuthenticatorData(bytes):
                    def is_user_verified(self):
                        return passwordless

                binding = FakeAuthenticatorData(b"binding")
                rc_m.return_value = binding
                yield json.dumps(
                    {
                        "authenticatorAttachment": "cross-platform",
                        "clientExtensionResults": {"credProps": {"rk": passwordless}},
                        "id": "123",
                        "rawId": "456",
                        "response": {
                            "attestationObject": "ao",
                            "clientDataJSON": "cdj",
                            "transports": ["usb"],
                        },
                        "type": "public-key",
                    }
                )

    return f


@pytest.fixture(autouse=True)
def clear_context_request():
    context._request_var.set(None)


@pytest.fixture
def enable_cache(settings):
    from django.core.cache import cache

    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    cache.clear()
    yield


@pytest.fixture
def totp_validation_bypass():
    @contextmanager
    def f():
        with patch("allauth.mfa.totp.internal.auth.validate_totp_code") as m:
            m.return_value = True
            yield

    return f


@pytest.fixture
def provider_id():
    return "unittest-server"


@pytest.fixture
def openid_connect_provider_id():
    return "unittest-server"


@pytest.fixture
def password_reset_key_generator():
    def f(user):
        from allauth.account import app_settings

        token_generator = app_settings.PASSWORD_RESET_TOKEN_GENERATOR()
        uid = user_pk_to_url_str(user)
        temp_key = token_generator.make_token(user)
        key = f"{uid}-{temp_key}"
        return key

    return f


@pytest.fixture
def google_provider_settings(settings):
    gsettings = {"APPS": [{"client_id": "client_id", "secret": "secret"}]}
    settings.SOCIALACCOUNT_PROVIDERS = {"google": gsettings}
    return gsettings


@pytest.fixture
def twitter_provider_settings(settings):
    tsettings = {"APPS": [{"client_id": "client_id", "secret": "secret"}]}
    settings.SOCIALACCOUNT_PROVIDERS = {"twitter": tsettings}
    return tsettings


@pytest.fixture
def user_with_totp(user):
    from allauth.mfa.totp.internal import auth

    auth.TOTP.activate(user, auth.generate_totp_secret())
    return user


@pytest.fixture
def user_with_recovery_codes(user_with_totp):
    from allauth.mfa.recovery_codes.internal import auth

    auth.RecoveryCodes.activate(user_with_totp)
    return user_with_totp


@pytest.fixture
def passkey(user):
    from allauth.mfa.models import Authenticator

    authenticator = Authenticator.objects.create(
        user=user,
        type=Authenticator.Type.WEBAUTHN,
        data={
            "name": "Test passkey",
            "passwordless": True,
            "credential": {},
        },
    )
    return authenticator


@pytest.fixture
def user_with_passkey(user, passkey):
    return user


@pytest.fixture
def sociallogin_setup_state():
    def setup(client, process=None, next_url=None, **kwargs):
        state_id = "123"
        session = client.session
        state = {"process": process or AuthProcess.LOGIN, **kwargs}
        if next_url:
            state["next"] = next_url
        states = {}
        states[state_id] = [state, time.time()]
        session[statekit.STATES_SESSION_KEY] = states
        session.save()
        return state_id

    return setup


@pytest.fixture
def request_factory(rf):
    class RequestFactory:
        def get(self, path):
            request = rf.get(path)
            SessionMiddleware(lambda request: None).process_request(request)
            MessageMiddleware(lambda request: None).process_request(request)
            return request

    return RequestFactory()


@pytest.fixture
def get_last_email_verification_code():
    from allauth.account.internal.flows import email_verification_by_code

    def f(client, mailoutbox):
        code = re.search(
            "\n[0-9a-z]{6}\n", mailoutbox[-1].body, re.I | re.DOTALL | re.MULTILINE
        )[0].strip()
        if hasattr(client, "headless_session"):
            session = client.headless_session()
        else:
            session = client.session
        assert (
            session[email_verification_by_code.EMAIL_VERIFICATION_CODE_SESSION_KEY][
                "code"
            ]
            == code
        )
        return code

    return f


@pytest.fixture
def get_last_password_reset_code():
    from allauth.account.internal.flows import password_reset_by_code

    def f(client, mailoutbox):
        code = re.search(
            "\n[0-9a-z]{8}\n", mailoutbox[-1].body, re.I | re.DOTALL | re.MULTILINE
        )[0].strip()
        if hasattr(client, "headless_session"):
            session = client.headless_session()
        else:
            session = client.session
        assert (
            session[password_reset_by_code.PASSWORD_RESET_VERIFICATION_SESSION_KEY][
                "code"
            ]
            == code
        )
        return code

    return f


@pytest.fixture
def settings_impacting_urls(settings):
    @contextmanager
    def f(**kv):
        def reload_urlconf():
            clear_url_caches()
            for urlconf in [
                settings.ROOT_URLCONF,
                "allauth.account.urls",
                "allauth.urls",
                "allauth.mfa.urls",
                "allauth.mfa.base.urls",
                "allauth.headless.urls",
                "allauth.headless.base.urls",
                "allauth.headless.socialaccount.urls",
                "allauth.headless.usersessions.urls",
                "allauth.headless.mfa.urls",
            ]:
                if urlconf in sys.modules:
                    importlib.reload(sys.modules[urlconf])
            set_urlconf(None)

        old_values = {}
        for k, v in kv.items():
            if hasattr(settings, k):
                old_values[k] = getattr(settings, k)
            setattr(settings, k, v)
        reload_urlconf()
        yield
        for k, v in kv.items():
            if k in old_values:
                setattr(settings, k, old_values[k])
            else:
                delattr(settings, k)
        reload_urlconf()

    return f


@pytest.fixture(autouse=True)
def clear_phone_stub():
    from tests.projects.common import phone_stub

    yield
    phone_stub.clear()


@pytest.fixture
def sms_outbox():
    from tests.projects.common import phone_stub

    return phone_stub.sms_outbox


@pytest.fixture
def phone_factory():
    def f():
        return f"+31{random.randint(1, 10**10):010}"

    return f


@pytest.fixture
def phone(phone_factory):
    return phone_factory()


@pytest.fixture
def user_with_phone(user, phone):
    from allauth.account.adapter import get_adapter

    get_adapter().set_phone(user, phone, True)
    return user


def pytest_ignore_collect(path, config):
    from tests.projects.common.settings import INSTALLED_SOCIALACCOUNT_APPS

    if "allauth.socialaccount.providers.saml" not in INSTALLED_SOCIALACCOUNT_APPS:
        if (
            Path(__file__).parent / "apps" / "socialaccount" / "providers" / "saml"
            in Path(path).parents
        ):
            return True

    tests_to_skip = {
        "tests.projects.account_only.settings": (
            "headless",
            "mfa",
            "usersessions",
            "socialaccount",
            "idp",
        ),
        "tests.projects.headless_only.settings": ("idp",),
    }
    dsm = os.getenv("DJANGO_SETTINGS_MODULE")
    skipped_paths = tests_to_skip.get(dsm)
    if not skipped_paths:
        return False
    for skipped_path in skipped_paths:
        abs_skipped_path = Path(__file__).parent / "apps" / skipped_path
        if abs_skipped_path == Path(path) or abs_skipped_path in Path(path).parents:
            return True
    return False


@pytest.fixture()
def messagesoutbox():
    from tests.projects.common import adapters

    adapters.messagesoutbox = []
    yield adapters.messagesoutbox
