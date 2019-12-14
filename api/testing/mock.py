import datetime
import json
import random

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
    footprint = Footprint.objects.create(user=user_info.user, name=user_info.nickname, sex=user_info.sex,
                                         tag=user_info.current_tag, latitude=str(random.randrange(90)),
                                         longitude=str(random.randrange(180)), place=random_str(random.randint(1, 8)),
                                         content=random_str(20), image_list_str=json.dumps(image_list),
                                         forward_num=random.randint(1, 100), favor_num=random.randint(1, 100),
                                         comment_num=random.randint(1, 100))
    return footprint
