import hashlib
import json

from chat.models import ChatRecord, ChatConversationInfo
from user_info.manager.user_info_mananger import get_user_info_by_user_id_db
from utilities.date_time import datetime_to_str, FORMAT_DATETIME


def get_conversation_id_by_user_ids(user_id_list):
    user_id_list.sort(key=lambda peer_id: int(peer_id))
    peer_id_list = map(str, user_id_list)
    peer_str = ":".join(peer_id_list)
    return hashlib.md5(peer_str.encode('utf-8')).hexdigest()


def create_chat_record_db(conversation_id, content_json, send_id):
    """
    创建聊天记录
    :param conversation_id:
    :param content_json:
    {"type": "text", "text":"[文本]我的病情是这样的..."},
    {"type": "image", "url":"[图片]images/2011/09/06/da56b46bf19b.png"},
    {"type": "audio", "url":"[音频]audio/2011/09/06/da56b46bf19b.png", "duration": 1200《单位为毫秒》},
    :param content:
    :param send_id: 发送者的user_id
    :return:
    """
    record = ChatRecord.objects.create(conversation_id=conversation_id, addresser_id=send_id, content=content_json)
    return record


def get_conversation_info_by_conversation_id(conversation_id):
    try:
        return ChatConversationInfo.objects.get(conversation_id=conversation_id)
    except:
        return None


def get_or_create_conversation_info(conversation_id, send_id, receiver_id):
    """

    :param conversation_id:
    :param send_id:
    :param receiver_id:
    :return:
    """
    user_ids = [send_id, receiver_id]
    user_ids.sort()
    return ChatConversationInfo.objects.get_or_create(conversation_id=conversation_id,
                                                      defaults={'user_1_id': user_ids[0], 'user_2_id': user_ids[1]})


def build_conversation_list(user_id, conversation_id, conversation_info, start, end):
    """

    :param user_id:
    :param conversation_id:
    :param start:
    :param end:
    :return:
    """
    my_info = get_user_info_by_user_id_db(user_id)
    receiver_id = conversation_info.user_1_id if conversation_info.user_1_id != user_id else conversation_info.user_2_id
    receiver_info = get_user_info_by_user_id_db(receiver_id)
    chat_record = ChatRecord.objects.filter(conversation_id=conversation_id).order_by('-created_time')[start: end + 1]
    result = {'has_more': len(chat_record) > end - start}
    result.update({
        'content_list': [{'content': json.loads(chat.content), 'is_me': user_id == chat.addresser_id,
                          'created_time': datetime_to_str(chat.created_time, FORMAT_DATETIME)} for chat in chat_record]
    })
    result.update({'my_info': {'user_id': user_id, 'avatar': my_info.avatar},
                   'receiver_info': {'user_id': receiver_id, 'avatar': receiver_info.avatar}})
    return result
