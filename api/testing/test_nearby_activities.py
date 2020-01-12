from django.test import TestCase

from api.testing import mock
from commercial.testing.mock import create_activity
from footprint.models import FlowType
from utilities.mock_utility.helper import create_user_login_client


class TestNearby(TestCase):

    def test_get_nearby_activities(self):
        """
        python manage.py test --settings=settings-test api.testing.test_nearby_activities.TestNearby.test_get_nearby_activities
        """
        activity = create_activity()
        client, user = create_user_login_client()
        user_info = mock.create_user_info(user)
        client.post('/footprint/create/', {
            'content': '测试啊测试', 'image_list': '["1.jpg", "2.jpg"]', 'lon': 116, 'lat': 40, 'hide': 0,
            'location': '填上'
        })
        result = client.json_get('/api/get_nearby_activities/', {'lon': 116, 'lat': 40, 'radius': 100})
        self.assertEqual(len(result['footprints']), 1)
        self.assertEqual(len(result['activities']), 1)

        result = client.json_get('/api/discovery/')
        self.assertEqual(len(result['items']), 2)
        self.assertEqual(result['items'][0]['flow_type'], FlowType.FOOTPRINT)
        result = client.json_get('/api/discovery/')
        items = result['items']
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['location'], '填上')


