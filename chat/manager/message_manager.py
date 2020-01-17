import datetime

from redis_utils.container.api_redis_client import redis
from user_info.manager.user_info_mananger import get_user_info_by_user_id_db
from utilities.date_time import datetime_to_str, FORMAT_DATETIME


class ConversationMessageManager(object):
    """
    对话的首条内容管理类
    """
    @classmethod
    def build_redis_key(cls, user_id):
        """
        返回缓存主key
        """
        return "conversation_user_{}".format(user_id)

    @classmethod
    def add_message(cls, to_user_id, from_user_id, conversation_id, content):
        """
        包括添加自己的消息和另外那个人的消息
        message信息包括： {conversation_id, avatar, content, created_time, has_badge}
        :param from_user_id:
        :param to_user_id:
        :param conversation_id:
        :param content:
        :return:
        """
        user_info = get_user_info_by_user_id_db(to_user_id)
        message = {
            'conversation_id': conversation_id, 'avatar': user_info.avatar, 'last_message': content, 'has_new': 1,
            'time': datetime_to_str(datetime.datetime.now(), FORMAT_DATETIME), 'username': user_info.nickname
        }
        redis.hset_pickle(cls.build_redis_key(to_user_id), conversation_id, message)

        # 更新信息
        message['has_new'] = 0
        redis.hset_pickle(cls.build_redis_key(from_user_id), conversation_id, message)

    @classmethod
    def get_all_message_list(cls, user_id):
        all_message = redis.hvals_pickle(cls.build_redis_key(user_id))
        all_message.sort(key=lambda item: item['time'])
        return all_message

    @classmethod
    def get_message(cls, user_id, conversation_id):
        return redis.hget_pickle(cls.build_redis_key(user_id), conversation_id)

    @classmethod
    def clear_badge(cls, user_id, conversation_id):
        message = cls.get_message(user_id, conversation_id)
        message['has_new'] = 0
        redis.hset_pickle(cls.build_redis_key(user_id), conversation_id, message)
