from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from user_info.manager.user_info_mananger import update_my_profile_db, get_user_info_by_user_id_db, \
    get_user_brief_profile
from utilities.date_time import str_to_datetime, datetime_to_str
from utilities.request_utils import get_data_from_request
from utilities.response import json_http_success, json_http_error


@csrf_exempt
@login_required
def set_my_profile_view(request):
    """
    设置我的资料接口
    URL[POST]: /user_info/my_profile/edit/
    :param request: sex, avatar, location, nickname, birthday, signature, wechat_no, show_wechat_no
    :return:
    """
    post_data = get_data_from_request(request)

    sex = post_data.get('sex')
    avatar = post_data.get('avatar')
    location = post_data.get('location')
    nickname = post_data.get('nickname')
    birthday = post_data.get('birthday')
    wechat_no = post_data.get('wechat_no')
    show_wechat_no = post_data.get('show_wechat_no')
    if show_wechat_no is not None:
        show_wechat_no = bool(int(show_wechat_no))
    signature = post_data.get('signature')
    if birthday:
        birthday = str_to_datetime(birthday)
    user_info = update_my_profile_db(request.user, sex, avatar, location, nickname, wechat_no, show_wechat_no,
                                     signature, birthday)
    return json_http_success() if user_info else json_http_error()


@login_required
def get_my_profile_view(request):
    """
    获取我的资料
    URL[GET]: /user_info/my_profile/
    :param request:
    :return:
    """
    user_info = get_user_info_by_user_id_db(request.user.id)
    result = {
        'avatar': user_info.avatar or '',
        'nickname': user_info.nickname or '',
        'birthday': datetime_to_str(user_info.birthday) if user_info.birthday else '',
        'location': user_info.location or '',
        'sex': user_info.sex,
        'wechat_no': user_info.wechat_no,
        'show_wechat_no': user_info.show_wechat_no,
        'signature': user_info.signature,
        'user_id': request.user.id,
    }
    return json_http_success(result)


@login_required
def get_user_brief_profile_view(request):
    """
    获取用户小窗口简介
    1.用户个人资料
    2.用户最新一条票圈
    URL[GET]: /user_info/get_user_info/
    :param request: user_id
    """
    user_id = request.GET['user_id']
    if not user_id:
        return json_http_error('')
    return json_http_success({'user_info': get_user_brief_profile(user_id)})

