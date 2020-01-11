import hashlib

from chat.models import ChatRecord


def get_conversation_id_by_user_ids(user_id_list):
    user_id_list.sort(key=lambda peer_id: int(peer_id))
    peer_id_list = map(str, user_id_list)
    peer_str = ":".join(peer_id_list)
    return hashlib.md5(peer_str).hexdigest()


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

