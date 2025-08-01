from django.test import TestCase
from django.test.utils import override_settings

from allauth.socialaccount.providers.pinterest.provider import PinterestProvider
from tests.apps.socialaccount.base import OAuth2TestsMixin
from tests.mocking import MockedResponse


class PinterestTests(OAuth2TestsMixin, TestCase):
    provider_id = PinterestProvider.id

    def get_mocked_response(self):
        return MockedResponse(
            200,
            """
            {
                "data": {
                    "url": "https://www.pinterest.com/muravskiyyarosl/",
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "id": "351247977031674143"
                }
            }
            """,
        )

    def get_expected_to_str(self):
        return "Jane Doe"

    @override_settings(
        SOCIALACCOUNT_AUTO_SIGNUP=False,
        SOCIALACCOUNT_PROVIDERS={
            "pinterest": {
                "API_VERSION": "v5",
            }
        },
    )
    def test_login_v5(self):
        self.provider_id = PinterestProvider.id
        resp = self.login(
            MockedResponse(
                200,
                """
                {
                    "account_type": "BUSINESS",
                    "profile_image": "https://i.pinimg.com/280x280_RS/5c/88/2f/5c882f4b02468fcd6cda2ce569c2c166.jpg",
                    "website_url": "https://sns-sdks.github.io/",
                    "username": "enjoylifebot"
                }
                """,
            ),
        )
        assert resp.status_code == 302
