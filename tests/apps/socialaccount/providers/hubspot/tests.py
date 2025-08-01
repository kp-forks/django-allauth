from django.test import TestCase

from allauth.socialaccount.providers.hubspot.provider import HubspotProvider
from tests.apps.socialaccount.base import OAuth2TestsMixin
from tests.mocking import MockedResponse


class HubspotTests(OAuth2TestsMixin, TestCase):
    provider_id = HubspotProvider.id

    def get_mocked_response(self):
        return MockedResponse(
            200,
            """{
                    "token": "CNye4dqFMBICAAEYhOKlDZZ_z6IVKI_xMjIUgmFsNQzgBjNE9YBmhAhNOtfN0ak6BAAAAEFCFIIwn2EVRLpvJI9hP4tbIeKHw7ZXSgNldTFSAFoA",
                    "user": "m@acme.com",
                    "hub_domain": "acme.com",
                    "scopes": ["oauth"],
                    "scope_to_scope_group_pks": [25, 31],
                    "trial_scopes": [],
                    "trial_scope_to_scope_group_pks": [],
                    "hub_id": 211580,
                    "app_id": 833572,
                    "expires_in": 1799,
                    "user_id": 42607123,
                    "token_type": "access"
                }""",
        )

    def get_expected_to_str(self):
        return "m@acme.com"
