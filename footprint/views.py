from django.contrib.auth.decorators import login_required

from api.manager.positon_manager import add_user_location
from footprint.manager.comment_manager import comment_footprint
from footprint.manager.footprint_manager import create_footprint_db, add_favor_db, get_footprint_by_id_db
from utilities.request_utils import get_data_from_request
from utilities.response import json_http_success, json_http_error


@login_required
def add_favor_view(request):
    """
    点赞view,点击两次的话就取消了
    URL[POST]: /api/footprint
    :param request: footprint id
    :return favor_num: 总的点赞数
    """
    post_data = get_data_from_request(request)
    footprint_id = post_data['footprint_id']
    favor_num = add_favor_db(footprint_id, request.user)
    return json_http_success({'favor_num': favor_num})


@login_required
def comment_footprint_view(request):
    """
    评论footprint，目前只能评论主贴
    :param request:
    :return:
    """
    post_data = get_data_from_request(request)
    footprint_id = post_data['footprint_id']
    comment = post_data['comment']
    success = comment_footprint(request.user, footprint_id, comment)
    return json_http_success() if success else json_http_error()


@login_required
def get_nearby_footprints_view(request):
    """
    获取附近的痕迹
    :param request: latitude, longitude
    :return:
    """
    return json_http_success()


@login_required
def post_footprint_view(request):
    """
    发布踪踪动态
    URL[POST]: /footprint/create/
    :param request:
    :return:
    """
    post_data = get_data_from_request(request)
    latitude = post_data.get('lat')
    longitude = post_data.get('lon')
    place = post_data['place']
    content = post_data['content']
    image_list_str = post_data['image_list']
    hide = bool(post_data.get('hide', False))

    footprint = create_footprint_db(request.user, content, latitude, longitude, place, image_list_str, hide)
    if latitude and longitude:
        add_user_location(footprint.id, longitude, latitude)
    return json_http_success()


# @login_required
# def get_footprint_detail_view(request):
#     """
#     获取痕迹详情
#     包含：
#     1.footprint详情
#     2.评论： 距离
#     3.评论的点赞数
#     :param request:
#     :return:
#     """
#     footprint_id = request.GET.get('footprint_id')
#     footprint = get_footprint_by_id_db(footprint_id)
#     footprint_detail =