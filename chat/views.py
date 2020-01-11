from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from chat.manager.chat_manager import get_conversation_id_by_user_ids, create_chat_record_db
from chat.manager.message_manager import ConversationMessageManager
from commercial.manager.activity_manager import get_club_by_id_db, build_club_info, \
    get_club_activities_info, get_commercial_activity_by_id_db, build_activity_detail, participate_activity
from user_info.manager.user_info_mananger import get_user_info_by_user_id_db
from utilities.request_utils import get_page_range, get_data_from_request
from utilities.response import json_http_success, json_http_error


@require_GET
@login_required
def get_my_conversation_list_view(request):
    """
    获取我的对话列表
    URL[GET]: /chat/conversation_list/
    :return: {
        "conversation_list": [
            {
                "avatar": "",
                "last_message": "",
                "has_new": "",
                "username": "",
                "conversation_id": ""
            }
        ]
    }
    """
    my_conversation_info_list = ConversationMessageManager.get_all_message_list(request.user.id)
    return json_http_success({'conversation_list': my_conversation_info_list})


@csrf_exempt
@require_POST
@login_required
def post_content(request):
    """
    发送信息
    URL[POST]: /chat/post_content/
    :param request: conversation_id， content_type， content
    """
    data = get_data_from_request(request)
    receiver_id = int(data.get('receiver_id'))
    conversation_id = data.get('conversation_id')
    if not receiver_id and not  conversation_id:
        return json_http_error('参数错误')
    conversation_id = conversation_id or get_conversation_id_by_user_ids([receiver_id, request.user.id])
    content = data['content_json']
    chat_record = create_chat_record_db(conversation_id, content, request.user.id)
    # 发推送、更新badge、
    return json_http_success()


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
    user_info = get_user_info_by_user_id_db(user.id)
    error_msg = participate_activity(activity_id, user_info.id)
    return json_http_success() if not error_msg else json_http_error(error_msg)
