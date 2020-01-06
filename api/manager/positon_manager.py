"""
管理距离相关
"""
from redis_utils.container.api_geo import RedisGeo

activity_location_container = RedisGeo('activity_location')
user_location_container = RedisGeo('user_location')


def add_user_location(footprint_id, lon, lat):
    """
    把用户地址加入容器
    """

    user_location_container.add(lon, lat, footprint_id)


def remove_user_location(footprint_id):
    """
    删除用户足迹
    :param footprint_id:
    :return:
    """
    user_location_container.redis.zrem(user_location_container.cache_key, footprint_id)


def get_user_location(user_id):
    """
    :param user_id:
    :return: [lon, lat]
    """
    position = user_location_container.get_position(user_id)[0]
    return position if position else [None, None]


#################################################################################


def add_activity_location(activity_id, lon, lat):
    """
    把活动地址加入容器
    :param activity_id:
    :return:
    """
    activity_location_container.add(lon, lat, activity_id)


def remove_activity_location(activity_id):
    # 删除活动
    activity_location_container.redis.zrem(activity_location_container.cache_key, activity_id)


def get_activity_location(activity_id):
    """
    :param activity_id:
    :return: [lon, lat]
    """
    position = activity_location_container.get_position(activity_id)[0]
    return position if position else [None, None]

#################################################################################



