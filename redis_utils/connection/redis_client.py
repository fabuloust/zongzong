# -*- coding:utf-8 -*-
"""
这里只针对 Django Model进行了优化

为什么不使用 https://github.com/sebleier/django-redis-cache/ ?
它全局替换Django的Cache
"""
from __future__ import absolute_import

import socket
import threading

from django.conf import settings

from redis.sentinel import Sentinel

from redis_utils.connection.custom_pool import create_block_redis_connection_pool
from redis_utils.connection.custom_redis import CustomRedis
from redis_utils.connection.fake_redis import CYFakerRedis
from utilities.settings_utils import is_for_testcase

if is_for_testcase():
    BaseRedisClass = CYFakerRedis
else:
    BaseRedisClass = CustomRedis
# BaseSentinelClass = Sentinel

# 几个常用的redis client，暂时和medweb兼容
DEFAULT_REDIS = "default"  # 默认缓存，用于缓存数据，互斥锁等

# 默认redis超时秒数
DEFAULT_REDIS_TIMEOUT_SECONDS = 1
# 读取配置的redis超时秒数
# _socket.SocketType#settimeout
REDIS_TIMEOUT_SECONDS = getattr(settings, "REDIS_TIMEOUT_MILLISECONDS", 0) / 1000.
if REDIS_TIMEOUT_SECONDS <= 0:
    REDIS_TIMEOUT_SECONDS = DEFAULT_REDIS_TIMEOUT_SECONDS
# Redis长连接配置，默认关闭为短连接，Connection->_connect可知
# https://github.com/andymccurdy/redis-py/blob/master/CHANGES
REDIS_SOCKET_KEEPALIVE = getattr(settings, "REDIS_SOCKET_KEEPALIVE", True)
REDIS_SOCKET_KEEPALIVE_OPTIONS = {
    socket.TCP_KEEPINTVL: 20,  # 前后两次keepalive探测之间的时间间隔，单位是秒
    socket.TCP_KEEPCNT: 3,  # 关闭一个非活跃连接之前的最大探测次数，server连续没有回应的情况
}
# TCP连接如果处于空闲状态，多久后发送keepalive探测，单位为秒。Mac没有该选项
if hasattr(socket, "TCP_KEEPIDLE"):
    REDIS_SOCKET_KEEPALIVE_OPTIONS[socket.TCP_KEEPIDLE] = 300

_MODULE_NAME = __name__

_local_cache = threading.local()


def get_redis_client_from_hostport(host, port, password):
    """
    通过提供主机IP端口、密码形式获取客户端连接
    """
    try:
        connection_pool = create_block_redis_connection_pool(
            host=host, port=int(port), password=password,
            socket_timeout=REDIS_TIMEOUT_SECONDS,
            socket_connect_timeout=REDIS_TIMEOUT_SECONDS,
            socket_keepalive=REDIS_SOCKET_KEEPALIVE,
            socket_keepalive_options=REDIS_SOCKET_KEEPALIVE_OPTIONS
        )
        return BaseRedisClass(
            host=host, port=int(port), password=password,
            connection_pool=connection_pool,
            socket_timeout=REDIS_TIMEOUT_SECONDS,
            socket_connect_timeout=REDIS_TIMEOUT_SECONDS,
            socket_keepalive=REDIS_SOCKET_KEEPALIVE,
            socket_keepalive_options=REDIS_SOCKET_KEEPALIVE_OPTIONS)
    except BaseException:
        if not getattr(settings, "DEBUG", False):
            pass
        return None


def get_redis_client_from_conf_by_host_port(conf_name, settings_key="REDIS"):
    """
    读取settings配置文件创建Redis Client

    默认读取属性REDIS，其值格式为
      REDIS = {
        "default": {  # default --> conf_name
          "host": host,
          "port": port,
          "password": password,
        },
      }

    :param conf_name:
    :param settings_key:
    :return: redis client or None
    """
    redis_conf = getattr(settings, settings_key, None)
    if not redis_conf:
        return None

    if conf_name not in redis_conf:
        return None

    cli_info = redis_conf.get(conf_name)
    host = cli_info.get("host", "localhost")
    port = cli_info.get("port", 6379)
    password = cli_info.get("password")
    return get_redis_client_from_hostport(host, port, password)


def get_redis_client_from_conf(conf_name, settings_key="REDIS"):
    """
    利用： settings中的配置来创建Redis Client
    """
    redis_cli = get_redis_client_from_conf_by_host_port(conf_name, settings_key)
    return redis_cli
