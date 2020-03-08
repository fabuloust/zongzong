import requests

from redis_utils.container.api_redis_client import redis
from weixin.consts import APP_ID, APP_SECRET


URL = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
ACCESS_TOKEN_KEY = 'wx_access_token'


def get_access_token():
    """
    获取access_token
    """
    access_token = redis.get('access_token')
    if access_token:
        return access_token
    try:
        result = requests.get(URL.format(APP_ID, APP_SECRET)).json()
        access_token, expires_in = result['access_token'], result['expires_in']
        redis.setex('access_token', expires_in, access_token)
        return access_token
    except:
        return None
