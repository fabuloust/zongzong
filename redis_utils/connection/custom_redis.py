# -*- encoding:utf-8 -*-
from __future__ import absolute_import

import os
import pickle
import threading
import time
import logging
import redis as pyredis
from redis.connection import Token
from redis.exceptions import RedisError, DataError

from redis_utils.container.consts import GeoUnitEnum, GeoSortEnum


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

    def zadd_pickle(self, key, *args):
        """
        增加新的成员
        其中args为：score, value, score, value的配对方式，调用者保证score在前面
        """
        # 因为index为偶数的值存储为score，为奇数的值存储value，需要对value进行序列化操作
        # 例如: args = [100, {1:2}, 200, "test"]，下标0开始，需要对{1:2}， "test"序列化
        serialized_args_list = [pickle.dumps(args[index], pickle.HIGHEST_PROTOCOL) if index % 2 else args[index]
                                for index in range(len(args))]
        self.zadd(key, *serialized_args_list)

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

    def zincrby_pickle(self, key, value, amount):
        """
        给指定的value增加score
        """
        self.zincrby(key, pickle.dumps(value), amount=amount)

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

    # GEO COMMANDS
    def geoadd(self, name, *values):
        """
        Add the specified geospatial items to the specified key identified
        by the ``name`` argument. The Geospatial items are given as ordered
        members of the ``values`` argument, each item or place is formed by
        the triad longitude, latitude and name.
        """
        if len(values) % 3 != 0:
            raise DataError("GEOADD requires places with lon, lat and name"
                            " values")
        return self.execute_command('GEOADD', name, *values)

    def geodist(self, name, place1, place2, unit=None):
        """
        Return the distance between ``place1`` and ``place2`` members of the
        ``name`` key.
        The units must be one of the following : m, km mi, ft. By default
        meters are used.
        """
        pieces = [name, place1, place2]
        if unit and unit not in GeoUnitEnum.values():
            raise DataError("GEODIST invalid unit")
        elif unit:
            pieces.append(unit)
        return self.execute_command('GEODIST', *pieces)

    def geohash(self, name, *values):
        """
        Return the geo hash string for each item of ``values`` members of
        the specified key identified by the ``name`` argument.
        """
        return self.execute_command('GEOHASH', name, *values)

    def geopos(self, name, *values):
        """
        Return the positions of each item of ``values`` as members of
        the specified key identified by the ``name`` argument. Each position
        is represented by the pairs lon and lat.
        """
        return self.execute_command('GEOPOS', name, *values)

    def georadius(self, name, longitude, latitude, radius, unit=None,
                  withdist=False, withcoord=False, withhash=False, count=None,
                  sort=None, store=None, store_dist=None):
        """
        Return the members of the specified key identified by the
        ``name`` argument which are within the borders of the area specified
        with the ``latitude`` and ``longitude`` location and the maximum
        distance from the center specified by the ``radius`` value.

        The units must be one of the following : m, km mi, ft. By default

        ``withdist`` indicates to return the distances of each place.

        ``withcoord`` indicates to return the latitude and longitude of
        each place.

        ``withhash`` indicates to return the geohash string of each place.

        ``count`` indicates to return the number of elements up to N.

        ``sort`` indicates to return the places in a sorted way, ASC for
        nearest to fairest and DESC for fairest to nearest.

        ``store`` indicates to save the places names in a sorted set named
        with a specific key, each element of the destination sorted set is
        populated with the score got from the original geo sorted set.

        ``store_dist`` indicates to save the places names in a sorted set
        named with a specific key, instead of ``store`` the sorted set
        destination score is set with the distance.
        :return 如果不传多余参数 返回 [place1_name, place2_name, ....]
        否则根据传的参数返回二维数组，子数组对应项分别为选择的项，例如with_dist=True
        则会返回[[place1_name, place1_dist], [place2_name, place2_dist], ....]
        """
        return self._georadiusgeneric('GEORADIUS',
                                      name, longitude, latitude, radius,
                                      unit=unit, withdist=withdist,
                                      withcoord=withcoord, withhash=withhash,
                                      count=count, sort=sort, store=store,
                                      store_dist=store_dist)

    def georadiusbymember(self, name, member, radius, unit=None,
                          withdist=False, withcoord=False, withhash=False,
                          count=None, sort=None, store=None, store_dist=None):
        """
        与上一个命令的却别在于，参数用位置名member代替了位置的经纬度
        """
        return self._georadiusgeneric('GEORADIUSBYMEMBER',
                                      name, member, radius, unit=unit,
                                      withdist=withdist, withcoord=withcoord,
                                      withhash=withhash, count=count,
                                      sort=sort, store=store,
                                      store_dist=store_dist)

    def _georadiusgeneric(self, command, *args, **kwargs):
        pieces = list(args)
        if kwargs['unit'] and kwargs['unit'] not in GeoUnitEnum.values():
            raise DataError("GEORADIUS invalid unit")
        elif kwargs['unit']:
            pieces.append(kwargs['unit'])
        else:
            pieces.append(GeoUnitEnum.M, )

        for token in ('withdist', 'withcoord', 'withhash'):
            if kwargs[token]:
                pieces.append(Token(token.upper()))

        if kwargs['count']:
            pieces.extend([Token('COUNT'), kwargs['count']])

        if kwargs['sort'] and kwargs['sort'] not in GeoSortEnum.values():
            raise DataError("GEORADIUS invalid sort")
        elif kwargs['sort']:
            pieces.append(Token(kwargs['sort']))

        if kwargs['store'] and kwargs['store_dist']:
            raise DataError("GEORADIUS store and store_dist cant be set"
                            " together")

        if kwargs['store']:
            pieces.extend([Token('STORE'), kwargs['store']])

        if kwargs['store_dist']:
            pieces.extend([Token('STOREDIST'), kwargs['store_dist']])

        return self.execute_command(command, *pieces, **kwargs)


class EmptyCustomRedis(CustomRedis):
    pass
