import hashlib
import json
import time

from django.db import models


class ChatRecord(models.Model):
    """
        无限聊天消息记录
        content类型注释：
        {"type": "text", "text":"[文本]我的病情是这样的..."},
        {"type": "image", "url":"[图片]images/2011/09/06/da56b46bf19b.png"},
        {"type": "audio", "url":"[音频]audio/2011/09/06/da56b46bf19b.png", "duration": 1200《单位为毫秒》},
        {"type": "wap", "title":"[wap广告]这里需要插入一个广告"， "web_title":"这里需要插入一个广告"， "url":"www.chunyu.me", "portrait":"头像"},
        {"type": "online_referral", "text":"[在线转诊]为您在线转诊至春雨儿科...", "referral_id": 120},
        {"type": "offline_referral", "text":"[在线转诊]为您线下转诊至春雨儿科...", "appointment_id": 120},
        {"type":"family_profile_reminder","url":"","duration":0}
        {"type": "busy_reminder", "text": "您的私人医生正处于门诊中或忙碌状态，未能立即回复请您见谅。如需立即咨询，可联系在线医助"}   # 给用户推送
        {"type": "call_information", "status": s/f, "text": "%s 呼叫 %s，未接通/"}
        {"type": "purchase_ehr_record", "text": "XX为YY购买了健康档案"}
        {"type":"clinic_appointment","appointment_doctor_id":2,"appointment_doctor_name":"周玲"}
    """
    addresser_id = models.PositiveIntegerField(verbose_name=u'发送者user_id')
    conversation_id = models.CharField(max_length=100, help_text='对话id号', db_index=True)

    content = models.TextField(default='{}', help_text='对话内容, json串')
    is_delete = models.BooleanField(default=False, help_text='辅助用户删除功能')

    created_time = models.DateTimeField(auto_now_add=True, db_index=True)
    last_modified = models.DateTimeField(auto_now=True)

    def get_timestamp_microsecond(self):
        """
        返回时间戳，微秒级
        """
        return int(1000000 * time.mktime(self.created_time.timetuple())) \
            + self.created_time.microsecond

    @staticmethod
    def get_conversation_id_by_peerids(peer_id_list):
        """
            通过一堆peer_id获取他们的conversation_id
        """
        peer_id_list.sort(key=lambda peer_id: int(peer_id))
        peer_id_list = map(str, peer_id_list)
        peer_str = ":".join(peer_id_list)
        return hashlib.md5(peer_str).hexdigest()

    def get_content(self):
        """
        获取消息内容
        RET:content
        """
        content_dict = json.loads(self.content)
        content_type = content_dict.get('type')
        if content_type in ['text']:
            return content_dict.get('text')
        elif content_type in ['image', 'audio']:
            return content_dict.get('url')
        else:
            return ''


class ChatConversationInfo(models.Model):
    """
    会话的基础信息
    """
    conversation_id = models.CharField(max_length=100, unique=True)
    user_1_id = models.IntegerField(default=0, help_text="用户1id")
    user_2_id = models.IntegerField(default=0, help_text="用户2id")

    created_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("conversation_id", )
