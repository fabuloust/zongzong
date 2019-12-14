# -*- coding:utf-8 -*-

"""
微信解密用户信息，参考了官方示例


接口变动：

* 0.1.4, fantianyu，增加了解密方法V2，允许非用户信息解密，增加错误码返回


参考链接：

* 小程序登录，https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/login.html
* 开放数据校验与解密，https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/signature.html
* 微信官方代码实例，https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/demo/aes-sample.zip
* 加解密代码示例，https://stackoverflow.com/questions/39690400/php-openssl-aes-in-python
* UnionID 机制说明，https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/union-id.html
* 获取转发详细信息，https://developers.weixin.qq.com/miniprogram/dev/api/share/wx.getShareInfo.html
"""

from __future__ import absolute_import

import base64

import simplejson as json
from Crypto.Cipher import AES

from utilities.enum import EnumBase, EnumItem

LENGTH_SESSION_KEY = 24
LENGTH_IV = 24


class WXDataCryptErrorChoices(EnumBase):
    OK = EnumItem(0, u"正确解析")
    ILLEGAL_AES_KEY = EnumItem(-41001, u"encodingAesKey 非法")
    ILLEGAL_IV = EnumItem(-41002, u"encodingIV 非法")
    ILLEGAL_BUFFER = EnumItem(-41003, u"aes 解密失败，得到的buffer非法")


def verify_user_info(user_info, expect_value):
    """
    校验用户数据是否满足要求
    :param user_info:
    :param expect_value:
    :return: 满足，True; 不满足，False
    """
    return user_info['watermark']['appid'] == expect_value


class WechatMiniDataCryptV2(object):
    """
    微信解密用户信息，参考了官方示例
    """

    def __init__(self, encoded_session_key, encoded_iv):
        """
        :param encoded_session_key: 用户 session_key，需要 base64 解密
        :param encoded_iv: 解密算法使用的向量，需要 base64 解密
        """
        self.encoded_session_key = encoded_session_key
        self.encoded_iv = encoded_iv

    @staticmethod
    def __pad(s):
        return s + (AES.block_size - len(s) % AES.block_size) * chr(
            AES.block_size - len(s) % AES.block_size)

    @staticmethod
    def __unpad(s):
        # 末尾诸如：\x03\x03\x03，将字符串末尾的多余字符去掉
        return s[0:-ord(s[-1])]

    def encrypt(self, raw):
        """
        用于数据验证
        """
        key = base64.b64decode(self.encoded_session_key)
        iv = base64.b64decode(self.encoded_iv)

        cipher = AES.new(key, AES.MODE_CBC, iv)
        raw = self.__pad(raw)
        return base64.b64encode(cipher.encrypt(raw))

    def decrypt(self, encoded_data):
        """
        使用 AES-128-CBC 算法解密
        :param encoded_data: 待解密用户数据
        :return: error_code, info_str
        """
        if len(self.encoded_session_key) != LENGTH_SESSION_KEY:
            return WXDataCryptErrorChoices.ILLEGAL_AES_KEY, ""
        key = base64.b64decode(self.encoded_session_key)

        if len(self.encoded_iv) != LENGTH_IV:
            return WXDataCryptErrorChoices.ILLEGAL_IV, ""
        iv = base64.b64decode(self.encoded_iv)

        data = base64.b64decode(encoded_data)

        cipher = AES.new(key, AES.MODE_CBC, iv)
        return WXDataCryptErrorChoices.OK, self.__unpad(cipher.decrypt(data))

    def decrypt_info(self, encoded_data, verify_func=verify_user_info, **kwargs):
        """
        生成用户信息解密字典

        ILLEGAL_BUFFER，一般是因为 session_key 过期了

        不需要校验返回值，需设置 verify_func=None
        :param encoded_data:
        :param verify_func: 默认校验用户数据
        :param kwargs: 需校验返回值时，传 expect_value
        :return: error_code, info_dict
        情景一，用户信息
        {
            openID, string, open_id
            nickName, string, 用户昵称
            gender，int，0 未知，1 男性，2 女性
            city，string，用户所在城市
            province，string，用户所在省份
            country，string，用户所在国家
            avatarUrl，string，用户头像图片的 URL。URL 最后一个数值代表正方形头像大小（有 0、46、64、96、132 数值可选，
                                0 代表 640x640 的正方形头像，46 表示 46x46 的正方形头像，剩余数值以此类推。默认132），
                                用户没有头像时该项为空。若用户更换头像，原有头像 URL 将失效。
            unionId，string，绑定公众帐号后，微信用来唯一标识用户的 ID
            watermark，dict
            {
                appid，string，小程序 APPID
                timestamp，int, 时间戳
            }
        }

        情景二，群信息
        {
            openGId，string, 群 ID
        }
        """
        error_code, info_str = self.decrypt(encoded_data)
        if error_code == WXDataCryptErrorChoices.OK:
            if info_str.startswith("{") and info_str.endswith("}"):
                info_dict = json.loads(info_str)
                if not callable(verify_func) or \
                        verify_func(info_dict, kwargs.get("expect_value")):
                    return WXDataCryptErrorChoices.OK, info_dict

            error_code = WXDataCryptErrorChoices.ILLEGAL_BUFFER
        return error_code, None
