import datetime

from django.test import TestCase

from user_info.models import UserBaseInfo
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
        self.assertEqual(result['error_code'], 0)
        user_info = UserBaseInfo.objects.all()[0]
        self.assertEqual(user_info.sex, 'f')
        self.assertEqual(user_info.avatar, 'test.jpg')
        self.assertEqual(user_info.nickname, 'test')
        self.assertEqual(user_info.location, '地球')
        self.assertEqual(user_info.wechat_no, 'sss')
        self.assertEqual(user_info.show_wechat_no, 1)
        self.assertEqual(user_info.signature, '这是我的签名')
        self.assertEqual(user_info.birthday, datetime.date(2000, 1, 1))
