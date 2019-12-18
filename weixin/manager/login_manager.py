# -*- coding:utf-8 -*-

from __future__ import absolute_import

import requests
import simplejson as json
from django.utils.decorators import available_attrs
from django.utils.functional import wraps

from weixin.consts import SYNC_REQUEST_TIME_OUT, WEIXIN_MINI_CODE_TO_SESSION, APP_ID, APP_SECRET


def wechat_login_required_impl(func=None, conf=None, login_func=None, extra_user_test_func=None):
    """
    只适用于微信，其他浏览器会提示『请在微信下打开』
    view在微信浏览器中要求必须登陆
    :param func:
    :param conf: @see WeChatCommonConf
    :param login_func: 登陆函数,接收 (request, conf, open_id, access_token) 参数
    :param extra_user_test_func: 用户检测函数。接受参数 (user, conf)；如果返回值为 False, 则认为当前的用户检测失败，需要重新登陆
    :return:
    """
    actual_decorator = _user_passes_test(
        lambda u: u.is_authenticated(),
        conf=conf,
        login_func=login_func,
        extra_user_test_func=extra_user_test_func,
    )
    if func:
        return actual_decorator(func)
    return actual_decorator


def _user_passes_test(test_func, conf, login_func, extra_user_test_func=None):
    """
    实际的装饰器，判断是否已经登陆，如果未登陆则跳转到微信授权页面去登陆，需要用户手工授权
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            # 判断是否是微信请求, （小程序请求也需要排除因为认证方式不一样）
            is_from_wechat_pub = is_weixin_request(request, exclude_mini=True)

            # 非微信直接返回
            if not is_from_wechat_pub:
                return string_http_response(u'请在微信下打开')

            # 已经登陆了则执行view函数
            if test_func(request.user) and (
                    extra_user_test_func is None or
                    (callable(extra_user_test_func) and extra_user_test_func(request.user, conf))
            ):
                return view_func(request, *args, **kwargs)

            # 未登陆，则使用公众账号登录
            is_final_result, result = get_wechat_open_id_and_access_token_in_explicit_mode(request, conf)
            if not is_final_result:
                return result

            open_id, access_token = result[:2]
            # 执行登陆
            login_func(request, conf, open_id, access_token)
            # 执行view函数
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


class WechatMiniResultCodeToSession(object):
    """
    小程序登陆结果
    """

    def __init__(self, json_result):
        # -1 系统繁忙，此时请开发者稍候再试，0 请求成功，40029 code 无效，45011 频率限制，每个用户每分钟100次
        self.errcode = json_result.get('errcode')
        self.errormsg = json_result.get('errmsg')
        self.openid = json_result.get('openid', '')
        self.session_key = json_result.get('session_key', '')
        self.unionid = json_result.get('unionid', '')
        # 无效参数，请勿使用
        self.expires_in = json_result.get('expires_in', 0)


def get_wechat_mini_session_by_code(code, timeout=SYNC_REQUEST_TIME_OUT):
    """
    小程序专用，通过code置换session

    参考链接：
    * code2Session，https://developers.weixin.qq.com/miniprogram/dev/api/open-api/login/code2Session.html
    :param mini_conf:   @see WeChatMiniCommonConf
    :param code:
    :param timeout:
    :return:
    """
    # if is_for_testcase():
    #     return WechatMiniResultCodeToSession({
    #         "openid": 'oOKH50BZNJrNGTfiaEHVD66qY48s',
    #         'session_key': 'eLM0zHCm8L7QcbfreW7UmA==',
    #     })

    url = WEIXIN_MINI_CODE_TO_SESSION.format(**{
        "app_id": APP_ID,
        "secret": APP_SECRET,
        "code": code
    })
    content = requests.get(url, timeout=timeout).content
    json_result = json.loads(content)
    return WechatMiniResultCodeToSession(json_result)
