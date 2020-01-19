import json

from geopy.distance import geodesic

from commercial.manager.activity_manager import get_commercial_activity_by_id_db
from footprint.models import Footprint, Favor, TotalFlow, FlowType, Comment
from user_info.manager.user_info_mananger import get_user_info_by_user_id_db
from utilities.date_time import datetime_to_str
from utilities.time_utils import get_time_show


def get_footprint_by_id_db(footprint_id):
    try:
        return Footprint.objects.get(id=footprint_id)
    except Footprint.DoesNotExist:
        return None


def get_footprints_by_ids_db(footprint_ids):
    return Footprint.objects.filter(id__in=footprint_ids)


def create_footprint_db(user_id, thinking, latitude, longitude, location, image_list, hide):
    """
    创建痕迹
    :param user_id:
    :param thinking:
    :param latitude: 纬度
    :param longitude: 经度
    :param location: 地点名
    :param image_list: list
    :return: footprint
    """
    user_info = get_user_info_by_user_id_db(user_id)
    footprint = Footprint.objects.create(user=user_info.user, name=user_info.nickname, sex=user_info.sex,
                                         content=thinking, lat=latitude, lon=longitude, location=location,
                                         image_list_str=json.dumps(image_list), hide=hide, avatar=user_info.avatar)
    return footprint


def get_user_newest_footprint_db(user_id):
    """
    获取用户最新的一个动态
    :param user:
    :return:
    """
    query = Footprint.objects.filter(user_id=user_id).order_by('-created_time')
    return query[0] if query else None


def get_footprints_by_user_id_db(user_id, start, end):
    """
    获取用户足迹
    """
    return Footprint.objects.filter(user_id=user_id).order_by('-created_time')[start: end]


def update_footprint_favor_num_db(footprint_id, num):
    footprint = get_footprint_by_id_db(footprint_id)
    footprint.favor_num += num
    footprint.save()
    return footprint.favor_num


def update_activity_favor_num(activity_id, num):
    activity = get_commercial_activity_by_id_db(activity_id)
    activity.favor_num += num
    activity.save()
    return activity.favor_num


def add_favor_db(flow_id, flow_type, user_id):
    """
    点赞
    """
    favor, created = Favor.objects.get_or_create(flow_id=flow_id, flow_type=flow_type, user_id=user_id)
    if not created:
        favor.favored = not favor.favored
        favor.save()
    if flow_type == FlowType.FOOTPRINT:
        favor_num = update_footprint_favor_num_db(flow_id, 1 if favor.favored else -1)
    else:
        favor_num = update_activity_favor_num(flow_id, 1 if favor.favored else -1)
    return favor_num


def update_comment_num_db(footprint_id, num=1):
    footprint = get_footprint_by_id_db(footprint_id)
    footprint.comment_num += num
    footprint.save()
    return footprint.comment_num


def get_footprint_comment_list(footprint_id, start, end):
    return Comment.objects.filter(flow_id=footprint_id, flow_type=FlowType.FOOTPRINT,
                                  is_deleted=False).order_by('-created_time')[start: end]


def add_to_flow(flow_id, flow_type):
    return TotalFlow.objects.create(flow_id=flow_id, flow_type=flow_type)


def get_flows_db(start_num, end_num):
    return TotalFlow.objects.order_by('-created_time')[start_num: end_num]


def is_user_favored_footprint(user_id, flow_id, flow_type):
    return Favor.objects.filter(user_id=user_id, flow_id=flow_id, flow_type=flow_type).exists()


def build_user_footprint(footprint):
    """
    构建用户足迹
    :param footprint:
    :return: {
        content,
        time,
        location,
        distance,
        image_list,
        favor_num,
        comment_num,
        forward_num
    }
    """
    return {
        'id': footprint.id,
        'avatar': footprint.avatar,
        'content': footprint.content,
        'show_time': get_time_show(footprint.created_time),
        'location': footprint.location,
        'latitude': footprint.latitude,
        'longitude': footprint.longitude,
        'distance': 0,
        'image_list': footprint.image_list,
        'favor_num': footprint.favor_num,
        'comment_num': footprint.comment_num,
        'forward_num': footprint.forward_num,
    }


def build_comment(comment):
    return {
        'avatar': comment.avatar,
        'name': comment.name,
        'created_time': datetime_to_str(comment.created_time),
        'content': comment.comment,
        'user_id': comment.user_id
    }


def build_footprint_detail(footprint, user_id):
    """
    展示的痕迹详情，包括
    1、用户头像、用户名、时间、距离自己，是否关注
    2. footprint详情
    3.评论（总数）： 各个评论及点赞数
    :param footprint:
    :return: {
        'followed': True or False,
        'user_info': {
            'image', 'show_time', 'latitude', 'longitude', 'place',
        }
        'footprint': {
            'content', image_list, favor_num, reply_num, forward_num, show_time
        }
        'comment_num',
        comment_list: [
            {image, nickname, show_time, distance, favor_num, user_id},
        ]
    }
    """
    user_info = get_user_info_by_user_id_db(footprint.user_id)
    user_info_data = {
        'avatar': user_info.avatar,
        'nickname': user_info.nickname,
        'user_id': footprint.user_id
    }
    foot_print_data = {
        'location': footprint.location,
        'content': footprint.content,
        'image_list': footprint.image_list,
        'favor_num': footprint.favor_num,
        'reply_num': footprint.comment_num,
        'forward_num': footprint.forward_num,
        'show_time': get_time_show(footprint.created_time),
        'favored': is_user_favored_footprint(user_id, footprint.id, FlowType.FOOTPRINT),
    }
    comment_list = get_footprint_comment_list(footprint.id, 0, 20)
    comment_data = {'comments': [build_comment(comment) for comment in comment_list]}
    result = user_info_data
    result.update(foot_print_data)
    result.update(comment_data)
    return result


def build_footprint_list_info(footprints, user_id, lat=None, lon=None):
    """
    构建足迹列表详情
    :param footprints:
    :return:
    """
    need_distance = bool(lat and lon)
    result = []
    for footprint in footprints:
        info = {
            'location': footprint.location,
            'created_time': get_time_show(footprint.created_time),
            'content': footprint.content,
            'image_list': footprint.image_list,
            'comment_num': footprint.comment_num,
            'favor_num': footprint.favor_num,
            'footprint_id': footprint.id,
            'favored': is_user_favored_footprint(user_id, footprint.id, FlowType.FOOTPRINT)
        }
        if need_distance:
            distance = geodesic((lat, lon), (footprint.lat, footprint.lon)).meters
            info['distance'] = distance
        result.append(info)
    return result
