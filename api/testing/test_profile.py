import datetime
import json

from django.test import TestCase

from api.testing import mock
from footprint.consts import FootprintChoices
from user_info.consts import SexChoices
from user_info.manager.user_info_mananger import get_user_info_db
from utilities.mock_utility.helper import create_user_login_client


class TestMyProfile(TestCase):

    def test_get_my_profile(self):
        """
        python manage.py test api.testing.test_profile.TestMyProfile.test_get_my_profile
        """
        client, user = create_user_login_client()
        mock.create_user_info(user)
        result = client.json_get('/api/user/profile/')
        self.assertTrue('birthday' in result)

    def test_set_my_profile(self):
        """
        python manage.py test api.testing.test_profile.TestMyProfile.test_set_my_profile
        """
        client, user = create_user_login_client()
        mock.create_user_info(user)
        result = client.json_post('/api/user/set_profile/', {'nickname': 'snow', 'birthday': '1989-11-25', 'sex': '女',
                                                             'show_wechat_no': 1})
        self.assertTrue(result['error_code'] == 0)
        user_info = get_user_info_db(user)
        self.assertEqual(user_info.birthday, datetime.date(1989, 11, 25))
        self.assertEqual(user_info.sex, SexChoices.FEMALE)
        self.assertEqual(user_info.show_wechat_no, True)

    def test_tab_list_view(self):
        """
        python manage.py test api.testing.test_profile.TestMyProfile.test_tab_list_view
        """
        client, user = create_user_login_client()
        mock.create_user_info(user)
        result = client.json_get('/api/user/tab_list/')
        self.assertEqual(result['tab_list'], FootprintChoices.values())

        result = client.json_post('/api/user/set_tab_list/', data={'tab_list': json.dumps([2, 1, 5, 6, 3, 4])})
        self.assertEqual(result['error_code'], 0)
