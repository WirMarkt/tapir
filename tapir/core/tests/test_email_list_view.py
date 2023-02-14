from django.urls import reverse

from tapir.accounts.tests.factories.factories import TapirUserFactory
from tapir.utils.tests_utils import TapirFactoryTestBase


class TestEmailListView(TapirFactoryTestBase):
    def test_only_visible_for_member_office(self):
        self.login_as_normal_user()
        response = self.client.get(reverse("core:email_list"))
        self.assertEqual(response.status_code, 403)

    def test_all_emails_are_included(self):
        user = TapirUserFactory.create(
            preferred_language="en", is_in_member_office=True
        )
        self.login_as_user(user)

        response = self.client.get(reverse("core:email_list"))
        self.assertEqual(200, response.status_code)

        response_content = response.content.decode()
        expected_email_names = [
            "Tapir account created",
            "Shift missed",
            "Stand-in found",
            "Shift reminder",
            "Extra shares bought",
            "Membership confirmation for active users",
            "Membership confirmation for investing users",
        ]
        for name in expected_email_names:
            self.assertIn(name, response_content)
