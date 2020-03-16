"""
内容检测相关
"""
import json

import qiniu
import requests

from log_utils.loggers import info_logger
from utilities.upload_utils import QINIU_ACCESS_KEY, QINIU_SECRET_KEY
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
        info_logger.info('content:{}, check result: {}'.format(content, result['errorMsg']))
        return False
    return True


def is_image_valid(image_url):
    url = "http://ai.qiniuapi.com/v3/image/censor"
    body = {'data': {'uri': image_url}, "params": {"scene": ['pulp', 'terror', 'politician']}}
    q = qiniu.Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
    header = {'Content-Type': 'application/json',
              'Authorization': 'Qiniu {}'.format(q.token_of_request(url, body, 'application/json'))}
    result = requests.post(url, {'data': {'uri': image_url},
                                 "params": {"scene": ['pulp', 'terror', 'politician']}}, headers=header).json()
    print(result)

