"""
内容检测相关
"""
import json

import requests

from log_utils.loggers import info_logger
from weixin.manager.token import get_access_token

MSG_URL = 'https://api.weixin.qq.com/wxa/msg_sec_check?access_token={}'


def is_content_valid(content):
    """
    检查内容是否合规
    :param content:
    :return:
    """

    access_token = get_access_token()
    try:
        data = {'content': content.encode('utf-8').decode('latin1')}
        result = requests.post(MSG_URL.format(access_token), json.dumps(data, ensure_ascii=False)).json()
        if result['errcode'] != 0:
            info_logger.info('content:{}, check result: {}'.format(content, result['error_msg']))
            return False
        return True
    except:
        return True


