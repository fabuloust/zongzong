# -*- coding:utf-8 -*-
"""
放在redis里面共享数据容器
由于hsetnx, sadd, pipeline等均没有pickle支持,
这个地方统一自己管理序列化/反序列化

RedisDict: HashMap实现
RedisSet: Set集合
RedisSortedSet: 有序集合
RedisList: 列表

GeneralListCacheByTime: 用来管理一组有序集合SortedSet
GeneralListCache: 用来管理一组list列表

RedisCounter: 基于Redis的计数器
DailyCounter: 每日计数器

BasicBadgeManager: Badge管理

InfoCacheManager: 特殊的HashMap封装，当Redis缺失某些值时可自动计算

RandModelCacheManager: 随机获取Mode Cache
"""
import datetime
import logging
import pickle
import time
import zlib
from random import randint

from redis_utils.container.api_redis_client import redis
from utilities.date_time import timestamp_to_datetime, convert_datime_to_timestamp

DAY_SECONDS = 60 * 60 * 24  # 一天对应的秒数
MONTH_SECONDS = 30 * 24 * 60 * 60


class _RedisStorageBase(object):
    """
    所有redis容器基类
    """
    def __init__(
            self,
            cache_key,
            redis_instance=redis,
            expire_time=DAY_SECONDS,
            need_pickle=False,
            need_compress=False,
    ):
        """
        :param cache_key: redis中的键值
        :param redis_instance: 使用的redis,默认放在普通redis中
        :param expire_time: 过期时间
        :param need_pickle: 由于redis存储只支持string类型的value, 如果不是string需要pickle操作进行序列化
          需要注意的是, 如果need_pickle为False, 那么不管写入什么类型的数据, 重新获取后的值均为string类型
        :param need_compress: 是否需要压缩数据后存储，数据压缩采用zlib的默认压缩级别.
        """
        self._cache_key = cache_key
        self._redis_instance = redis_instance
        self._expire_time = expire_time
        self._need_pickle = need_pickle
        self._need_compress = need_compress

    def clear(self):
        """
        删除所有元素
        """
        self._redis_instance.delete(self._cache_key)

    def cache_exists(self):
        """
        判断缓存是否存在
        :return: bool
        """
        return self._redis_instance.exists(self._cache_key)

    def _serialize(self, value):
        pickle_value = pickle.dumps(value) if self._need_pickle else value
        return zlib.compress(pickle_value) if self._need_compress else pickle_value

    def _deserialize(self, value):
        value = zlib.decompress(value) if self._need_compress else value
        return pickle.loads(value) if self._need_pickle else value

    def _expire(self):
        self._redis_instance.expire(self._cache_key, self._expire_time)


class RedisDict(_RedisStorageBase):
    """
    dict like redis storage
    使用 redis hset
    """
    def copy(self):
        """
        返回一个字典
        :return: dict
        """
        cached_dict = self._redis_instance.hgetall(self._cache_key)
        cached_dict = {key: self._deserialize(value) for key, value in cached_dict.items()}
        return cached_dict

    def get(self, key, default=None):
        """
        获取元素
        """
        value = self._redis_instance.hget(self._cache_key, key)
        if value is None:
            return default
        return self._deserialize(value)

    def mget(self, keys):
        """
        批量获取元素
        :param keys: list / tuple
        :return: {key: value}
        """
        if not keys:
            return {}
        value_list = self._redis_instance.hmget(self._cache_key, keys)
        result = {key: self._deserialize(value) for key, value in zip(keys, value_list)
                  if value is not None}
        return result

    def hincrby(self, key, amount=1):
        """
        整数元素自增
        """
        # 字典元素数据不能进行压缩或pickle
        assert not self._need_compress and not self._need_pickle
        return self._redis_instance.hincrby(self._cache_key, key, amount)

    def has_key(self, key):
        """
        判断是否存在键值为k的元素
        :param key:
        :return: bool
        """
        return self.__contains__(key)

    def items(self):
        """
        :return: list of (key, value)
        """
        copy_dict = self.copy()
        return copy_dict.items()

    def iteritems(self):
        """
        返回(key, value)的迭代器
        """
        if not hasattr(self._redis_instance, "hscan"):
            logging.error("%s does not support hscan" % self._redis_instance)
            return self.items()
        return self._Iter(self)

    def keys(self):
        """
        :return: list of keys
        """
        return self._redis_instance.hkeys(self._cache_key)

    def values(self):
        """
        :return: list of values
        """
        value_list = self._redis_instance.hvals(self._cache_key)
        value_list = [self._deserialize(value) for value in value_list]
        return value_list

    def pop(self, key, default=None):
        """
        删除k, 并返回对应的value。如果没有对应的k, 返回d。
        和dict不同的是,这个地方不会抛KeyError异常
        :return: value
        """
        value = self.get(key, default)
        self._redis_instance.hdel(self._cache_key, key)
        return value

    def setdefault(self, key, value=None):
        """
        如果k不存在设置k对应的value为d
        :return: k对应的value值
        """
        save_value = self._serialize(value)
        is_set = self._redis_instance.hsetnx(self._cache_key, key, save_value)
        if is_set:
            self._expire()
            return value
        return self.get(key, value)

    def update(self, E=None, **F):
        """
        D.update([E, ]**F) -> None.  Update D from dict/iterable E and F.
        If E present and has a .keys() method, does:     for k in E: D[k] = E[k]
        If E present and lacks .keys() method, does:     for (k, v) in E: D[k] = v
        In either case, this is followed by: for k in F: D[k] = F[k]
        """
        if not E:
            key_value_list = []
        elif hasattr(E, "keys"):
            key_value_list = [(k, E[k]) for k in E]
        else:
            key_value_list = [(k, v) for (k, v) in E]

        for k in F:
            key_value_list.append((k, F[k]))

        # 由于redis的pipeline没有实现hset_pickle, 这个地方先手动pickle
        key_value_list = [(k, self._serialize(v)) for (k, v) in key_value_list]

        pipeline = self._redis_instance.pipeline(transaction=False)
        for (key, value) in key_value_list:
            pipeline.hset(self._cache_key, key, value)
        pipeline.execute()

        if key_value_list:
            self._expire()

    def __contains__(self, item):
        """
        D.__contains__(y) --> True if D has a key k, else False
        """
        return self._redis_instance.hexists(self._cache_key, item)

    def __setitem__(self, key, value):
        """
        x.__setitem__(key, value) <==> x[key] = value
        """
        save_value = self._serialize(value)
        self._redis_instance.hset(self._cache_key, key, save_value)
        self._expire()

    def __delitem__(self, key):
        """
        x.__delitem__(key) <==> del x[key]
        """
        exists = self._redis_instance.hdel(self._cache_key, key)
        if exists == 0:
            raise KeyError(key)

    def __getitem__(self, key):
        """
        x.__getitem__(key) <==> x[key]
        与dict不同的是, 如果key不存在会返回None, 而不是抛KeyError异常
        """
        return self.get(key)

    def __iter__(self):
        """
        x.__iter__() <==> iter(x)
        如果有大量元素, 请使用iteritems()
        """
        key_list = self.keys()
        return iter(key_list)

    def __len__(self):
        """
        x.__len__() <==> len(x)
        """
        return self._redis_instance.hlen(self._cache_key)

    # =========== 其它方法, 兼容老版本 ============
    def set_value(self, key, value):
        self[key] = value

    def get_value(self, key):
        return self[key]

    def exists(self, key):
        return key in self

    def delete_keys(self, *keys):
        """
        删除一些key值
        :return: 被删除key的个数
        """
        if not keys:
            return 0
        return self._redis_instance.hdel(self._cache_key, *keys)

    # =========== 私有 ============
    class _Iter(object):
        """
        iteritems迭代器
        """
        def __init__(self, redis_dict, fetch_per_count=100):
            self.__redis_dict = redis_dict
            self.__redis_instance = redis_dict._redis_instance
            self.__cache_key = redis_dict._cache_key
            self.__deserialize = redis_dict._deserialize

            self.fetch_per_count = fetch_per_count
            self.__next_cursor = None
            self.__cur_values = None

        def __iter__(self):
            return self

        def next(self):
            if self.__next_cursor == 0 and not self.__cur_values:
                raise StopIteration

            if self.__cur_values:  # should be a dict
                key, value = self.__cur_values.popitem()
                value = self.__deserialize(value)
                return key, value

            cursor = self.__next_cursor if self.__next_cursor is not None else 0
            try:
                self.__next_cursor, self.__cur_values = \
                    self.__redis_instance.hscan(self.__cache_key, cursor=cursor, count=self.fetch_per_count)
            except:
                # 老版本redis不支持HSCAN命令
                self.__next_cursor = 0
                self.__cur_values = self.__redis_instance.hgetall(self.__cache_key)
            return self.next()


class RedisSet(_RedisStorageBase):
    """
    存储数据集合
    使用 redis set

    需要注意的是，对于字典等类型数据，可能不能正常工作。(pickle结果不确定)
    e.g.
        >>> import cPickle
        >>> msg = {'type': 'reading', '_id': 1234, 'time': 12345656, 'content': 'hello, world', 'badge': True,
        ... 'username': 'name', 'is_online': True}
        >>> t1 = cPickle.dumps(msg)
        >>> t = cPickle.loads(t1)
        >>> t2 = cPickle.dumps(t)
        >>> msg == t
        True
        >>> t1 == t2
        False
    """
    def add(self, value):
        """
        添加一个值
        如果添加多个值, 请使用update
        """
        save_value = self._serialize(value)
        self._redis_instance.sadd(self._cache_key, save_value)
        self._expire()

    def remove(self, value):
        """
        移除value, 如果value不在集合中, 抛出KeyError异常
        如果删除多个值, 请使用discard
        """
        succeed = self._remove_value(value)
        if succeed == 0:
            raise KeyError(value)

    def discard(self, *values):
        """
        移除value, 如果value不在集合中, do noting
        :return: 被移除的元素个数
        """
        return self._remove_value(*values)

    def pop(self):
        """
        随机移除一个数据,并返回
        如果集合为空, 抛出KeyError异常
        """
        value = self._redis_instance.spop(self._cache_key)
        if value is None:
            raise KeyError
        return self._deserialize(value)

    def sample(self, count):
        """
        随机返回count个元素的列表
        """
        value_list = self._redis_instance.srandmember(self._cache_key, count)
        return [self._deserialize(value) for value in value_list]

    def update(self, *args):
        """
        更新集合元素
        如果参数可以迭代, 迭代加入参数中元素
        """
        if not args:
            return 
        value_list = []
        for value in args:
            if not hasattr(value, "__iter__"):
                value_list.append(value)
                continue
            for item in value:
                value_list.append(item)

        value_list = [self._serialize(value) for value in value_list]
        self._redis_instance.sadd(self._cache_key, *value_list)
        self._expire()

    def copy(self):
        """
        返回一个set集合
        """
        values = self._redis_instance.smembers(self._cache_key)
        return {self._deserialize(v) for v in values}

    def __contains__(self, value):
        """
        S.__contains__(y) --> True if S has a key k, else False
        """
        save_value = self._serialize(value)
        return self._redis_instance.sismember(self._cache_key, save_value)

    def __iter__(self):
        """
        x.__iter__() <==> iter(x)
        """
        if not hasattr(self._redis_instance, "sscan"):
            logging.error("%s does not support sscan" % self._redis_instance)
            values = self.copy()
            return iter(values)
        return self._Iter(self)

    def __len__(self):
        """
        x.__len__() <==> len(x)
        """
        return self._redis_instance.scard(self._cache_key)

    def _remove_value(self, *values):
        if not values:
            return 0
        value_list = [self._serialize(v) for v in values]
        return self._redis_instance.srem(self._cache_key, *value_list)

    # =========== 其它方法, 兼容老版本 ============
    def get_members(self):
        return self.copy()

    def cache_delete(self):
        """
        删除集合
        """
        return self.clear()

    # =========== 私有 ============
    class _Iter(object):
        def __init__(self, redis_set, fetch_per_count=100):
            self.__redis_set = redis_set
            self.__redis_instance = redis_set._redis_instance
            self.__cache_key = redis_set._cache_key
            self.__deserialize = redis_set._deserialize

            self.fetch_per_count = fetch_per_count
            self.__next_cursor = None
            self.__cur_values = None

        def __iter__(self):
            return self

        def next(self):
            if self.__next_cursor == 0 and not self.__cur_values:
                raise StopIteration

            if self.__cur_values:  # should be list
                value = self.__cur_values.pop()
                return self.__deserialize(value)

            cursor = self.__next_cursor if self.__next_cursor is not None else 0
            try:
                self.__next_cursor, self.__cur_values = \
                    self.__redis_instance.sscan(self.__cache_key, cursor=cursor, count=self.fetch_per_count)
            except:  # redis.ResponseError
                # 老版本redis不支持SSCAN命令
                self.__next_cursor = 0
                values = self.__redis_instance.smembers(self.__cache_key)
                self.__cur_values = list(values)

            return self.next()


class RedisSortedSet(_RedisStorageBase):
    """
    存储带有score的有序集合
    利用 redis zset

    同RedisSet，对于字典等类型数据，可能不能正常工作。@see RedisSet
    """
    def add(self, value, score=None):
        """
        添加一个value
        :param value:
        :param score: 如果不给, 默认为当前时间戳
        """
        score = score if score is not None else time.time()
        self.madd(score, value)

    def madd(self, *args, **kwargs):
        """
        添加元素, 需要注意的是, 这个方法与add方法score和value顺序不一致!
        :param args: score1, name1, score2, name2
        :param kwargs: name1=score1, name2=score2
        :return:
        """
        score_name_list = list(args)
        for i in range(1, len(score_name_list), 2):
            score_name_list[i] = self._serialize(score_name_list[i])

        for name, score in kwargs.items():
            score_name_list.append(score)
            score_name_list.append(self._serialize(name))

        if not score_name_list:
            return

        self._redis_instance.zadd(self._cache_key, *score_name_list)
        self._expire()

    def remove(self, *values):
        """
        移除values
        :return: 被移除元素个数
        """
        if not values:
            return 0
        value_list = [self._serialize(v) for v in values]
        return self._redis_instance.zrem(self._cache_key, *value_list)

    def values_by_score(self, min_score="-inf", max_score="+inf", start=None, num=None, reverse=False):
        """
        获取指定score区间内的元素
        :return: [value], list of value
        """
        if min_score is None:
            min_score = "-inf"
        if max_score is None:
            max_score = "+inf"

        if not reverse:
            value_list = self._redis_instance.zrangebyscore(self._cache_key, min_score, max_score, start, num)
        else:
            value_list = self._redis_instance.zrevrangebyscore(self._cache_key, max_score, min_score, start, num)

        return [self._deserialize(value) for value in value_list]

    def values_by_score_with_score(self, min_score="-inf", max_score="+inf", start=None, num=None, reverse=False):
        """
        获取指定score区间内的元素, 并返回对应的score值
        :return: [(value, score)], list of (value, score)
        """
        if not reverse:
            value_list = self._redis_instance.zrangebyscore(self._cache_key, min_score, max_score,
                                                            start, num, withscores=True)
        else:
            value_list = self._redis_instance.zrevrangebyscore(self._cache_key, max_score, min_score,
                                                               start, num, withscores=True)

        return [(self._deserialize(value), score) for (value, score) in value_list]

    def values_by_range(self, start=0, end=-1, reverse=False):
        """
        返回指定区间内的元素
        :return: [value], list of value
        """
        if reverse:
            value_list = self._redis_instance.zrevrange(self._cache_key, start, end)
        else:
            value_list = self._redis_instance.zrange(self._cache_key, start, end)
        return [self._deserialize(value) for value in value_list]

    def values_by_range_with_score(self, start=0, end=-1):
        """
        返回指定区间内的元素
        :return: [(value, score)], list of (value, score)
        """
        value_list = self._redis_instance.zrange(self._cache_key, start, end, withscores=True)
        return [(self._deserialize(value), score) for (value, score) in value_list]

    def count_within_score(self, min_score="-inf", max_score="+inf"):
        """
        获取score介于给定score之间的元素个数
        注: 如果获取所有元素数量，请使用 len, @see __len__
        :return: int
        """
        return self._redis_instance.zcount(self._cache_key, min_score, max_score)

    def update_score(self, value, score, set_flag=False):
        """
        更新value对应的score值, 如果value不存在会加入value
        :param value:
        :param score:
        :param set_flag: 如果为True, 将分值设为score, 否则在原来基础上增加score
        :return: 新的score值
        """
        if set_flag:  # 这种情况, 直接调用插入方法更新score值
            self.add(value, score)
            return score

        save_value = self._serialize(value)
        now_score = self._redis_instance.zincrby(self._cache_key, save_value, score)
        self._expire()
        return now_score

    def score(self, value):
        """
        获取value对应的score值
        :param value:
        :return: float, 如果value存在, 否则返回None
        """
        save_value = self._serialize(value)
        return self._redis_instance.zscore(self._cache_key, save_value)

    def remove_range_by_score(self, min_score, max_score):
        """
        删除score值介于min_score和max_score之间(包括边界)的成员
        :param min_score:
        :param max_score:
        :return: 被移除成员的数量
        """
        return self._redis_instance.zremrangebyscore(self._cache_key, min_score, max_score)

    def remove_range_by_rank(self, start, stop):
        """
        删除位于排名内的成员，包含start, stop
        :param start: 以0为底, -1表示最后一个成员
        :param stop:
        :return: 被移除成员的数量
        """
        return self._redis_instance.zremrangebyrank(self._cache_key, start, stop)

    def __len__(self):
        """
        x.__len__() <==> len(x)
        """
        return self._redis_instance.zcard(self._cache_key)

    def __contains__(self, value):
        save_value = self._serialize(value)
        score = self._redis_instance.zscore(self._cache_key, save_value)
        return score is not None

    def __iter__(self):
        """
        x.__iter__() <==> iter(x)
        迭代返回(name, value)值
        """
        if not hasattr(self._redis_instance, "zscan"):
            logging.error("%s does not support zscan" % self._redis_instance)
            value_score_list = self.values_by_range_with_score(0, -1)
            return iter(value_score_list)

        return self._Iter(self)

    # =========== 私有 ============
    class _Iter(object):
        def __init__(self, redis_set, fetch_per_count=100):
            self.__redis_set = redis_set
            self.__redis_instance = redis_set._redis_instance
            self.__cache_key = redis_set._cache_key
            self.__deserialize = redis_set._deserialize

            self.fetch_per_count = fetch_per_count
            self.__next_cursor = None
            self.__cur_values = None

        def __iter__(self):
            return self

        def next(self):
            if self.__next_cursor == 0 and not self.__cur_values:
                raise StopIteration

            if self.__cur_values:  # should be list
                value, score = self.__cur_values.pop()
                return self.__deserialize(value), score

            cursor = self.__next_cursor if self.__next_cursor is not None else 0
            try:
                self.__next_cursor, self.__cur_values = \
                    self.__redis_instance.zscan(self.__cache_key, cursor=cursor, count=self.fetch_per_count)
            except:
                # 老版本redis不支持ZSCAN命令
                self.__next_cursor = 0
                self.__cur_values = self.__redis_instance.zrange(self.__cache_key, 0, -1, withscores=True)

            return self.next()


class RedisCounter(object):
    """
    在redis中记录次数
    与python的Counter不同的是, 这里不涉及获取次数最多(最少)的元素
    因此选择hset存储,而不是zset, 以便获取更好的更新次数性能
    """
    def __init__(self, cache_key, redis_instance=redis, expire_time=DAY_SECONDS, delete_0=True):
        """
        :param cache_key: redis中的键值
        :param redis_instance: 使用的redis,默认放在普通redis中
        :param expire_time: 过期时间
        :param delete_0: 是否删除记数为0的元素
        """
        self._cache_key = cache_key
        self._redis_instance = redis_instance
        self.expire_time = expire_time
        self.delete_0 = delete_0

    def get_count(self, key):
        """
        获取key的记数值
        :param key:
        :return: int
        """
        value = self._redis_instance.hget(self._cache_key, key)
        return int(value or 0)

    def mget_count(self, *keys):
        """
        获取一组key对应的次数
        :param keys:
        :return: {key: count}
        """
        if not keys:
            return {}
        value_list = self._redis_instance.hmget(self._cache_key, keys)
        return {key: int(value or 0) for key, value in zip(keys, value_list)}

    def incr(self, key, count=1):
        """
        更新记数
        :param key:
        :param count:
        :return: 更新的记数值
        """
        new_count = self._redis_instance.hincrby(self._cache_key, key, count)
        if new_count == 0 and self.delete_0:
            self._redis_instance.hdel(self._cache_key, key)
        self._expire()
        return new_count

    def remove(self, *keys):
        """
        移除keys中所有元素的记数
        :return: 被移除元素个数
        """
        if not keys:
            return 0
        return self._redis_instance.hdel(self._cache_key, *keys)

    def _expire(self):
        self._redis_instance.expire(self._cache_key, self.expire_time)

    def _get_all_count(self):
        """
        主要给testcase使用
        :return: {key: count}
        """
        result = self._redis_instance.hgetall(self._cache_key)
        for key, value in result.items():
            result[key] = int(value)
        return result

    def clear(self):
        self._redis_instance.delete(self._cache_key)


class RedisList(_RedisStorageBase):
    """
    redis list
    """
    def lpush(self, value):
        """
        use lpush to add value
        """
        save_value = self._serialize(value)
        self._redis_instance.lpush(self._cache_key, save_value)
        self._expire()

    def lpop(self):
        """
        use lpop to remove value
        """
        value = self._redis_instance.lpop(self._cache_key)
        if value is None:
            return None
        self._expire()
        return self._deserialize(value)

    def lrem(self, value, is_serialized=True):
        """
        user lrem to remove value
        :param value:
        :param is_serialized:  value 是否序列化以后数据
        :return:
        """
        if not is_serialized:
            value = self._serialize(value)
        self._redis_instance.lrem(self._cache_key, 0, value)
        self._expire()

    def rpush(self, value):
        """
        use rpush to add value
        """
        save_value = self._serialize(value)
        self._redis_instance.rpush(self._cache_key, save_value)
        self._expire()

    def rpop(self):
        """
        use rpop to remove value
        """
        value = self._redis_instance.rpop(self._cache_key)
        if value is None:
            return None
        self._expire()
        return self._deserialize(value)

    def range(self, start, end):
        """
        use lrange get values
        """
        values = self._redis_instance.lrange(self._cache_key, start, end)
        return [self._deserialize(value) for value in values]

    def range_with_raw(self, start, end):
        """
        use lrange get values
        """
        values = self._redis_instance.lrange(self._cache_key, start, end)
        return [self._deserialize(value) for value in values], values

    def remove(self, *values):
        """
        batch version of lrem
        """
        value_list = [self._serialize(value) for value in values]
        pipeline = self._redis_instance.pipeline(transaction=False)
        for value in value_list:
            self.lrem(value)
        pipeline.execute()
        self._expire()

    def rpoplpush(self):
        """
        rpop->lpush
        """
        self._redis_instance.rpoplpush(self._cache_key, self._cache_key)

    def __len__(self):
        return self._redis_instance.llen(self._cache_key)

    def __getitem__(self, index):
        """
        x.__getitem__(index) <==> x[index]
        """
        value = self._redis_instance.lindex(self._cache_key, index)
        if value is None:
            return None
        return self._deserialize(value)

    def __setitem__(self, key, value):
        """
        x.__setitem__(key, value) <==> x[key] = value
        """
        save_value = self._serialize(value)
        self._redis_instance.lset(self._cache_key, key, save_value)
        self._expire()


class BasicBadgeManager(object):
    """
    通用badge manager

    使用实例的方式，初始化时必须提供 带1个可变参数的 cache_key
    """
    my_redis = redis
    expire_time = 60 * 60 * 24 * 30

    def __init__(self, basic_cache_key, my_redis=None, expire_time=None):
        self.basic_cache_key = basic_cache_key
        if my_redis:
            self.my_redis = my_redis
        if expire_time:
            self.expire_time = expire_time

    def _build_cache_key(self, key):
        return self.basic_cache_key % key

    def increase_badge(self, uid, service_id):
        key = self._build_cache_key(uid)
        self.my_redis.sadd(key, service_id)
        self.my_redis.expire(key, self.expire_time)

    def decrease_badge(self, uid, service_id):
        key = self._build_cache_key(uid)
        return self.my_redis.srem(key, service_id)

    def delete_badge(self, uid):
        key = self._build_cache_key(uid)
        return self.my_redis.delete(key)

    def has_new_badge(self, uid):
        key = self._build_cache_key(uid)
        return self.my_redis.exists(key)

    def get_badge_num(self, uid):
        key = self._build_cache_key(uid)
        return self.my_redis.scard(key)

    def get_badge_members(self, uid):
        key = self._build_cache_key(uid)
        return self.my_redis.smembers(key)

    def service_has_badge(self, uid, service_id):
        key = self._build_cache_key(uid)
        return self.my_redis.sismember(key, service_id)


class GeneralListCacheByTime(object):
    """
    以时间为顺序的 cache for list

    需要注意的是，对于字典等类型数据，可能不能正常工作。
    @see RedisSortedSet
    """
    def __init__(self, redis_key, redis_instance=redis, expire_time=24*60*60, need_pickle=False,
                 recycle=False, time_span_day=None, max_length=None):
        """
        :param recycle: 是否保存所有的redis key供垃圾回收, 当group_id量很大时建议recycle=False
        :param time_span_day: 有序队列的时间跨度，防止队列过长，为None时表示不限制时间 
        :param max_length: 有序队列的最大长度，防止队列过长，为None时表示不限制长度 
        """
        self.redis_key = redis_key
        self.redis_instance = redis_instance
        self.expire_time = expire_time
        self.need_pickle = need_pickle
        self.recycle = recycle
        self.time_span_seconds = DAY_SECONDS * int(time_span_day) if time_span_day else None
        self.max_length = int(max_length) if max_length else None
        # 保存该 cache key 拥有的group_ids，用于垃圾回收
        if recycle:
            group_set_key = "%s:_GROUP_SET" % (redis_key, )
            self.group_id_set = RedisSet(group_set_key, redis_instance=redis_instance)

    def get_cache_key(self, group_id):
        return "%s:%s" % (self.redis_key, group_id)

    def _get_container(self, group_id):
        cache_key = self.get_cache_key(group_id)
        return RedisSortedSet(cache_key, self.redis_instance, self.expire_time, self.need_pickle)

    def is_member(self, group_id, member):
        """
        该元素是否存在
        """
        container = self._get_container(group_id)
        return member in container

    def remove_member(self, group_id, member):
        """
        从时间列表中移除元素
        """
        container = self._get_container(group_id)
        container.remove(member)

    def _delete_redundant_data(self, group_id, time_=None):
        """
        删除多余的数据
        策略：1、根据时间跨度删除过去xx天以前的数据
             2、根据最大长度删除历史数据
        :param group_id: 
        :return: 
        """
        container = self._get_container(group_id)
        if self.time_span_seconds:
            threshold_score = self._get_score_with_time(time_) - self.time_span_seconds
            container.remove_range_by_score(0, threshold_score)
        elif self.max_length:
            # https://redis.io/commands/zremrangebyrank
            # 仅保留末尾self.max_length个元素
            # zremrangebyrank同时会删除stop右边界，所以需要额外-1
            container.remove_range_by_rank(0, -self.max_length-1)

    def add_member(self, group_id, member, time_=None, force_update=False):
        """
        时间列表中添加新元素
        :param time_: 时间
        :param force_update:  强制更新
        """
        container = self._get_container(group_id)
        if self.is_member(group_id, member) and not force_update:
            return
        score = self._get_score_with_time(time_)
        container.add(member, score)
        if self.recycle:
            self.group_id_set.add(group_id)
        # 保持固定长度，清除业务场景多余的数据
        self._delete_redundant_data(group_id, time_)

    def add_members(self, group_id, **kwargs):
        """
        时间列表中添加新元素
        :param group_id:
        :param kwargs: {member: time}
        :return:
        """
        if not kwargs:
            return
        container = self._get_container(group_id)
        member_2_score = {member: self._get_score_with_time(time_) for member, time_ in kwargs.items()}
        container.madd(**member_2_score)
        if self.recycle:
            self.group_id_set.add(group_id)
        # 保持固定长度，清除业务场景多余的数据
        self._delete_redundant_data(group_id)

    def get_member_by_time(self, group_id, start_time, end_time, with_score=False, start=None, num=None, reverse=False):
        """
        获得指定时间内的member
        """
        container = self._get_container(group_id)
        min_score = self._get_score_with_time(start_time)
        max_score = self._get_score_with_time(end_time)
        return container.values_by_score_with_score(min_score, max_score, start=start, num=num, reverse=reverse) if with_score else \
            container.values_by_score(min_score, max_score, start=start, num=num, reverse=reverse)

    def get_member_count_by_time(self, group_id, start_time, end_time):
        """
        获得指定时间内的member数量
        """
        container = self._get_container(group_id)
        min_score = self._get_score_with_time(start_time)
        max_score = self._get_score_with_time(end_time)
        return container.count_within_score(min_score, max_score)

    def get_member_join_time(self, group_id, member):
        """
        获得member的加入时间
        :return: datetime or None
        """
        container = self._get_container(group_id)
        score = container.score(member)
        if not score:
            return None
        return timestamp_to_datetime(score)

    def get_member_by_rank(self, group_id, start=0, end=-1, desc=False):
        """
        获得指定排名内的member
        :param group_id: 组别
        :param start: 开始index
        :param end: 结束index, 默认取全部
        :param desc: 是否降序(第0名为最近的)
        :return: [member0, member1]
        """
        container = self._get_container(group_id)
        return container.values_by_range(start, end, reverse=desc)

    def get_member_count(self, group_id):
        container = self._get_container(group_id)
        return len(container)

    def clear_member_by_rank(self, group_id, start, end):
        """
        :param group_id:
        :param start: 显式要求输入是为了保证调用者清楚自己在干什么
        :param end:
        :return:
        """
        container = self._get_container(group_id)
        result = container.remove_range_by_rank(start, end)
        if self.recycle and not len(container):
            self.group_id_set.discard(group_id)
        return result

    def clear_specific_group_expired_value(self, group_id, deadline):
        """
        将deadline之前指定group的member全部删掉
        """
        score = self._get_score_with_time(deadline)
        container = self._get_container(group_id)
        container.remove_range_by_score(0, score)
        if self.recycle and not len(container):
            self.group_id_set.discard(group_id)

    def clear_expired_value(self, deadline):
        """
        将deadline之前的member全部删掉
        【通常是脚本定期使用删除历史数据，针对全部的group成员】
        """
        if not self.recycle:
            return
        for group_id in self.group_id_set:
            self.clear_specific_group_expired_value(group_id, deadline)

    def clear_member(self, group_id):
        """
        清空组内所有成员
        """
        container = self._get_container(group_id)
        container.clear()
        if self.recycle:
            self.group_id_set.discard(group_id)

    def is_group_member(self, group_id):
        """
        元素是否在
        """
        return group_id in self.group_id_set

    @staticmethod
    def _get_score_with_time(time_=None):
        """
        将时间转换成score <timestamp>值
        :param time_:
        :return: float
        """
        if time_ is None:
            return time.time()
        if isinstance(time_, (int, float)):
            return time_
        if isinstance(time_, datetime.datetime):
            # 通常传datetime类型的都是各个model的created_time之类的，可以简单精确到秒就可以了
            return convert_datime_to_timestamp(time_)
        return float(time_)


class GeneralListCache(object):
    """
    cache for list, FIFO顺序
    用来管理一组RedisList
    get_cache_key用来生成redis key, 每个key对应一个RedisList
    """
    def __init__(self, redis_key, redis_instance=redis, expire_time=24*60*60, need_pickle=False, recycle=False):
        """
        :param recycle: 是否保存所有的redis key供垃圾回收, 当group_id量很大时建议recycle=False
        """
        self.redis_key = redis_key
        self.redis_instance = redis_instance
        self.expire_time = expire_time
        self.need_pickle = need_pickle
        self.recycle = recycle
        if recycle:
            group_set_key = "%s_general_list_group_set" % (redis_key, )
            # 保存该 cache key 拥有的group_ids，用于垃圾回收
            # pop member清空redis list后,会同步清除group_id_set中的元素
            # 但是对于redis中过期删除的,group_id_set中存储的group_id并不会自动删除
            # 固定使用redis(而非persist_redis)存储
            self.group_id_set = RedisSet(group_set_key, redis_instance=redis)

    def get_cache_key(self, group_id):
        return "%s:%s" % (self.redis_key, group_id)

    def _get_container(self, group_id):
        cache_key = self.get_cache_key(group_id)
        return RedisList(cache_key, self.redis_instance, self.expire_time, self.need_pickle)

    def pop_member(self, group_id):
        """
        取出元素
        """
        container = self._get_container(group_id)
        result = container.lpop()
        # rpush放入None, pop时result=None, 因此不能使用if not result判断列表是否为空
        if self.recycle and not len(container):
            self.group_id_set.discard(group_id)
        return result

    def pop_members(self, group_id):
        """
        取出所有元素
        """
        container = self._get_container(group_id)
        result = container.range(0, -1)
        container.clear()
        if self.recycle:
            self.group_id_set.discard(group_id)
        return result

    def members(self, group_id, start=0, end=-1):
        """
        取所有元素,但不删除
        :param group_id: group_id
        :param start: 开始下标, [包含
        :param end: 结束下标, ]包含
        :return: list
        """
        container = self._get_container(group_id)
        return container.range(start, end)

    def members_with_raw(self, group_id, start=0, end=-1):
        """
        取所有元素,但不删除
        :param group_id: group_id
        :param start: 开始下标, [包含
        :param end: 结束下标, ]包含
        :return: (list of deserialized, list of serialized)
        """
        container = self._get_container(group_id)
        return container.range_with_raw(start, end)

    def add_member(self, group_id, member):
        """
        添加元素
        """
        container = self._get_container(group_id)
        container.rpush(member)
        if self.recycle:
            self.group_id_set.add(group_id)

    def delete_member(self, group_id, member, is_serialized=True):
        """
        删除元素
        """
        container = self._get_container(group_id)
        result = container.lrem(member, is_serialized=is_serialized)
        if self.recycle and not len(container):
            self.group_id_set.discard(group_id)
        return result

    def length(self, group_id):
        """
        列表长度
        """
        container = self._get_container(group_id)
        return len(container)

    def clear_all(self):
        """
        删除所有元素
        """
        if not self.recycle:
            return
        for group_id in self.group_id_set:
            container = self._get_container(group_id)
            container.clear()
        self.group_id_set.clear()


class DailyCounter(object):
    """
    每日计数器
    """

    def __init__(self, keyword, expire_time=60 * 60 * 24, redis_instance=redis, specific_date=None):
        """
        keyword:  计数器的标识名字
        redis_instance: 使用的redis实例
        expire_time: redis过期时间
        specific_date: 指定计数器的计算时间
        """
        self.keyword = keyword
        self.expire_time = expire_time
        self.redis_instance = redis_instance
        self.specific_date = specific_date

    def _build_daily_counter_key(self):
        specific_date = self.specific_date or datetime.date.today()
        return "redis_daily_counter_key_%s_%s" % (self.keyword, specific_date)

    def update_value(self, value=1):
        """
        跟新计数器的值
        """
        counter_key = self._build_daily_counter_key()
        self.redis_instance.incrby(counter_key, value)
        self.redis_instance.expire(counter_key, self.expire_time)

    def get_value(self):
        """
        获取计数器的值
        """
        counter_key = self._build_daily_counter_key()
        return int(self.redis_instance.get(counter_key) or 0)


class RedisHyperLogLog(_RedisStorageBase):
    """
    Redis HyperLogLog操作的封装
    用途：'大批量'数据的去重计数, 占用空间很少
    经典使用场景：UV计算(PV计算需要自己实现)
    不适用场景: 对结果要求绝对精确的场景

    HyperLogLog是一种在大数据场景中基于概率统计去重技术的算法, 不会具体存储各个数据
    空间复杂度为O(log(log(N)), 时间复杂度为O(1)
    redis的实现，一个存储2^64个数据的HyperLogLog实例，只需要12KB的空间

    注意: HyperLogLog算法基于统计概率学原理，非绝对准确，不适用于对结果要求绝对精确的场景
    redis的实现在标准误差「0.81%」的前提下能够统计2^64数据
    """
    def get_key(self):
        return self._cache_key

    def record(self, *data):
        """
        :param data: 统计的数据或数据集
        """
        self._redis_instance.pfadd(self._cache_key, *data)
        self._redis_instance.expire(self._cache_key, self._expire_time)

    def get_count(self):
        """
        获取去重计数的结果
        :return:
        """
        return self._redis_instance.pfcount(self._cache_key)

    def merge(self, *source_keys):
        """
        将source_key对应的hyperloglog数据合并到b本实例
        :param source_keys: 其他需要被合并的hyperloglog实例的key
        :return True or False: 是否成功
        """
        return self._redis_instance.pfmerge(self._cache_key, *source_keys)

    def get_merged_count(self, *keys):
        """
        获取多个HyperLogLog集合的计算结果
        :param keys: 要计算的多个HyperLogLog实例的redis key
        :return: 多个HyperLogLog实例的数据去重技术的结果
        """
        temp_key = 'hyperloglog_temp_key' + str(randint(1, 1000))
        self._redis_instance.pfmerge(temp_key, *keys)
        total_count = self._redis_instance.pfcount(temp_key)
        self._redis_instance.delete(temp_key)
        return total_count


class RegisterableClass(object):
    """
    实例可被注册的类
    """

    def __init__(self):
        super(RegisterableClass, self).__init__()
        self.subclasses = {}

    def get_register_base_class(self):
        """
        获得可被注册类的基类（即注册类必须为该类的子类）
        """
        # 默认返回自己所在的类
        return self.__class__

    def register(self, name, subclass):
        to_register_class = self.get_register_base_class()
        if not issubclass(subclass, to_register_class):
            raise ValueError("subclass is not subclass of %s" % to_register_class.__name__)
        if name in self.subclasses:
            raise ValueError("name:%s has been registered" % name)
        else:
            self.subclasses[name] = subclass

    def get_subclass(self, name):
        """
        通过类的名字获得 子类
        """
        if name not in self.subclasses:
            registered_name = ', '.join(self.subclasses.keys())
            raise ValueError("name: %s has not been registered.\n Registered name is:\n%s" % (name, registered_name))
        else:
            return self.subclasses[name]()

    def has_subclass(self, name):
        """
        判断是否有subclass
        """
        return name in self.subclasses
