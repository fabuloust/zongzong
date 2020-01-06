# -*- encoding:utf-8 -*-
from __future__ import absolute_import

import _pickle as pickle
import os
import threading
import time
import logging

import redis as pyredis
from redis.exceptions import RedisError


class ConnectionProxy(object):
    """
    对象删除时，自动释放回连接池
    现在主要是给thrift rpc server，需要协程退出后，释放连接用。
    """
    MAX_IDLE_SECONDS = 3500

    def __init__(self, connection, pool=None):
        self._proxy_connection = connection
        self._proxy_pool = pool
        self._last_execute_timestamp = int(time.time())

    def __getattr__(self, item):
        return getattr(self._proxy_connection, item)

    def __del__(self):
        if self._proxy_pool:
            self._proxy_pool.release(self._proxy_connection)

    def send_command(self, *args):
        now_timestamp = int(time.time())
        # 春雨redis server连接最大空闲时间为1小时，此处如果接近1小时未用，则重连
        if (now_timestamp - self._last_execute_timestamp) > self.MAX_IDLE_SECONDS:
            self._proxy_connection.disconnect()
            logging.warn("disconenct redis connection %s when idle too long %s => %s" %
                         (repr(self._proxy_connection), self._last_execute_timestamp, now_timestamp))
        self._last_execute_timestamp = now_timestamp
        return self._proxy_connection.send_command(*args)


class ConnectionPoolProxy(object):
    """
    Redis执行command时候，默认每次获取一个连接，执行完释放回连接池
    修改为：
      每个线程/协程获取完连接后，在线程/协程结束前不释放连接
      线程/协程结束后，自动释放连接

    注：属性，方法，都加上了个"proxy"前缀，避免和被代理对象属性冲突。
    """
    CONNECTION_KEY = "connection"

    def __init__(self, pool):
        self._proxy_pool = pool
        self.proxy_reset()

    def proxy_reset(self):
        self._local_connection = threading.local()
        self._proxy_id = os.getpid()
        self._proxy_lock = threading.Lock()

    def proxy_check_pid(self):
        if self._proxy_id != os.getpid():
            with self._proxy_lock:
                if self._proxy_id == os.getpid():
                    return
                self.proxy_reset()

    def __getattr__(self, item):
        return getattr(self._proxy_pool, item)

    def get_connection(self, command_name, *keys, **options):
        self.proxy_check_pid()
        connection_proxy = getattr(self._local_connection, self.CONNECTION_KEY, None)
        if not connection_proxy:
            connection = self._proxy_pool.get_connection(command_name, *keys, **options)
            connection_proxy = ConnectionProxy(connection, self._proxy_pool)
            setattr(self._local_connection, self.CONNECTION_KEY, connection_proxy)
        return connection_proxy

    def release(self, connection):
        pass

    def __repr__(self):
        return repr(self._proxy_pool)


class CustomRedis(pyredis.StrictRedis):
    def __init__(self, *args, **kwargs):
        super(CustomRedis, self).__init__(*args, **kwargs)
        self.connection_pool = ConnectionPoolProxy(self.connection_pool)

    def execute_command(self, *args, **options):
        """
        重写该命令，主要是为了检测Redis命令的长度
        最长不能超过128字节，防止代码Bug导致Key特别长
        """
        # 有些key直接传递的整形等，可以直接忽略
        if len(args) > 2 and isinstance(args[1], str):
            # 第一个参数为Redis的命令，第二个参数为key名字
            redis_command_key = args[1]
            try:
                command_key_length = len(redis_command_key)
                if command_key_length > 128:
                    raise RedisError("redis key is too long, please fix: %s-%s" % (redis_command_key, command_key_length))
            except RedisError:
                pass
        return super(CustomRedis, self).execute_command(*args, **options)

    def delete(self, *names):
        """
        默认删除为异步删除，提高性能
        https://stackoverflow.com/questions/45818371/is-the-unlink-command-always-better-than-del-command
        如果线程切换的开销过于影响，再改回来，大key再使用unlink处理
        """
        return self.execute_command('UNLINK', *names)

    def sync_delete(self, *names):
        """
        同步删除 
        """
        return self.execute_command('DEL', *names)

    def get_pickle(self, key):
        val = self.get(key)
        if val is None:
            return val
        return pickle.loads(val)

    def set_pickle(self, key, val):
        val = pickle.dumps(val, pickle.HIGHEST_PROTOCOL)
        self.set(key, val)

    def setex_pickle(self, name, time, value):
        value = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        return self.setex(name, time, value)

    def hget_pickle(self, name, key):
        val = self.hget(name, key)
        if val is None:
            return val
        return pickle.loads(val)

    def hset_pickle(self, name, key, val):
        val = pickle.dumps(val, pickle.HIGHEST_PROTOCOL)
        self.hset(name, key, val)

    def hvals_pickle(self, name):
        result = self.hvals(name)
        return [pickle.loads(val) for val in result]

    def hmset_pickle(self, name, item_dict):
        result = {key: pickle.dumps(value, pickle.HIGHEST_PROTOCOL) for key, value in item_dict.items()}
        self.hmset(name, result)

    def hmget_pickle(self, name, keys, *args):
        values = self.hmget(name, keys, *args)
        # key不存在时返回None，不需要pickle.loads
        return [value if value is None else pickle.loads(value) for value in values]

    def hgetall_pickle(self, name):
        result = self.hgetall(name)
        return {key: pickle.loads(value) for key, value in result.items()}

    def rpush_pickle(self, name, *values):
        values = [pickle.dumps(value, pickle.HIGHEST_PROTOCOL) for value in values]
        self.rpush(name, *values)

    def lpop_pickle(self, name):
        val = self.lpop(name)
        if val is None:
            return val
        return pickle.loads(val)

    def lpush_pickle(self, name, *values):
        values = [pickle.dumps(value, pickle.HIGHEST_PROTOCOL) for value in values]
        self.lpush(name, *values)

    def lrange_pickle(self, key, start, stop):
        values = self.lrange(key, start, stop)
        return [pickle.loads(value) for value in values]

    def lrem_pickle(self, key, value, count=1):
        value = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        self.lrem(key, 0, value)

    def lindex_pickle(self, name, index):
        value = self.lindex(name, index)
        return pickle.loads(value)

    def lset_pickle(self, name, index, value):
        value = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        self.lset(name, index, value)

    # 下面这两个地方，由于咱们目前有对value进行pickle的需求，与原生无法保持一致。因此做下兼容
    def zadd(self, name, *args):
        score_map = {args[index]: args[index - 1] for index in range(len(args)) if index % 2}
        return super(CustomRedis, self).zadd(name, score_map)

    # Zset相关封装
    def zadd_pickle(self, key, *args):
        """
        增加新的成员
        其中args为：score, value, score, value的配对方式，调用者保证score在前面
        """
        # 因为index为偶数的值存储为score，为奇数的值存储value，需要对value进行序列化操作
        # 例如: args = [100, {1:2}, 200, "test"]
        score_map = {pickle.dumps(args[index]): args[index - 1] for index in range(len(args)) if index % 2}
        return super(CustomRedis, self).zadd(key, score_map)

    def zrem_pickle(self, key, *values):
        """
        根据value值删除set中指定元素
        """
        values = [pickle.dumps(value, pickle.HIGHEST_PROTOCOL) for value in values]
        self.zrem(key, *values)

    def zscore_pickle(self, key, value):
        """
        获取value值对应的score
        """
        return self.zscore(key, pickle.dumps(value, pickle.HIGHEST_PROTOCOL))

    def zincrby_pickle(self, key, amount, value):
        """
        给指定的value增加score
        """
        self.zincrby(key, amount, pickle.dumps(value))

    def zrange_pickle(self, key, start, end):
        """
        获取特定排名内的成员，左右边界都取出来，暂时不返回相应的score值
        """
        result = self.zrange(key, start, end)
        result = [pickle.loads(item) for item in result]
        return result

    def zrevrange_pickle(self, key, start, end):
        """
        逆序获取特定排名内的成员，左右边界都取出来
        """
        result = self.zrevrange(key, start, end)
        result = [pickle.loads(item) for item in result]
        return result

    def zrangebyscore_pickle(self, key, min_score, max_score, start=None, num=None):
        """
        获取特定分值范围内的成员
        """
        result = self.zrangebyscore(key, min_score, max_score, start, num)
        result = [pickle.loads(item) for item in result]
        return result

    def bf_reserve(self, key, error_rate, size):
        """
        创建布隆过滤器
        """
        return self.execute_command('BF.RESERVE', key, error_rate, size)

    def bf_add(self, key, item):
        """
        往布隆过滤器里添加元素
        :return 1 if newly add else 0
        """
        return self.execute_command('BF.ADD', key, item)

    def bf_madd(self, key, *items):
        """
        添加多个元素
        :return: [0, 1, 0, ....]
        """
        return self.execute_command('BF.MADD', key, *items)

    def bf_exists(self, key, item):
        """
        key中是否存在item
        """
        return self.execute_command('BF.EXISTS', key, item)

    def bf_mexists(self, key, *items):
        """
        key的容器中是否存在item对应的序列
        """
        return self.execute_command('BF.EXISTS', key, *items)

    def cl_throttle(self, key, max_burst, token_number, period, quantity=1):
        """
        创建令牌桶
        :param key:
        :param max_burst: 桶的最大容量
        :param token_number: period时间内可产生的token数
        :param period: 如上所示，单位为秒
        :param quantity: 取令牌的数量
        :return: success, max_burst + 1， token_num_left, seconds_when_available, sencods_when_full
        """
        return self.execute_command('CL.THROTTLE', key, max_burst, token_number, period, quantity)
