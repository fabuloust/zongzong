# -*- coding:utf-8 -*-
import json

from django.test.client import MULTIPART_CONTENT, Client


from utilities.mock_utility import mock


DEFAULT_DEVICE_ID = 'b9267a2bd8241863fcc62d22c4b3f3d1dd73d8c19ecfdddad08967ecf02b7186'


class CustomClient(Client):
    def __init__(self):
        super(CustomClient, self).__init__()

    def json_post(self, path, data={}, content_type=MULTIPART_CONTENT, **extra):
        path = self.handle_http_path(path)
        response = self.post(path, data, content_type, **extra)
        return json.loads(response.content)

    def json_raw_post(self, path, data={}):
        """
        以raw_post_data的方式发送json_post请求
        """
        json_str = json.dumps(data)
        path = self.handle_http_path(path)
        response = self.post(path, json_str, 'application/json', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        return json.loads(response.content)

    def json_get(self, path, data={}, follow=False, **extra):
        path, data = self.handle_http_get_path(path, data)
        response = self.get(path, data, follow, **extra)
        return json.loads(response.content)
    
    def handle_http_path(self, path):
        if '?' not in path:
            path += '?'
        return path
    
    def handle_http_get_path(self, path, data):
        path = self.handle_http_path(path)
        if not data:
            return path, data
        return path, data


def create_user_login_client(user=None):
    login_user = user if user else mock.create_user()
    client = CustomClient()
    client.login(username=login_user.username, password='1qaz2wsx')
    return client, login_user
