from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST

from api.manager.view_manager import get_nearby_activity, build_flows_detail
from footprint.manager.footprint_manager import get_flows_db
from utilities.request_utils import get_page_range
from utilities.response import json_http_response, json_http_success, json_http_error


def hello_view(request):
    """
    欢迎接口
    """
    return json_http_response('welcome to zongzong! ')


@require_GET
def get_nearby_activities_view(request):
    """
    URL[GET]: /api/get_nearby_activities/
    :return: {
        user_locations: [
            {user_id, name, avatar, time, lat, lon}
        ]
        activities: [
            {activity_id, name, avatar, description, quota}
        ]
    }
    """
    lon = request.GET.get('lon')
    lat = request.GET.get('lat')
    radius = request.GET.get('radius', 7)
    if not lon or not lat:
        return json_http_error('必须传经纬度')
    result = get_nearby_activity(float(lon), float(lat), float(radius))
    return json_http_success(result)


@login_required
def discovery_view(request):
    """
    URL[GET]: /api/discovery/
    获取本市的所有活动，包括商家活动和足迹
    :param request: page
    :return: {
        items: [{flow_id, flow_type, avatar, name, distance, location, post_time, content, image_list}, ...]
    }
    """
    page = int(request.GET.get('page', 1))
    start_num, end_num = get_page_range(page)
    flows = get_flows_db(start_num, end_num)
    result = build_flows_detail(flows)
    return json_http_success({'items': result})
