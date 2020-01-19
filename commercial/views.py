from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from commercial.manager.banner_manager import get_top_banner_db, build_top_banner
from commercial.manager.activity_manager import build_club_info, \
    build_activity_detail, participate_activity, \
    build_activity_brief_info
from commercial.manager.db_manager import get_commercial_activity_by_id_db, get_commercial_activities_by_club_id_db, \
    get_club_by_id_db
from footprint.manager.footprint_manager import add_favor_db
from footprint.models import FlowType
from user_info.manager.user_info_mananger import get_user_info_by_user_id_db
from utilities.request_utils import get_page_range, get_data_from_request
from utilities.response import json_http_success, json_http_error


@require_GET
def get_top_banner_view(request):
    """
    获取顶部banner广告信息
    :return: {
        title, avatar,  activity_id,
    }
    """
    banner = get_top_banner_db()
    result = {} if not banner else build_top_banner(banner)
    return json_http_success(result)


@require_GET
@login_required
def get_club_info_view(request):
    """
    获取俱乐部信息
    URL[GET]: /commercial/get_club_info/
    :param request:
    :return: {
        club_info: {
            id, name, avatar, address,
        }
        activities_info: [
            {
                activity_id, distance, title, created_time, activity_time, images_list,
                total_quota, participants: [
                    {
                        user_id, avatar
                    },
                ]
            },

        ]

    }
    """
    club_id = int(request.GET['club_id'])
    club = get_club_by_id_db(club_id)
    if not club:
        return json_http_error('id错误')
    club_info = build_club_info(club)
    return json_http_success(club_info)


@require_GET
@login_required
def activity_detail_view(request):
    """
    获取活动详细信息
    URL[GET]: /commercial/get_activity_detail/
    :return: {
        top_image,
        title,
        club_name,
        avatar,
        telephone,
        introduction,
        image_list,
        detail,
        address,
        time_detail,
        description,
        total_quota,
        participants: [{user_id, avatar}]
    }
    """
    activity_id = request.GET['activity_id']
    activity = get_commercial_activity_by_id_db(activity_id)
    if not activity:
        return json_http_error('id错误')
    result = build_activity_detail(activity, request.user.id)
    return json_http_success(result)


@csrf_exempt
@require_POST
@login_required
def participate_activity_view(request):
    """
    获取俱乐部信息
    URL[GET]: /commercial/subscribe_activity/
    """
    user = request.user
    post_data = get_data_from_request(request)
    activity_id = post_data['activity_id']
    name = post_data['name']
    cellphone = post_data['cellphone']
    num = int(post_data['cellphone'])
    hint = post_data['hint']
    user_info = get_user_info_by_user_id_db(user.id)
    error_msg = participate_activity(activity_id, user_info.id, name, cellphone, num, hint)
    return json_http_success() if not error_msg else json_http_error(error_msg)


@require_GET
@login_required
def get_club_activities_info(request):
    """
    URL[GET]: /commercial/get_club_activity_info/
    :param request:
    :return:
    """
    club_id = int(request.GET['club_id'])
    page = int(request.GET.get('page', 1))
    lat = float(request.GET.get('lat', 0))
    lon = float(request.GET.get('lon', 0))
    start, end = get_page_range(page, 5)
    club = get_club_by_id_db(club_id)
    if not club:
        return json_http_error('错误')
    activities = get_commercial_activities_by_club_id_db(club_id, start, end)

    return json_http_success({'activity_list': [build_activity_brief_info(activity, request.user.id, lon, lat) for
                                                activity in activities],
                              'avatar': club.avatar})


@require_POST
@login_required
def favor_activity_view(request):
    """
    给活动点赞
    URL[POST]: /commercial/favor_activity/
    :param request:
    :return:
    """
    post_data = get_data_from_request(request)
    activity_id = post_data['activity_id']
    favor_num = add_favor_db(activity_id, FlowType.ACTIVITY, request.user.id)
    return json_http_success({'favor_num': favor_num})
