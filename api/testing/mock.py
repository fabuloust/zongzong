import datetime
import json
import random

from api.manager.positon_manager import add_user_location
from footprint.consts import FootprintChoices
from footprint.models import Footprint
from user_info.consts import SexChoices
from user_info.models import UserBaseInfo
from utilities.string_utils import random_str


def create_user_info(user):

    user_info = UserBaseInfo.objects.create(user=user, nickname=random_str(), signature=random_str(),
                                            sex=SexChoices.MALE, birthday=datetime.date(1989, 11, 25),
                                            tags=FootprintChoices.values(),
                                            current_tag=FootprintChoices.HELP)
    return user_info


def create_footprint(user_info):
    image_list = []
    for i in range(random.randrange(5, 10)):
        image_list.append('https://image.zongzong.com/' + random_str(i))
    lon = 116 + 0.1 * random.randint(1, 8)
    lat = 40 + 0.1 * random.randint(1, 8)
    footprint = Footprint.objects.create(user=user_info.user, name=user_info.nickname, sex=user_info.sex,
                                         lat=lat, lon=lon, place=random_str(random.randint(1, 8)),
                                         content=random_str(20), image_list_str=json.dumps(image_list),
                                         forward_num=random.randint(1, 100), favor_num=random.randint(1, 100),
                                         comment_num=random.randint(1, 100))
    add_user_location(footprint.id, lon, lat)
    return footprint
