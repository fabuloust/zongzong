from django.test import TestCase

from utilities.mock_utility.helper import create_user_login_client


class Test(TestCase):

    def test_chat(self):
        """
        python manage.py test --settings=settings-test chat.testing.test_chat.Test.test_chat
        """
        client, user = create_user_login_client()
        client2, user2 = create_user_login_client()
        client.json_post('/chat/post_content/')