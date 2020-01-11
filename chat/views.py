from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from chat.manager.chat_manager import get_conversation_id_by_user_ids, create_chat_record_db
from chat.manager.message_manager import ConversationMessageManager
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
def post_content_view(request):
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


# @require_GET
# @login_required
