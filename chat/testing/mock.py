# -*- encoding:utf-8 -*-
from __future__ import absolute_import

from random import randint

from api.manager.positon_manager import add_activity_location
from commercial.models import Club, CommercialActivity
from utilities.string_utils import random_str


def create_club():
    return Club.objects.create(name=random_str(8), fans_num=8, address=random_str(20), avatar=random_str(10),
                               lat=40 + 0.1 * randint(1, 8), lon=116 + 0.1 * randint(1, 8))


def create_activity(club=None, name='', address='', time_detail='', description='', total_quota=10, participant_num=6,
                    detail=''):
    if not club:
        club = create_club()
    name = name or random_str(8)
    address = address or random_str(20)
    time_detail = time_detail or random_str(20)
    description = description or random_str(30)
    total_quota = total_quota or randint(10, 20)
    participant_num = participant_num or randint(5, 10)
    detail = detail or random_str(8)
    activity = CommercialActivity.objects.create(club=club, name=name, address=address, time_detail=time_detail,
                                                 description=description, total_quota=total_quota,
                                                 participant_num=participant_num, detail=detail, lon=club.lon,
                                                 lat=club.lat)
    add_activity_location(activity.id, club.lon, club.lat)
    return activity
