# -*- encoding:utf-8 -*-

APP_ID = 'wx543aba2d0ec781c9'
APP_SECRET = 'c5414cf13f142c86ee1860bc421d51c1'

SIGNATURE_KEY = u"signature"
SYNC_REQUEST_TIME_OUT = 2  # 同步请求超时时间, 超过3s, uwsgi worker会harakiri
ASYNC_REQUEST_TIME_OUT = 5  # 异步请求超时时间, 可以设置得稍微长一点


WECHAT_OAUTH2_AUTH_URL = "https://open.weixin.qq.com/connect/oauth2/authorize?" \
                     "appid={app_id}&" \
                     "redirect_uri={redirect_uri}&" \
                     "response_type=code&" \
                     "scope={scope}&" \
                     "state={state}&" \
                     "connect_redirect=1#wechat_redirect"  # connect_redirect 这个在文档里没有记录，但是需要传


WECHAT_OAUTH2_ACCESS_TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token?" \
                      "appid={app_id}&" \
                      "secret={secret}&" \
                      "code={code}&" \
                      "grant_type=authorization_code"


WECHAT_USER_INFO_BY_OPEN_ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/user/info?" \
                                            "access_token={access_token}&" \
                                            "openid={open_id}&lang=zh_CN"


WECHAT_USER_INFO_BY_USER_ACCESS_TOKEN_URL = "https://api.weixin.qq.com/sns/userinfo?" \
                                     "access_token={access_token}&" \
                                     "openid={open_id}"


# 小程序通过 code 置换 session
WEIXIN_MINI_CODE_TO_SESSION = "https://api.weixin.qq.com/sns/jscode2session?" \
                        "appid={app_id}&" \
                        "secret={secret}&" \
                        "js_code={code}&grant_type=authorization_code"


# 微信授权时会传给微信一个以 `WEIXIN_AUTH_STATE_FLAG` 开头的state
WECHAT_AUTH_STATE_FLAG = 'WEIXIN_AUTH'

# 微信授权state保存在 fk_session的key
WECHAT_AUTH_STATE_KEY = "wechat_auth_state_key"


class WeChatOAuth2Scope(object):
    SNS_API_USER_INFO = "snsapi_userinfo"
    SNS_API_BASE = "snsapi_base"
