# -*- coding:utf-8 -*-

"""
加载配置文件信息
"""
from __future__ import absolute_import

try:
    from cy_settings.api import settings as _settings
except ImportError:
    try:
        from django.conf import settings
        getattr(settings, 'LOGIN_URL', None)  # 可能会报 ImproperlyConfigured 错误
    except BaseException:
        import settings as _settings


class SettingsProxy(object):
    """
    读取配置文件内容
    """
    def __init__(self, real_settings=_settings):
        self.settings = real_settings

    def __getattr__(self, item):
        return getattr(self.settings, item)


settings = SettingsProxy()
