# -*- encoding:utf-8 -*-
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from utilities.request_utils import get_data_from_request
from utilities.response import json_http_error, json_http_success
from weixin.manager.weixin_mini_manager import wx_mini_request_login, WxminiAuthManager


@csrf_exempt
@require_POST
def login_and_get_session_id_view(request):
    """
    使用小程序的登录然后返回session_id，目前支持两种登录方式：
    1、使用微信的code后台服务器验证方式
    2、使用春雨的用户名和账户验证
    URL[POST]: /weixin/get_session_id/
    :param request: {code, encryptedData, iv}
    """
    # 使用code方式进行登录
    post_data = get_data_from_request(request)
    code = post_data.get('code')
    encrypted_data = post_data.get('encryptedData')
    iv = post_data.get('iv')
    if code:
        user, session_key = WxminiAuthManager.sync_wx_mini_user_info(code, encrypted_data, iv)

    # 使用form表单携带账户和密码进行登录
    else:
        return json_http_error('缺少参数')

    # 用户登录返回session信息
    if not user:
        return json_http_error('invalid user')
    wx_mini_request_login(request, user, session_key)
    return json_http_success({"sessionid": request.session.session_key})
