from django.contrib.auth.decorators import login_required

from footprint.manager.footprint_manager import get_user_newest_footprint_db, build_user_footprint
from user_info.manager.user_info_mananger import get_user_brief_profile
from utilities.response import json_http_error, json_http_success


@login_required
def get_user_brief_profile_view(request):
    """
    获取用户小窗口简介
    1.用户个人资料
    2.用户最新一条票圈
    URL[GET]: /api/get_brief_introduction/
    :param request: user_id
    """
    user_id = request.GET['user_id']
    if not user_id:
        return json_http_error('')
    newest_footprint = get_user_newest_footprint_db(user_id)
    return json_http_success({'user_info': get_user_brief_profile(user_id),
                              'footprint_info': build_user_footprint(newest_footprint)})


