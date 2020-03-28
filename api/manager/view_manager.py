from geopy.distance import geodesic

from api.manager.positon_manager import user_location_container, activity_location_container
from commercial.manager.db_manager import get_commercial_activities_by_ids_db
from footprint.manager.footprint_manager import get_footprints_by_ids_db, is_user_favored
from footprint.models import FlowType
from utilities.date_time import time_format, datetime_to_str


def build_footprint_info(footprint, position):
    return {
        'footprint_id': footprint.id,
        'time': time_format(footprint.created_time),
        'user_id': footprint.user_id,
        'name': footprint.name,
        'avatar': footprint.avatar,
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
    positions = user_location_container.get_position(*user_locations)
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


def build_footprint_for_flow(footprint, user_id, lon, lat):
    return {
        'flow_id': footprint.id, 'flow_type': FlowType.FOOTPRINT, 'avatar': footprint.avatar,
        'name': footprint.name, 'distance': geodesic((lat, lon), (footprint.lat, footprint.lon)).meters,
        'location': footprint.location,
        'post_time': datetime_to_str(footprint.created_time), 'content': footprint.content,
        'image_list': footprint.image_list,
        'user_id': footprint.user_id,
        'favored': is_user_favored(user_id, footprint.id, FlowType.FOOTPRINT),
        'favor_num': footprint.favor_num,
    }


def build_activity_for_flow(activity, user_id, lon, lat):
    club = activity.club
    return {
        'flow_id': activity.id, 'flow_type': FlowType.ACTIVITY, 'avatar': club.avatar.url,
        'name': club.name, 'distance': geodesic((lat, lon), (activity.lat, activity.lon)).meters,
        'location': activity.address,
        'post_time': datetime_to_str(activity.created_time), 'content': activity.introduction,
        'image_list': activity.image_list,
        'favored': is_user_favored(user_id, activity.id, FlowType.ACTIVITY),
        'favor_num': activity.favor_num,
    }


def build_flows_detail(flows, user_id, lon, lat):
    """
    构建事件流详情，需要针对足迹和活动分别build
    """
    footprint_flows = filter(lambda item: item.flow_type == FlowType.FOOTPRINT, flows)
    activity_flows = filter(lambda item: item.flow_type == FlowType.ACTIVITY, flows)
    footprints = get_footprints_by_ids_db([item.flow_id for item in footprint_flows])
    activities = get_commercial_activities_by_ids_db([item.flow_id for item in activity_flows])
    footprint_details = [build_footprint_for_flow(footprint, user_id, lon, lat) for footprint in footprints]
    activity_details = [build_activity_for_flow(activity, user_id, lon, lat) for activity in activities]
    total_flow = footprint_details + activity_details
    return sorted(total_flow, key=lambda flow: flow['post_time'], reverse=True)
