from api.manager.positon_manager import user_location_container, activity_location_container
from commercial.manager.activity_manager import get_commercial_activities_by_ids_db
from footprint.manager.footprint_manager import get_footprints_by_ids_db
from utilities.date_time import time_format


def build_footprint_info(footprint, position):
    return {
        'footprint_id': footprint.id,
        'time': time_format(footprint.created_time),
        'user_id': footprint.user_id,
        'name': footprint.name,
        'avatar': footprint.image,
        'lat': position[1],
        'lon': position[0]
    }


def build_activity_info(activity, position):
    return {
        'activity_id': activity.id,
        'name': activity.name,
        'avatar': activity.club.avatar,
        'quota': '【{}/{}】'.format(activity.participant_num, activity.total_quota),
        'description': activity.description,
        'lat': position[1],
        'lon': position[0]
    }


def get_nearby_activity(lon, lat, radius=7):
    """
    获取附近的活动
    :param radius: 搜索半径，要求15km，那就订成7km
    :param lon:
    :param lat:
    :return:
    """
    # 构建用户足迹相关
    user_locations = user_location_container.get_members_within_radius(lon, lat, radius)
    print(user_locations)
    positions = user_location_container.get_position(*user_locations)
    print(positions)
    footprint_id_2_position = {int(footprint_id): location for footprint_id, location in zip(user_locations, positions)}
    footprints = get_footprints_by_ids_db([int(item) for item in user_locations])

    result = {
        'footprints': [build_footprint_info(footprint, footprint_id_2_position.get(footprint.id))
                       for footprint in footprints]
    }
    # 构建企业活动相关
    activity_locations = activity_location_container.get_members_within_radius(lon, lat, radius)
    positions = user_location_container.get_position(*activity_locations)
    activity_id_2_position = {int(footprint_id): location for footprint_id, location in zip(activity_locations, positions)}
    activities = get_commercial_activities_by_ids_db([int(item) for item in activity_locations])

    result.update({
        'activities': [build_activity_info(activity, activity_id_2_position.get(activity.id))
                       for activity in activities]
    })
    return result
