# -*- encoding:utf-8 -*-
"""
微信小程序平台: 春雨医生

接入指南:
    https://mp.weixin.qq.com/debug/wxadoc/dev/api/api-login.html?t=20161109

"""
from __future__ import absolute_import

import copy
import datetime

from django.contrib.auth import login

from user_info.manager.user_info_mananger import get_user_info_by_open_id_db, create_user_info_db
from weixin.consts import APP_ID
from weixin.manager.login_manager import get_wechat_mini_session_by_code
from weixin.manager.mini_data_crypt import WechatMiniDataCryptV2, WXDataCryptErrorChoices


class WxminiAuthManager(object):
    """
    微信小程序验证管理类
    """
    @classmethod
    def decrypt_mini_user_info(cls, user_session_key, encrypted_data, iv):
        try:
            error_code, user_info = WechatMiniDataCryptV2(
                user_session_key, iv).decrypt_info(encrypted_data, expect_value=APP_ID)
            if error_code == WXDataCryptErrorChoices.OK:
                return user_info
        except:
            pass
        return {}

    @classmethod
    def decrypt_mini_group_id(cls, user_session_key, encrypted_data, iv):
        try:
            error_code, group_info = WechatMiniDataCryptV2(
                user_session_key, iv).decrypt_info(encrypted_data, verify_func=None)
            if error_code == WXDataCryptErrorChoices.OK:
                return group_info["openGId"]
        except:
            pass

        return ""

    @classmethod
    def decrypt_mini_phone(cls, user_session_key, encrypted_data, iv):
        """
        获取手机号，https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/getPhoneNumber.html
        :param user_session_key:
        :param encrypted_data: 待解密数据
        :param iv: 解密向量
        :return: pure phone number
        """
        try:
            # error_code, {phoneNumber, purePhoneNumber, countryCode, watermark}
            error_code, phone_info = WechatMiniDataCryptV2(
                user_session_key, iv).decrypt_info(encrypted_data, verify_func=None)
            if error_code == WXDataCryptErrorChoices.OK:
                return phone_info["purePhoneNumber"]
        except:
            pass

        return ""

    @classmethod
    def get_wx_mini_user_simple_info_by_code(cls, code):
        """
        通过code获得用户的open_id，由于微信小程序的用户验证机制是自成体系的。所以单独实现一套
        :return: (
        open_id 用户唯一标识,
        session_key 会话密钥,
        union_id 不同公众号下用户唯一标识
        )
        """
        try:
            result = get_wechat_mini_session_by_code(code)
            if not result.errcode:
                return result.openid, result.session_key, result.unionid
        except:
            pass
        return '', '', ''

    @classmethod
    def sync_wx_mini_user_info(cls, code, encrypted_data, iv):
        """
        同步小程序用户信息
        :return user, session_key
        """
        open_id, session_key, _ = cls.get_wx_mini_user_simple_info_by_code(code)
        if not open_id or not session_key:
            return None, "", False

        # 解密用户详细信息
        user_info = cls.decrypt_mini_user_info(session_key, encrypted_data, iv)
        # {unionid, nickname, headimgurl}
        user_info = cls.convert_wx_mini_user_info_to_wx_user_info(user_info)
        if not user_info:
            # 可能是 session_key 已过期，无法解密
            return None, "", False

        user_base_info = get_user_info_by_open_id_db(open_id)
        if user_base_info:
            return user_base_info.user, session_key
        user_base_info = create_user_info_db(open_id, user_info["nickname"], user_info["headimgurl"])
        return user_base_info.user, session_key

    @classmethod
    def convert_wx_mini_user_info_to_wx_user_info(cls, mini_user_info):
        """
        将微信小程序的用户信息格式转化为公众号的用户信息格式
        """
        if not mini_user_info:
            return {}
        return {
            'unionid': mini_user_info['unionId'],
            'nickname': mini_user_info['nickName'],
            'headimgurl': mini_user_info['avatarUrl'],
        }


class WxminiFormSourceType(EnumBase):
    """
    小程序form id来源
    有些页面没有问题id
    """
    GRAPH = EnumItem(OrderQueryType.GRAPH, u'图文')
    USER = EnumItem('user', u'用户')


class WxminiManager(object):
    """
    微信小程序管理类（春雨医生小程序）
    """
    MY_REDIS = redis

    # 小程序用户端在线状态管理 - user.id
    USER_ONLINE_KEY = u'mini_user_online_%s'
    USER_ONLINE_EX = 60 * 60 * 24

    # 小程序用户端客服反馈通知剩余次数 - user.id
    USER_FEEDBACK_NOTICE_TIMES_KEY = u'mini_user_feedback_times_%s'
    USER_FEEDBACK_NOTICE_TIMES_EX = 60 * 60 * 48

    @classmethod
    def set_form_id_for_problem(cls, problem_id, form_id):
        """
        保存小程序回调通知使用的form id，目前使用最新的form id。
        PARA:
            problem_id 问题ID（解密后的原始ID）
            form_id 改问题对应的最新的form_id
        """
        push_form_id(WxminiFormSourceType.GRAPH, problem_id, form_id)

    @classmethod
    def set_form_id_by_user(cls, user_id, form_id):
        """
        保存用户最新的form id，主要是为发推送使用
        """
        push_form_id(WxminiFormSourceType.USER, user_id, form_id)

    @classmethod
    def get_form_id_by_user(cls, user_id):
        """
        根据用户id获取form id
        :param user_id:
        :return:
        """
        return pop_form_id(WxminiFormSourceType.USER, user_id)

    @classmethod
    def get_form_id_for_problem(cls, problem_id):
        """
        读取小程序回调通知使用的form id。
        PARA:
            form_id 改问题对应的最新的form_id
        """
        return pop_form_id(WxminiFormSourceType.GRAPH, problem_id)

    @classmethod
    def build_wx_mini_reply_msg_data(cls, problem, reply_text, form_id, open_id, template_id):
        """
        构造微信小程序回调通知消息
        RET:
            "template_id": temp_id, 模板ID
            "page": "index",
            "form_id": form_id,
            "data": {
                keyword1 医生回复
                keyword2 医生姓名
                keyword3 所属科室
                keyword4 所属医院
                keyword5 医生职称
            },
            "emphasis_keyword": ""
        """
        doctor = problem.doctor
        hospital = api_get_hospital_by_id(doctor.hospital_id)
        return WechatMiniTemplateMessage(
            open_id=open_id,
            template_id=template_id,
            page=DOCTOR_REPLY_PAGE % ChunyuAES.encrypt(problem.id),
            form_id=form_id,
            item_info=[
                WechatTemplateMessageItemFullField("keyword1", reply_text, "#173177"),
                WechatTemplateMessageItemFullField("keyword2", doctor.name, "#173177"),
                WechatTemplateMessageItemFullField("keyword3", get_clinic_name(problem.clinic_no), "#173177"),
                WechatTemplateMessageItemFullField("keyword4", hospital.name, "#173177"),
                WechatTemplateMessageItemFullField("keyword5", doctor.title, "#173177"),
            ]
        )

    @classmethod
    def build_wx_mini_feedback_notice_data(cls, reply_text, open_id):
        """
        构造微信小程序客服回答通知消息
        """
        return WechatTextMessage(open_id=open_id, text=str(reply_text))

    @classmethod
    def build_wx_mini_collect_heart_msg_data(cls, problem, record, form_id, open_id):
        """
        构造微信小程序中收集爱心活动回调通知消息
        PARAM: problem 问题实例，record UserAttendActivityRecord 参加活动实例
               form_id 模版id 前端提供给服务器先保存着 open_id 用户的open_id
        RET:
            "template_id": temp_id, 模板ID
            "page": "index", 跳转的页面地址
            "form_id": form_id, 模版id，前端提供给服务器先保存着
            "data": {
                keyword1 状态
                keyword2 奖励名称
                keyword3 备注
            },
            "emphasis_keyword": "" 模板需要放大的关键词
        """
        status_str, reward_str, remark_str = get_collect_heart_send_mini_msg(problem, record)
        return WechatMiniTemplateMessage(
            open_id=open_id,
            template_id=COLLECT_HEART_TEMP_ID,
            page=COLLECT_HEART_PAGE % ChunyuAES.encrypt(problem.id),
            form_id=form_id,
            item_info=[
                WechatTemplateMessageItemFullField("keyword1", status_str, "#173177"),
                WechatTemplateMessageItemFullField("keyword2", reward_str, "#173177"),
                WechatTemplateMessageItemFullField("keyword3", remark_str, "#173177"),
            ]
        )

    @classmethod
    def build_wx_mini_activity_msg_data(cls, template_msg_id, form_id, page, status_str, reward_str, remark_str, open_id):
        """
        构造微信小程序中活动回调通知消息
        PARAM:
               template_msg_id 模版消息id
               form_id 模版id 前端提供给服务器先保存着 open_id 用户的open_id
               page: 跳转地址
               status_str 状态信息
               reward_str: 奖励信息
               open_id: open_id
        RET:
            "template_id": temp_id, 模板ID
            "page": "index", 跳转的页面地址
            "form_id": form_id, 模版id，前端提供给服务器先保存着
            "data": {
                keyword1 状态
                keyword2 奖励名称
                keyword3 备注
            },
            "emphasis_keyword": "" 模板需要放大的关键词
        """
        return WechatMiniTemplateMessage(
            open_id=open_id,
            template_id=template_msg_id,
            page=page,
            form_id=form_id,
            item_info=[
                WechatTemplateMessageItemFullField("keyword1", status_str, "#173177"),
                WechatTemplateMessageItemFullField("keyword2", reward_str, "#173177"),
                WechatTemplateMessageItemFullField("keyword3", remark_str, "#173177"),
            ]
        )

    @classmethod
    def build_wx_mini_newer_task_msg_data(cls, form_id, open_id, event, prize='', inviter_id=''):
        """
        构造微信小程序中新手任务活动回调通知消息
        PARAM: form_id 模版id 前端提供给服务器先保存着 open_id 用户的open_id
        RET:
            "template_id": temp_id, 模板ID
            "page": "index", 跳转的页面地址
            "form_id": form_id, 模版id，前端提供给服务器
            "data": {
                keyword1 状态
                keyword2 奖励名称
                keyword3 备注
            },
            "emphasis_keyword": "" 模板需要放大的关键词
        """
        message = copy.deepcopy(NEWER_TASK_EVENT_MESSAGE[event])
        page = copy.deepcopy(NEWER_TASK_EVENT_PAGE[event])
        if prize and event in [NewerTaskEvent.NEWER_TASK_INVITATION, NewerTaskEvent.NEWER_TASK_2]:
            message['prize_str'] = message['prize_str'] % prize
        if inviter_id and event in [NewerTaskEvent.NEWER_TASK_2, NewerTaskEvent.NEWER_TASK_INVITATION,
                                    NewerTaskEvent.NEWER_TASK_INVITATION_ERROR]:
            page = page % inviter_id
        return WechatMiniTemplateMessage(
            open_id=open_id,
            template_id=NEWER_TASK_TEMP_ID,
            page=page,
            form_id=form_id,
            item_info=[
                WechatTemplateMessageItemFullField("keyword1", message['status_str'], "#173177"),
                WechatTemplateMessageItemFullField("keyword2", message['prize_str'], "#173177"),
                WechatTemplateMessageItemFullField("keyword3", message['remark_str'], "#173177"),
            ]
        )

    @classmethod
    def build_wx_mini_topic_msg_data(cls, form_id, open_id, topic):
        """
        构造医生话题模板消息
        :param form_id 小程序的form_id
        :param open_id
        :param topic DoctorTopic
        """
        return WechatMiniTemplateMessage(
            open_id=open_id,
            template_id=DOCTOR_TOPIC_TEMP_ID,
            page=DOCTOR_TOPIC_PAGE % topic.id,
            form_id=form_id,
            item_info=[
                WechatTemplateMessageItemFullField("keyword1", u'%s' % topic.get_title_content(),
                                                   "#173177"),
                WechatTemplateMessageItemFullField("keyword2", u'%s' % topic.doctor.name,
                                                   "#173177"),
                WechatTemplateMessageItemFullField("keyword3", u'你关注的医生发布了一篇话题，快来看看吧～', "#173177"),
            ]
        )

    @classmethod
    def build_wx_mini_news_msg_data(cls, form_id, open_id, news):
        """
        构造医生话题模板消息
        :param form_id 小程序的form_id
        :param open_id
        :param news 咨询信息
        """
        return WechatMiniTemplateMessage(
            open_id=open_id,
            template_id=NEWS_TEMP_ID,
            page=NEWS_PAGE % news['id'],
            form_id=form_id,
            item_info=[
                WechatTemplateMessageItemFullField("keyword1", u'每日健康科普',
                                                   "#173177"),
                WechatTemplateMessageItemFullField("keyword2", u'《%s》' % news.get('title', ''),
                                                   "#173177"),
                WechatTemplateMessageItemFullField("keyword3", u'%s' % news.get('digest', ''), "#173177"),
            ]
        )

    @classmethod
    def build_wx_mini_sale_service_msg_data(cls, form_id, open_id, conversation_id, assistant_name, reply_text, reply_time=None):
        reply_time = reply_time or datetime_to_str(datetime.datetime.now(), FORMAT_DATETIME)
        return WechatMiniTemplateMessage(
            open_id=open_id,
            template_id=SALE_SERVICE_TEMP_ID,
            page=SALE_SERVICE_PAGE % conversation_id,
            form_id=form_id,
            item_info=[
                WechatTemplateMessageItemFullField("keyword1", assistant_name, "#173177"),
                WechatTemplateMessageItemFullField("keyword2", reply_time, "#173177"),
                WechatTemplateMessageItemFullField("keyword3", reply_text, "#173177"),
            ]
        )

    @classmethod
    def build_wx_mini_qa_service_evaluate_notice_msg_data(cls, form_id, open_id, problem):
        problem_ask = truncate_unicode_str(problem.ask, PROBELM_CONTENT_RETURN_LEN)
        close_time_str = datetime_to_str(problem.close_time, FORMAT_DATETIME)
        return WechatMiniTemplateMessage(
            open_id=open_id,
            template_id=QA_SERVICE_EVALUATE_NOTICE_TEMP_ID,
            page=QA_SERVICE_PAGE.format(problem_id=problem.id),
            form_id=form_id,
            item_info=[
                WechatTemplateMessageItemFullField("keyword1", problem.doctor.name, COLOR_BLUE),
                WechatTemplateMessageItemFullField("keyword2", close_time_str, COLOR_BLUE),
                WechatTemplateMessageItemFullField("keyword3", problem_ask, COLOR_BLUE),
                WechatTemplateMessageItemFullField("keyword4", QA_SERVICE_EVALUATE_NOTICE_CONTENT, COLOR_BLUE),
            ]
        )

    @classmethod
    def build_wx_mini_advanced_graph_timeout_refund_notice_msg_data(cls, form_id, open_id, problem):
        return WechatMiniTemplateMessage(
            open_id=open_id,
            template_id=ADVANCED_GRAPH_TIMEOUT_REFUND_TEMP_ID,
            page=QA_SERVICE_PAGE.format(problem_id=problem.id),
            form_id=form_id,
            item_info=[
                WechatTemplateMessageItemFullField("keyword1", USER_REFUND_TO_CLINIC_MSG, COLOR_BLUE),
                WechatTemplateMessageItemFullField("keyword2", '{:.1f}元'.format(problem.get_price()), COLOR_BLUE),
            ]
        )

    @classmethod
    def build_wx_mini_tel_notify_msg_data(cls, open_id, form_id, mini_platform_name,
                                          service_id, ask_time_str, problem_ask, doctor_name=None):
        """
        电话咨询模板消息构建

        春雨医生小程序和医生端小程序复用
        """
        if not open_id or not form_id or not service_id or not ask_time_str or not problem_ask or \
                mini_platform_name not in (WEIXIN_PUBLIC_PLATFORM_NAME.WEIXIN_MINI,
                                           WEIXIN_PUBLIC_PLATFORM_NAME.WEIXIN_DOCTOR_MINI):
            return None

        if doctor_name is None and mini_platform_name == WEIXIN_PUBLIC_PLATFORM_NAME.WEIXIN_MINI:
            raise ValueError("电话服务医生姓名不能为空")

        problem_ask = truncate_unicode_str(problem_ask, PROBELM_CONTENT_RETURN_LEN)

        if mini_platform_name == WEIXIN_PUBLIC_PLATFORM_NAME.WEIXIN_MINI:
            template_id = USER_TEL_NOTIFY_TEMP_ID
            page = USER_TEL_PAGE.format(service_id)
            data = [
                ("keyword1", doctor_name),
                ("keyword2", ask_time_str),
                ("keyword3", problem_ask),
            ]
        else:
            template_id = DOCTOR_TEL_NOTIFY_TEMP_ID
            page = DOCTOR_TEL_PAGE.format(service_id)
            data = [
                ("keyword1", ask_time_str),
                ("keyword2", problem_ask),
            ]

        return WechatMiniTemplateMessage(
            open_id=open_id,
            template_id=template_id,
            page=page,
            form_id=form_id,
            item_info=[
                WechatTemplateMessageItemFullField(name, value, COLOR_BLUE)
                for name, value in data
            ]
        )

    @classmethod
    def set_user_online(cls, user_id):
        """
        小程序记录用户上线状态
        """
        cls.MY_REDIS.setex(cls.USER_ONLINE_KEY % user_id, cls.USER_ONLINE_EX, True)

    @classmethod
    def set_user_offline(cls, user_id):
        """
        小程序记录用户上线状态
        """
        cls.MY_REDIS.delete(cls.USER_ONLINE_KEY % user_id)

    @classmethod
    def is_user_online(cls, user_id):
        """
        查看用户在线状态
        """
        return cls.MY_REDIS.exists(cls.USER_ONLINE_KEY % user_id)

    @classmethod
    def set_feedback_notice_times(cls, user_id, times=3):
        """
        设置小程序用户发送客服回调通知的剩余次数
        """
        if times < 0:
            times = 0
        cls.MY_REDIS.setex(cls.USER_FEEDBACK_NOTICE_TIMES_KEY % user_id, cls.USER_FEEDBACK_NOTICE_TIMES_EX, times)

    @classmethod
    def get_feedback_notice_times(cls, user_id):
        """
        获取小程序用户发送客服回调通知的剩余次数
        """
        times = cls.MY_REDIS.get(cls.USER_FEEDBACK_NOTICE_TIMES_KEY % user_id)
        if times:
            return int(times)
        return 0


def build_session_key_of_wx_mini_session_key():
    """
    构造 session key
    """
    return'zongzong_weixin_session_key'


def get_wx_mini_session_key_by_request(request):
    """
    从 session 中获取小程序 session_key
    :param request:
    :param app_name:
    :return:
    """
    key = 'zongzong_weixin_sessuib'
    return request.session.get(key, "")


def set_wx_mini_session_key_by_request(request, wx_session_key):
    """
    保存小程序 session_key 到 session 中
    :param request:
    :param app_name:
    :param wx_session_key:
    """
    key = build_session_key_of_wx_mini_session_key()
    request.session[key] = wx_session_key


def wx_mini_request_login(request, wx_user, wx_session_key, need_session_id=True):
    """
    执行微信登录逻辑
    :param request:
    :param wx_user:
    :param app_name:
    :param wx_session_key:
    :param need_session_id: 需要同步返回 session_id
    :return:
    """
    login(request, wx_user)
    if need_session_id and not request.session.session_key:
        #  需要重新生成 session_id
        request.session.save()
    set_wx_mini_session_key_by_request(request, wx_session_key)
