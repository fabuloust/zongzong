from footprint.models import Footprint, FootprintFavor
from user_info.manager.user_info_mananger import get_user_info_db
from utilities.time_utils import get_time_show


def get_footprint_by_id_db(footprint_id):
    try:
        return Footprint.objects.get(id=footprint_id)
    except Footprint.DoesNotExist:
        return None


def create_footprint_db(user_id, thinking, tag, latitude, longitude, place, image_list_str):
    """
    创建痕迹
    :param user_id:
    :param thinking:
    :param tag: 标签
    :param latitude: 纬度
    :param longitude: 经度
    :param place: 地点名
    :param image_list_str: json list
    :return: footprint
    """
    user_info = get_user_info_db(user_id)
    footprint = Footprint.objects.create(user=user_info.user, name=user_info.nickname, sex=user_info.sex, tag=tag,
                                         content=thinking, latitude=latitude, longitude=longitude, place=place,
                                         image_list_str=image_list_str)
    return footprint


def get_user_newest_footprint_db(user_id):
    """
    获取用户最新的一个动态
    :param user:
    :return:
    """
    query = Footprint.objects.filter(user_id=user_id).order_by('-created_time')
    return query[0] if query else None


def update_footprint_favor_num_db(footprint_id, num):
    footprint = get_footprint_by_id_db(footprint_id)
    footprint.favor_num += num
    footprint.save()
    return footprint.favor_num


def add_favor_db(footprint_id, user):
    """
    点赞
    """
    footprint_favor, created = FootprintFavor.objects.get_or_create(footprint_id=footprint_id, user=user)
    if not created:
        footprint_favor.favored = not footprint_favor.favored
        footprint_favor.save()
    favor_num = update_footprint_favor_num_db(footprint_id, 1 if footprint_favor.favored else -1)
    return favor_num


def build_user_footprint(footprint):
    """
    构建用户足迹
    :param footprint:
    :return: {
        content,
        time,
        place,
        distance,
        image_list,
        favor_num,
        comment_num,
        forward_num
    }
    """
    return {
        'content': footprint.content,
        'show_time': get_time_show(footprint.created_time),
        'place': footprint.place,
        'latitude': footprint.latitude,
        'longitude': footprint.longitude,
        'distance': 0,
        'image_list': footprint.image_list,
        'favor_num': footprint.favor_num,
        'comment_num': footprint.comment_num,
        'forward_num': footprint.forward_num,
    }


# def build_footprint_detail(footprint, request_user):
#     """
#     展示的痕迹详情，包括
#     1、用户头像、用户名、时间、距离自己，是否关注
#     2. footprint详情
#     3.评论（总数）： 各个评论及点赞数
#     :param footprint:
#     :param request_user: 查看的用户
#     :return: {
#         'followed': True or False,
#         'user_info': {
#             'image', 'show_time', 'latitude', 'longitude', 'place',
#         }
#         'footprint': {
#             'content', image_list, favor_num, reply_num, forward_num, show_time
#         }
#         'comment_num',
#         comment_list: [
#             {image, nickname, show_time, distance, favor_num, user_id},
#         ]
#     }
#     """
#     user_info = get_user_info_db(footprint.user)
#     user_info_data = {
#         'image': user_info.image,
#         'nickname': user_info.nickname,
#         'place': footprint.place,
#     }
#     foot_print_data = {
#         'content': footprint.content,
#         'image_list': footprint.image_list_str,
#         'favor_num': footprint.favor_num,
#         'reply_num': footprint.comment_num,
#         'forward_num': footprint.forward_num,
#         'show_time': get_time_show(footprint.created_time)
#     }
#     comment_list =
