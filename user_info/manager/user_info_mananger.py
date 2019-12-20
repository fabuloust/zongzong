import json
import random

from django.contrib.auth.models import User

from user_info.models import UserBaseInfo
from footprint.consts import FootprintChoices
from utilities.time_utils import get_age_by_birthday


def random_password():
    return '%06d' % random.randint(0, 1000000)


def get_or_create_user_db(username):

    user, created = User.obects.get_or_create(username=username, defautls={'password': random_password()})
    return user, created


def get_user_info_db(user):
    """
    获取用户小窗页信息
    :param user:
    :return:
    """
    try:
        user_info = UserBaseInfo.objects.get(user=user)
        return user_info
    except UserBaseInfo.DoesNotExist:
        return None


def get_user_tag_list_db(user):
    """
    获取用户的标签配置
    :param user:
    :return:
    """
    try:
        user_info = UserBaseInfo.objects.get(user=user)
        return json.loads(user_info.tags)
    except UserBaseInfo.DoesNotExist:
        return FootprintChoices.values()


def update_user_tag_list_db(user, tag_list_str):
    """
    更新用户的踪踪tag列表
    :param tag_list_str:
    :param user:
    :return:
    """
    user_info = get_user_info_db(user)
    user_info.tags = tag_list_str
    user_info.save()
    return user_info


def update_my_profile_db(user, nickname, birthday, sex, show_wechat_no):
    """
    更新我的资料
    :param user:
    :param nickname:
    :param birthday:
    :param sex:
    :param show_wechat_no:
    """
    user_info = get_user_info_db(user)
    if user_info:
        user_info.nickname = nickname
        user_info.birthday = birthday
        user_info.sex = sex
        user_info.show_wechat_no = show_wechat_no
        user_info.save()
    return user_info


def get_user_brief_profile(user):
    """
    获取用户简介
    :param user:
    :return:
    """
    user_info = get_user_info_db(user)
    return {
        'image': user_info.image,
        'nickname': user_info.nickname,
        'sex': user_info.sex,
        'age': get_age_by_birthday(user_info.birthday),
        'current_tag': user_info.current_tag,
        'signature': user_info.signature,
    }


def get_user_info_by_open_id_db(open_id):
    """
    根据open_id获取用户信息
    :param open_id:
    :return: user_info_record
    """
    try:
        return UserBaseInfo.objects.get(open_id=open_id)
    except UserBaseInfo.DoesNotExist:
        return None


def get_user_by_open_id_db(open_id):
    user, created = get_or_create_user_db(open_id)
    return user, created


def create_user_info_db(open_id, nickname, image):
    """
    创建userbaseinfo
    :param open_id:
    :param nickname:
    :param image:
    :return: UserBaseInfo
    """
    user, created = get_or_create_user_db(open_id)
    user_info = UserBaseInfo.objects.create(user=user, open_id=open_id, nickname=nickname, image=image)
    return user_info
