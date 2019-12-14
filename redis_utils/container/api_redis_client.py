# -*- encoding:utf-8 -*-
"""
redis client获取
根据配置文件中`REDIS`和 SENTINEL_REDIS`属性获取redis client
`SENTINEL_REDIS`中的定义优先级更高
这两个字典中如果有key为{name}，则可以`from cy_cache.api_redis_client import {name}_redis`
"""
from __future__ import absolute_import

import sys


# 保留之前定义的 redis, model_redis等，防止有地方可能你有直接 `from cy_cache.api_redis_client import *`不能正常工作
from redis_utils.connection.redis_client import get_redis_client_from_conf, DEFAULT_REDIS

redis = get_redis_client_from_conf(DEFAULT_REDIS)


class _Module(object):
    """
    如果配置文件里面有定义
      REDIS = {"custom": INFO}
    或者
      SENTINEL_REDIS = {"custom": INFO}
    则可以直接 `from cy_cache.api_redis_client import custom_redis`
    """
    def __init__(self, real_module):
        self._real_module = real_module

        for k, v in real_module.__dict__.items():  # 使得`from real_module import *`能正常工作
            setattr(self, k, v)

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]

        def _get():
            try:
                return getattr(self._real_module, item)
            except AttributeError:
                return self.__get_redis_instant(item)

        result = _get()
        self.__dict__[item] = result
        return result

    def __get_redis_instant(self, name):
        suffix = "redis"
        suffix_len = len(suffix) + 1  # _redis
        if not name.endswith(suffix):
            raise AttributeError
        conf_name = name[:-suffix_len] or "default"  # name == "redis"
        return get_redis_client_from_conf(conf_name)


sys.modules[__name__] = _Module(sys.modules[__name__])
