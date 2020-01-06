from django.contrib.auth.decorators import login_required

from user_info.manager.user_info_mananger import update_my_profile_db
from utilities.date_time import str_to_datetime
from utilities.request_utils import get_data_from_request
from utilities.response import json_http_success, json_http_error


@login_required
def set_my_profile_view(request):
    """
    设置我的资料接口
    URL[POST]: /user_info/my_profile/edit/
    :param request: sex, avatar, location, nickname, birthday, signature, wechat_no, show_wechat_no
    :return:
    """
    post_data = get_data_from_request(request)

    sex = post_data['sex']
    avatar = post_data['avatar']
    location = post_data['location']
    nickname = post_data['nickname']
    birthday = post_data['birthday']
    wechat_no = post_data.get('wechat_no')
    show_wechat_no = bool(int(post_data['show_wechat_no']))
    signature = post_data['signature']

    birthday = str_to_datetime(birthday)
    user_info = update_my_profile_db(request.user, sex, avatar, location, nickname, wechat_no, show_wechat_no,
                                     signature, birthday)
    return json_http_success() if user_info else json_http_error()
