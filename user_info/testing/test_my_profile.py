from django.test import TestCase

from utilities.mock_utility.helper import create_user_login_client


class MyProfileTest(TestCase):

    def test_my_profile(self):
        """
        python manage.py test --settings=settings-test user_info.testing.test_my_profile.MyProfileTest.test_my_profile
        """
        client, user = create_user_login_client()
        result = client.json_post('/user_info/my_profile/edit/',
                                  {'sex': 'f', 'avatar': 'test.jpg', 'nickname': 'test',
                                   'location': '地球', 'wechat_no': 'sss', 'show_wechat_no': 1,
                                   'signature': '这是我的签名', 'birthday': '2000-01-01'})
        print(result.content)
