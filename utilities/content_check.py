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
    data = {"content": content}
    data = json.dumps(data, ensure_ascii=False)
    headers = {'Content-Type': 'application/json'}
    result = requests.post(MSG_URL.format(access_token), data.encode('utf-8'), headers=headers).json()
    if result['errcode'] != 0:
        print(result)
        info_logger.info('content:{}, check result: {}'.format(content, result['error_msg']))
        return False
    return True


