from django.contrib.auth.decorators import login_required

from user_info.consts import SexChoices
from user_info.manager.user_info_mananger import get_user_info_db, update_my_profile_db, get_user_tag_list_db, \
    update_user_tag_list_db
from utilities.date_time import date_to_str, FORMAT_DATE, str_to_date
from utilities.request_utils import get_data_from_request
from utilities.response import json_http_success, json_http_error


@login_required
def get_my_profile_view(request):
    """
    获取我的资料接口
    URL[GET]: /api/user/profile/
    """
    user_info = get_user_info_db(request.user)
    return json_http_success({
        'image': user_info.image,
        'nickname': user_info.nickname,
        'birthday': date_to_str(user_info.birthday, FORMAT_DATE),
        'sex': SexChoices.verbose(user_info.sex),
        'wechat_no': '',
        'signature': user_info.signature,
    })


@login_required
def set_my_profile_view(request):
    """
    设置我的资料接口
    URL[POST]: /api/user/set_profile/
    :param request: nickname, birthday, sex, show_wechat_no
    :return:
    """
    post_data = get_data_from_request(request)
    nickname = post_data['nickname']
    birthday = post_data['birthday']
    sex = post_data['sex']
    show_wechat_no = bool(int(post_data['show_wechat_no']))
    user_info = update_my_profile_db(request.user, nickname, str_to_date(birthday), SexChoices.get_value_by_verbose(sex),
                                     show_wechat_no)
    return json_http_success() if user_info else json_http_error()


@login_required
def set_my_tags_view(request):
    """
    设置我展示出的tag
    URL[POST]: /api/user/set_tag_list/
    :param request:  tag_list: []
    """


@login_required
def get_tag_list_view(request):
    """
    URL[GET]: /api/user/tag_list/
    :param request: user_id or None
    :return: {'tag_list': list}
    如果传user_id则是获取别人的tag，否则为自己的
    """
    user_id = request.GET.get('user_id')
    result = get_user_tag_list_db(user_id if user_id else request.user)
    return json_http_success({'tag_list': result})


@login_required
def set_tag_list_view(request):
    """
    URL[GET]: /api/user/tag_list/
    :param request: user_id or None
    :return: {'tag_list': list}
    如果传user_id则是获取别人的tag，否则为自己的
    """
    post_data = get_data_from_request(request)
    tag_list_str = post_data['tag_list']
    if not isinstance(tag_list_str, str):
        return json_http_error('tag list must be a json list')
    update_user_tag_list_db(request.user, tag_list_str)
    return json_http_success()
