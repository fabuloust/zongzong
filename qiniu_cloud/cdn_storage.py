# -*- coding: utf-8 -*-
try:
    from django.contrib.staticfiles.storage import StaticFilesStorage
    BaseClass = StaticFilesStorage
except ImportError:
    BaseClass = object

from cy_cloud_storage import upload_file_to_static
from cy_settings.api import settings

"""
static存储到又拍云上
目前策略是本地存一份，又拍云存一份

配置项，CDN_STATIC_URL_PREFIX_KEY，为url前缀字符串，可用于不同项目的相同文件名cdn文件隔离，例如django不同版本的后台static文件
例如CDN_STATIC_URL_PREFIX_KEY="medweb/"
文件static/admin/django.css上传后为，{七牛url前缀}/static/medweb/admin/django.css
"""


def ensure_utf8(str1):
    if not str1:
        return ''
    if isinstance(str1, unicode):
        return str1.encode('utf-8')
    return str1


class CDNStorage(BaseClass):

    def __init__(self):
        super(CDNStorage, self).__init__()

    def _save(self, name, content):
        super(CDNStorage, self)._save(name, content)
        relative_name = ensure_utf8(name)
        prefix_key = getattr(settings, "CDN_STATIC_URL_PREFIX_KEY", None)
        if prefix_key:
            relative_name = prefix_key + relative_name
        absolute_name = ensure_utf8(content.name)
        _flag, path = upload_file_to_static(relative_name, absolute_name)
        print 'upload to cdn %s' % path
