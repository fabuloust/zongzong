import json
import random

from django.test import TestCase

from api.testing import mock
from footprint.consts import FootprintChoices
from footprint.models import Footprint
from utilities.mock_utility.helper import create_user_login_client


class TestFootprint(TestCase):
    """
    测试痕迹相关的东西
    """

    def test_user_brief_profile_view(self):
        """
        测试浮窗的用户详情
        python manage.py test footprint.testing.test_footprint_views.TestFootprint.test_user_brief_profile_view
        """
        client, user = create_user_login_client()
        user_info = mock.create_user_info(user)
        mock.create_footprint(user_info)

        client_2, user_2 = create_user_login_client()
        result = client_2.json_get('/api/user/brief_introduction/?user_id={}'.format(user.id))
        self.assertEqual(result['error_code'], 0)
        self.assertTrue('user_info' in result)
        self.assertTrue('footprint_info' in result)

    def test_create_footprint_view(self):
        """
        测试发布踪踪
        python manage.py test footprint.testing.test_footprint_views.TestFootprint.test_create_footprint_view
        """
        client, user = create_user_login_client()
        mock.create_user_info(user)
        image_list_str = json.dumps(['image1', 'image2', 'image3'])
        result = client.json_post('/api/footprint/create/',
                                  data={'thinking': u'真他妈操蛋啊！', 'image_list': image_list_str,
                                        'latitude': random.randint(0, 90),
                                        'longitude': random.randint(0, 180), 'location': 'heaven'})
        self.assertEqual(result['error_code'], 0)
        footprint = Footprint.objects.get(user_id=user.id)
        self.assertEqual(footprint.location, 'heaven')




