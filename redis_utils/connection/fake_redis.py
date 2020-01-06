# -*- coding: utf-8 -*-

"""
春雨对 fake redis 的定制
"""
from __future__ import absolute_import

import pickle
import time
import six

import fakeredis
import simplejson as json
from fakeredis import FakeStrictRedis
from geopy.distance import geodesic
from redis import DataError

from redis_utils.container.consts import GeoUnitEnum, GeoSortEnum


def iteritems(d):
    return iter(d.items())


# 原来expire不支持小数，fake下int_types
fakeredis.int_types = (float, ) + six.integer_types

port_2_fake_server = {}


class CYFakerRedis(FakeStrictRedis):
    """
    春雨对 FakeRedis 做定制

    singleton=False，不与其他 db_client 共享 _db，防止 flush 时被清掉

    """
    def __init__(self, db=0, charset='utf-8', errors='strict',
                 decode_responses=False, connected=True, **kwargs):

        db = int(kwargs.get("port", 0))
        if db not in port_2_fake_server:
            port_2_fake_server[db] = server = fakeredis.FakeServer()
        else:
            server = port_2_fake_server[db]

        if 'connection_pool' in kwargs:
            kwargs.pop('connection_pool')
        # 新版的fakeredis的不同的存储是通过server来控制的，server相同则存储相同
        FakeStrictRedis.__init__(self, db=0, charset=charset, errors=errors,
                                 decode_responses=decode_responses,
                                 connected=connected, server=server, **kwargs)

    def sync_delete(self, *names):
        """
        同步删除 
        """
        return self.delete(*names)

    def get_pickle(self, key):
        val = self.get(key)
        if val is None:
            return val
        return pickle.loads(val)

    def set_pickle(self, key, val):
        val = pickle.dumps(val)
        self.set(key, val)

    def setex_pickle(self, name, time, value):
        value = pickle.dumps(value)
        return self.setex(name, time, value)

    def hget_pickle(self, name, key):
        val = self.hget(name, key)
        if val is None:
            return val
        return pickle.loads(val)

    def hset_pickle(self, name, key, val):
        val = pickle.dumps(val)
        self.hset(name, key, val)

    def hvals_pickle(self, name):
        result = self.hvals(name)
        return [pickle.loads(val) for val in result]

    def hmset_pickle(self, name, item_dict):
        result = {key: pickle.dumps(value) for key, value in item_dict.items()}
        self.hmset(name, result)

    def hmget_pickle(self, name, keys, *args):
        values = self.hmget(name, keys, *args)
        # # key不存在时返回None，不需要pickle.loads
        return [value if value is None else pickle.loads(value) for value in values]

    def hgetall_pickle(self, name):
        result = self.hgetall(name)
        return {key: pickle.loads(value) for key, value in result.items()}

    def rpush_pickle(self, name, *values):
        values = [pickle.dumps(value) for value in values]
        self.rpush(name, *values)

    def lpop_pickle(self, name):
        val = self.lpop(name)
        if val is None:
            return val
        return pickle.loads(val)

    def lpush_pickle(self, name, *values):
        values = [pickle.dumps(value) for value in values]
        self.lpush(name, *values)

    def lrange_pickle(self, key, start, stop):
        values = self.lrange(key, start, stop)
        return [pickle.loads(value) for value in values]

    def lrem_pickle(self, key, value, count=1):
        value = pickle.dumps(value)
        self.lrem(key, 0, value)

    def lindex_pickle(self, name, index):
        value = self.lindex(name, index)
        return pickle.loads(value)

    def lset_pickle(self, name, index, value):
        value = pickle.dumps(value)
        self.lset(name, index, value)

    # 下面这两个地方，由于咱们目前有对value进行pickle的需求，与原生无法保持一致。因此做下兼容
    def zadd(self, name, *args):
        score_map = {args[index]: args[index - 1] for index in range(len(args)) if index % 2}
        return super(CYFakerRedis, self).zadd(name, score_map)

    # Zset相关封装
    def zadd_pickle(self, key, *args):
        """
        增加新的成员
        其中args为：score, value, score, value的配对方式，调用者保证score在前面
        """
        # 因为index为偶数的值存储为score，为奇数的值存储value，需要对value进行序列化操作
        # 例如: args = [100, {1:2}, 200, "test"]
        score_map = {pickle.dumps(args[index]): args[index - 1] for index in range(len(args)) if index % 2}
        return super(CYFakerRedis, self).zadd(key, score_map)

    def zrem_pickle(self, key, *values):
        """
        根据value值删除set中指定元素
        """
        values = [pickle.dumps(value) for value in values]
        self.zrem(key, *values)

    def zscore_pickle(self, key, value):
        """
        获取value值对应的score
        """
        return self.zscore(key, pickle.dumps(value))

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

    def zrangebyscore_pickle(self, key, min_score=None, max_score=None, start=None, num=None):
        """
        获取特定分值范围内的成员
        """
        result = self.zrangebyscore(key, min_score, max_score, start, num)
        result = [pickle.loads(item) for item in result]
        return result

    def bf_reserve(self, key, error_rate, size):
        """
        创建布隆过滤器, 默认成功
        """
        return True

    def bf_add(self, key, item):
        """
        往布隆过滤器里添加元素
        :return 1 if newly add else 0
        """
        return self.sadd(key, item)

    def bf_madd(self, key, *items):
        """
        添加多个元素
        :return: [0, 1, 0, ....]
        """
        return self.sadd(key, *items)

    def bf_insert(self):
        pass

    def bf_exists(self, key, item):
        """
        key中是否存在item
        """
        return self.sismember(key, item)

    def bf_mexists(self, key, *item):
        """
        key的容器中是否存在item对应的序列
        """
        return [self.sismember(key, value) for value in item]

    def cl_throttle(self, key, capacity, count_per_period, period, get_num=1):
        """
        创建限流器, 通过时间来模拟，仿照RateLimiter的实现
        """
        capacity_key = key + 'capacity'
        if self.exists(capacity_key):
            left_num = int(self.get(capacity_key))
        else:
            left_num = capacity
            self.set(capacity_key, left_num)

        micro_second_per_second = 1000000
        microseconds = int(period * micro_second_per_second)
        # 每个令牌的发放时间间隔,单位微秒
        micro_second_per_permit = int(microseconds / count_per_period)
        last_permit_time = int(self.get(key) or 0)
        now_time = int(time.time() * micro_second_per_second)
        # 时间窗口内，没有使用过令牌，重置时间
        delta_time = now_time - last_permit_time
        if delta_time > microseconds:
            self.set(key, now_time)
            self.set(capacity_key, capacity)
            return True, capacity + 1, capacity, -1, -1
        # 令牌耗尽
        elif delta_time < micro_second_per_permit and left_num == 0:
            return False, capacity + 1, 0, \
                (last_permit_time + micro_second_per_permit - now_time) / micro_second_per_second, \
                capacity * period / count_per_period
        # 刷新一下过期时间
        self.expire(key, period)

        # 期间生成的token数
        generated_token_num = delta_time / micro_second_per_permit
        left_num = min(capacity, left_num + generated_token_num)
        self.set(capacity_key, max(0, left_num - get_num))
        self.set(key, now_time)
        return True, capacity + 1, left_num, -1, period * (capacity - left_num) / count_per_period

    # GEO COMMANDS
    def geoadd(self, key, *values):
        """
        Add the specified geospatial items to the specified key identified
        by the ``name`` argument. The Geospatial items are given as ordered
        members of the ``values`` argument, each item or place is formed by
        the triad longitude, latitude and name.
        """
        if len(values) % 3 != 0:
            raise DataError("GEOADD requires places with lon, lat and name"
                            " values")
        for i in range(0, len(values), 3):
            self.hset(key, values[i + 2], json.dumps(values[i:i + 2]))
        return True

    def geodist(self, name, place1, place2, unit=None):
        """
        Return the distance between ``place1`` and ``place2`` members of the
        ``name`` key.
        The units must be one of the following : m, km mi, ft. By default
        meters are used.
        """
        if unit and unit not in GeoUnitEnum.values():
            raise DataError("GEODIST invalid unit")
        if not self.hget(name, place1) or not self.hget(name, place2):
            raise DataError("place does not exists")
        place1_data = json.loads(self.hget(name, place1))
        place2_data = json.loads(self.hget(name, place2))
        distance = geodesic((place1_data[1], place1_data[0]), (place2_data[1], place2_data[0]))
        if unit == GeoUnitEnum.M or not unit:
            return distance.meters
        elif unit == GeoUnitEnum.MI:
            return distance.miles
        elif unit == GeoUnitEnum.KM:
            return distance.kilometers
        else:
            return distance.feet

    def geohash(self, name, *values):
        """
        测试用例里用不到这玩意儿
        """
        return ''

    def geopos(self, name, *values):
        """
        Return the positions of each item of ``values`` as members of
        the specified key identified by the ``name`` argument. Each position
        is represented by the pairs lon and lat.
        """
        result = []
        for place in values:
            position = self.hget(name, place)
            position = json.loads(position) if position else None
            result.append(position)
        return result

    def georadius(self, name, longitude, latitude, radius, unit=None,
                  withdist=False, withcoord=False, withhash=False, count=None,
                  sort=None, store=None, store_dist=None):
        """
        测试用例只支持with_dist和count，别的就不支持了，太麻烦且没用, 如果有需求自己去查文档吧。。
        获取单位unit的半径radius内的单位，根据配置项可以返回距离，坐标，hash三个信息，并可以选择数量和按距离排列的顺序
        """
        if unit and unit not in GeoUnitEnum.values() or (sort and sort not in GeoSortEnum.values()):
            raise DataError("GEODIST invalid unit")
        all_items = self.hgetall(name)
        all_items = {key: json.loads(value) for key, value in all_items.items()}
        result = []
        for place_name, item in all_items.items():
            lon, lat = item
            dist = geodesic((latitude, longitude), (lat, lon))
            distance = dist.m if unit == GeoUnitEnum.M else dist.km if unit == GeoUnitEnum.KM else dist.mi \
                if unit == GeoUnitEnum.MI else dist.ft
            if distance <= radius:
                result.append([place_name, distance])
        if sort:
            result.sort(key=lambda x: x[1], reverse=sort == GeoSortEnum.DESC)

        if not withdist:
            result = [item[0] for item in result]

        return result if not count else result[:count]

    def georadiusbymember(self, name, member, radius, unit=None,
                          withdist=False, withcoord=False, withhash=False,
                          count=None, sort=None, store=None, store_dist=None):
        """
        与上面一个的区别是用地点名member代替了地点的左边
        """
        if unit and unit not in GeoUnitEnum.values():
            raise DataError("GEODIST invalid unit")
        place_data = self.hget(name, member)
        if not place_data:
            raise DataError("member does not exist")
        place_data = json.loads(place_data)
        lon, lat = place_data
        return self.georadius(name, lon, lat, radius, unit, withdist, withcoord, withhash, count, sort, store,
                              store_dist)


class FakeSentinel(object):
    """
    @see redis.sentinel.Sentinel
    """

    def __init__(self, sentinels, min_other_sentinels=0, sentinel_kwargs=None,
                 **connection_kwargs):
        # if sentinel_kwargs isn't defined, use the socket_* options from
        # connection_kwargs
        if sentinel_kwargs is None:
            sentinel_kwargs = {k: v for k, v in iteritems(connection_kwargs)
                               if k.startswith('socket_')}
        self.sentinel_kwargs = sentinel_kwargs
        self.min_other_sentinels = min_other_sentinels
        self.connection_kwargs = connection_kwargs

    def discover_master(self, service_name):
        return "127.0.0.1", 6379

    def filter_slaves(self, slaves):
        return slaves

    def discover_slaves(self, service_name):
        return []

    def master_for(self, service_name, redis_class=CYFakerRedis, **kwargs):
        return redis_class()
