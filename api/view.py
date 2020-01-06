from django.views.decorators.http import require_GET, require_POST

from api.manager.view_manager import get_nearby_activity
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
            {user_id, name, image, time, lat, lon}
        ]
        activities: [
            {activity_id, name, image, description, quota}
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



