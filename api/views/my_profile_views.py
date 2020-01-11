from django.contrib.auth.decorators import login_required

from user_info.consts import SexChoices
from user_info.manager.user_info_mananger import get_user_info_by_user_id_db
from utilities.date_time import date_to_str, FORMAT_DATE
from utilities.response import json_http_success


@login_required
def get_my_profile_view(request):
    """
    获取我的资料接口
    URL[GET]: /api/user/profile/
    """
    user_info = get_user_info_by_user_id_db(request.user.id)
    return json_http_success({
        'avatar': user_info.avatar,
        'nickname': user_info.nickname,
        'birthday': date_to_str(user_info.birthday, FORMAT_DATE),
        'sex': SexChoices.verbose(user_info.sex),
        'wechat_no': '',
        'signature': user_info.signature,
    })
