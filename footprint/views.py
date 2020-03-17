import logging

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from api.manager.positon_manager import add_user_location
from footprint.manager.comment_manager import create_comment_db
from footprint.manager.footprint_manager import create_footprint_db, add_favor_db, \
    build_footprint_detail, get_footprint_by_id_db, get_footprints_by_user_id_db, update_comment_num_db, \
    build_footprint_list_info
from footprint.models import FlowType
from utilities.content_check import is_content_valid
from utilities.image_check import is_image_valid
from utilities.request_utils import get_data_from_request, get_page_range
from utilities.response import json_http_success, json_http_error


@csrf_exempt
@login_required
def add_favor_view(request):
    """
    点赞view,点击两次的话就取消了
    URL[POST]: /footprint/favor/
    :param request: footprint id
    :return favor_num: 总的点赞数
    """
    post_data = get_data_from_request(request)
    footprint_id = post_data['footprint_id']
    favor_num = add_favor_db(footprint_id, FlowType.FOOTPRINT, request.user.id)
    return json_http_success({'favor_num': favor_num})


@csrf_exempt
@login_required
def comment_footprint_view(request):
    """
    URL[POST]: /footprint/comment/
    评论footprint，目前只能评论主贴
    :param request:
    :return:
    """
    post_data = get_data_from_request(request)
    footprint_id = post_data['footprint_id']
    comment = post_data['comment']
    if not is_content_valid(comment):
        return json_http_error('请注意用词')
    success = create_comment_db(request.user, footprint_id, comment)
    if success:
        comment_num = update_comment_num_db(footprint_id)
        return json_http_success({'comment_num': comment_num})
    return json_http_error()


@csrf_exempt
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
    location = post_data.get('location')
    content = post_data['content']
    if not is_content_valid(content):
        return json_http_error('请注意用词')
    image_list = post_data['image_list']
    for image in image_list:
        if not is_image_valid(image):
            return json_http_error('请文明发言')
    hide = bool(int(post_data.get('hide', 0)))
    footprint = create_footprint_db(request.user, content, latitude, longitude, location, image_list, hide)
    if latitude and longitude:
        add_user_location(footprint.id, longitude, latitude)
    return json_http_success()


@login_required
def get_footprint_detail_view(request):
    """
    /footprint/detail/
    获取痕迹详情
    包含：
    1.footprint详情
    2.评论： 距离
    3.评论的点赞数
    :param request:
    :return:
    """
    footprint_id = request.GET.get('footprint_id')
    footprint = get_footprint_by_id_db(footprint_id)
    footprint_detail = build_footprint_detail(footprint, request.user.id)
    return json_http_success(footprint_detail)


@login_required
def get_user_footprint_track_view(request):
    """
    /footprint/user_track/
    :param request:
    :return:
    """
    user_id = int(request.GET.get('user_id', 0)) or request.user.id
    page = int(request.GET.get('page', 0))
    lat = float(request.GET.get('lat', 0))
    lon = float(request.GET.get('lon', 0))
    start, end = get_page_range(page, 5)
    footprints = get_footprints_by_user_id_db(user_id, start, end)
    has_more = len(footprints) > 5
    footprints = footprints[:5]
    result = build_footprint_list_info(footprints, request.user.id, lat, lon)
    return json_http_success({'footprints': result, 'has_more': has_more})
