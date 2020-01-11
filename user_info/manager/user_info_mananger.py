import random

from django.contrib.auth.models import User

from user_info.models import UserBaseInfo
from utilities.time_utils import get_age_by_birthday


def random_password():
    return '%06d' % random.randint(0, 1000000)


def get_or_create_user_db(username):

    user, created = User.objects.get_or_create(username=username, defaults={'password': random_password()})
    return user, created


def get_user_info_by_user_id_db(user_id):
    """
    获取用户小窗页信息
    :param user_id:
    :return:
    """
    user_info, _ = UserBaseInfo.objects.get_or_create(user_id=user_id)
    return user_info


def get_user_infos_by_user_ids_db(user_ids):
    return UserBaseInfo.objects.get(user_id__in=user_ids)


def update_my_profile_db(user, sex, avatar, location, nickname, wechat_no, show_wechat_no, signature, birthday):
    """
    更新我的资料
    :param user:
    :param nickname:
    :param birthday:
    :param sex:
    :param show_wechat_no:
    """
    user_info = get_user_info_by_user_id_db(user.id)
    if sex:
        user_info.sex = sex
    if avatar:
        user_info.avatar = avatar
    if location:
        user_info.location = location
    if nickname:
        user_info.nickname = nickname
    if wechat_no:
        user_info.wechat_no = wechat_no
    if show_wechat_no:
        user_info.show_wechat_no = show_wechat_no
    if signature:
        user_info.signature = signature
    if birthday:
        user_info.birthday = birthday
    user_info.save()
    return user_info


def get_user_brief_profile(user):
    """
    获取用户简介
    :param user:
    :return:
    """
    user_info = get_user_info_by_user_id_db(user.id)
    return {
        'avatar': user_info.avatar,
        'nickname': user_info.nickname,
        'sex': user_info.sex,
        'age': get_age_by_birthday(user_info.birthday),
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


def create_user_info_db(open_id, nickname, avatar):
    """
    创建userbaseinfo
    :param open_id:
    :param nickname:
    :param avatar:
    :return: UserBaseInfo
    """
    user, created = get_or_create_user_db(open_id)
    user_info = UserBaseInfo.objects.create(user=user, open_id=open_id, nickname=nickname, avatar=avatar)
    return user_info
