from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from allauth.account import app_settings as account_settings
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.disqus.provider import DisqusProvider
from tests.apps.socialaccount.base import OAuth2TestsMixin
from tests.mocking import MockedResponse


@override_settings(
    SOCIALACCOUNT_AUTO_SIGNUP=True,
    ACCOUNT_SIGNUP_FORM_CLASS=None,
    ACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.MANDATORY,
)
class DisqusTests(OAuth2TestsMixin, TestCase):
    provider_id = DisqusProvider.id

    def get_mocked_response(
        self, name="Raymond Penners", email="raymond.penners@example.com"
    ):
        return MockedResponse(
            200,
            """
              {"response": {"name": "%s",
               "avatar": {
                "permalink": "https://lh5.googleusercontent.com/photo.jpg"
               },
               "email": "%s",
               "profileUrl": "https://plus.google.com/108204268033311374519",
               "id": "108204268033311374519" }}
        """
            % (name, email),
        )

    def get_expected_to_str(self):
        return "raymond.penners@example.com"

    def test_account_connect(self):
        email = "user@example.com"
        user = User.objects.create(username="user", is_active=True, email=email)
        user.set_password("test")
        user.save()
        EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
        self.client.login(username=user.username, password="test")
        self.login(self.get_mocked_response(), process="connect")
        # Check if we connected...
        self.assertTrue(
            SocialAccount.objects.filter(user=user, provider=DisqusProvider.id).exists()
        )
        # For now, we do not pick up any new email addresses on connect
        self.assertEqual(EmailAddress.objects.filter(user=user).count(), 1)
        self.assertEqual(EmailAddress.objects.filter(user=user, email=email).count(), 1)
