from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST

from commercial.manager.banner_manager import get_top_banner_db, build_top_banner
from commercial.manager.activity_manager import get_club_by_id_db, build_club_info, get_club_activities, \
    get_club_activities_info, get_commercial_activity_by_id_db, build_activity_detail, participate_activity
from user_info.manager.user_info_mananger import get_user_info_db
from utilities.request_utils import get_page_range
from utilities.response import json_http_success, json_http_error


@require_GET
def get_top_banner_view(request):
    """
    获取顶部banner广告信息
    :return: {
        title, image,  activity_id,
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
            id, name, image, address,
        }
        activities_info: [
            {
                activity_id, distance, title, created_time, activity_time, images_list,
                total_quota, participants: [
                    {
                        user_id, image
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
def get_club_activities_info_view(request):
    """
    获取俱乐部活动信息
    :param request: page
    :return:
    """
    page = int(request.GET.get('page', 1))
    club_id = int(request.GET.get('club_id'))
    start_num, end_num = get_page_range(page)
    activities_info = get_club_activities_info(club_id, start_num, end_num)
    return json_http_success(activities_info)


def get_activity_by_id_db(Ω):
    pass


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
        participants: [{user_id, image}]
    }
    """
    activity_id = request.GET['activity_id']
    activity = get_commercial_activity_by_id_db(activity_id)
    if not activity:
        return json_http_error('id错误')
    result = build_activity_detail(activity)
    return json_http_success(result)


@require_POST
@login_required
def participate_activity_view(request):
    """
    获取俱乐部信息
    URL[GET]: /commercial/participate_activity/
    """
    user = request.user
    activity_id = request.GET['activity_id']
    user_info = get_user_info_db(user)
    error_msg = participate_activity(activity_id, user_info.id)
    return json_http_success() if not error_msg else json_http_error(error_msg)
