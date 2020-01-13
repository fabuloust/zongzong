from django.test import TestCase

from commercial.testing import mock
from utilities.mock_utility.helper import create_user_login_client


class Test(TestCase):

    def test_club(self):
        """
        python manage.py test --settings=settings-test commercial.testing.test_commercial_related.Test.test_club
        """
        club = mock.create_club()
        client, user = create_user_login_client()
        result = client.json_get('/commercial/get_club_info/?club_id={}'.format(club.id))
        self.assertTrue('avatar' in result)
        activity = mock.create_activity(club)
        result = client.json_get('/commercial/get_activity_detail/?activity_id={}'.format(activity.id))
        self.assertEqual(len(result['participants']), 0)
        client.json_post('/commercial/subscribe_activity/', {'activity_id': activity.id, 'name': 'test',
                                                             'cellphone': '18210065466', 'num': 2,
                                                             'hint': '没有'})
        result = client.json_get('/commercial/get_activity_detail/?activity_id={}'.format(activity.id))
        self.assertEqual(len(result['participants']), 1)