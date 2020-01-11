import json
import random

from django.test import TestCase

from api.testing import mock
from footprint.models import Footprint
from utilities.mock_utility.helper import create_user_login_client


class TestFootprint(TestCase):
    """
    测试痕迹相关的东西
    python manage.py test  --settings=settings-test footprint.testing.test_footprint_views.TestFootprint
    """
    def test_create_footprint_view(self):
        """
        测试发布踪踪
        python manage.py test footprint.testing.test_footprint_views.TestFootprint.test_create_footprint_view
        """
        client, user = create_user_login_client()
        mock.create_user_info(user)
        image_list_str = json.dumps(['image1', 'image2', 'image3'])
        result = client.json_post('/footprint/create/',
                                  data={'content': u'真他妈操蛋啊！', 'image_list': image_list_str,
                                        'latitude': random.randint(0, 90),
                                        'longitude': random.randint(0, 180), 'location': 'heaven'})
        self.assertEqual(result['error_code'], 0)
        footprint = Footprint.objects.get(user_id=user.id)
        self.assertEqual(footprint.location, 'heaven')




