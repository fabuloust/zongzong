# -*- coding:utf-8 -*-
"""
大数据相关redis 容器
具体包括：
HyperLogLog: 大数据条件下统计集合中的元素数
BloomFilter（布隆过滤器）: 大数据条件下判断元素是否在集合中
RedisRateLimiter: 限流器
"""
import re
from random import randint

from redis_utils.container.api_redis_client import redis

rate_re = re.compile('([\d]+)/([\d]*)([smhd])')
_PERIODS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
}


def split_rate(rate):
    """
    rate 格式：次数 / 每多少 秒|分|小时|天
    :param rate:
    :return: 次数，秒
    """
    count, multi, period = rate_re.match(rate).groups()
    count = int(count)
    seconds = _PERIODS[period.lower()]
    if multi:
        seconds = seconds * int(multi)
    return count, seconds


class RedisHyperLogLog(object):
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
    def __init__(self, cache_key, expire_time=3600 * 24 * 60, redis_instance=redis):
        """
        :param cache_key: 注意key的唯一性
        :param expire_time: 超时时间，根据场景定义超时时间
        :param redis_instance: 支持配置不同的redis实例
        """
        self.cache_key = cache_key
        self.expire_time = expire_time
        self._redis_instance = redis_instance

    def record(self, *data):
        """
        :param data: 统计的数据或数据集
        """
        self._redis_instance.pfadd(self.cache_key, *data)
        self._redis_instance.expire(self.cache_key, self.expire_time)

    def get_count(self):
        """
        获取去重计数的结果
        :return:
        """
        return self._redis_instance.pfcount(self.cache_key)

    def merge(self, *source_keys):
        """
        将source_key对应的hyperloglog数据合并到b本实例
        :param source_keys: 其他需要被合并的hyperloglog实例的key
        :return True or False: 是否成功
        """
        return self._redis_instance.pfmerge(self.cache_key, *source_keys)

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


class RedisBloomFilter(object):
    """
    redis 布隆过滤器操作封装
    注意：布隆过滤器非精确计算容器，存在一定概率的出错情况
    具体为:
        1.如果过滤器判断元素不在容器中，肯定是正确的
        2.如果过滤器判断元素在容器中，有一定概率是错误的
    注意点： 不支持从容器中删除元素
    """

    def __init__(self, key, initial_size, error_rate=0.01, redis_instance=redis):
        """
        创建布隆过滤器
        注意：
        1. 默认的error_rate(错误率)是 0.01，错误率越低，需要的空间越大
        2. 初始的initial_size需要根据场景评估，预计放入的数量，当实际数量超出设定的大小时，误判率会上升
        3. 不支持参数修改，因此 创建容器时一定要注意参数配置
        4. 当加入的数据量大于容器的容量时，错误率会急剧上升
        :param key:
        :param error_rate: 错误率，0~1
        :param initial_size: 容器可容纳的数据量（根据场景预估，值必须大于场景可能产生的数据量）
        :return: True or False
        """
        self.redis = redis_instance
        self.cache_key = key
        self.size = initial_size
        self.error_rate = error_rate
        if self.redis.exists(key):
            return
        self.redis.bf_reserve(key, error_rate, initial_size)

    def add(self, item):
        """
        添加元素
        :param item:
        :return: 1(新添加) or 0
        """
        return self.redis.bf_add(self.cache_key, item)

    def madd(self, *items):
        """
        添加多个元素
        :param items:
        :return: [1, 0, 1, 1, ...]
        """
        return self.redis.bf_madd(self.cache_key, *items)

    def exists(self, item):
        """
        是否存在item
        :return:  True or False
        """
        return self.redis.bf_exists(self.cache_key, item)

    def mexists(self, *items):
        """
        是否存在多个item
        :param items:
        :return: 结果序列
        """
        return self.redis.bf_mexists(self.cache_key, *items)


class RedisRateLimiter(object):
    """
    redis实现的限流器
    令牌桶算法的原理是定义一个按一定速率产生token的桶，每次去桶中申请token，若桶中没有足够的token则申请失败，否则成功。
    在请求不多的情况下，桶中的token基本会饱和，此时若流量激增，并不会马上拒绝请求，所以这种算法允许一定的流量激增。
    文档：https://github.com/brandur/redis-cell/blob/master/README.md
    说明：空闲时的实际容量 = capacity + 1，多的一个是除了预定义的外，实时生成的
    注意：
    1. 与之前的RateLimiter相比，支持一个值为capacity的脉冲，以应对访问量临时增大
    2. 需要根据场景定义允许的脉冲量，已经常规速率
    3. 主要用途：接口限流，后续有啥可以补充
    """
    def __init__(self, key, capacity, rate, redis_instance=redis):
        """
        :param key: cache_key
        :param capacity: 令牌桶容量
        :param rate: 次数/时间间隔，支持
        's': 秒,
        'm': 分,
        'h': 小时,
        'd': 天,
        """
        self.cache_key = u'redis_throttle_{}'.format(key)
        self.capacity = capacity
        self.rate = rate
        self.permits, self.seconds = split_rate(rate)
        self.redis = redis_instance
        self.redis.cl_throttle(key, capacity, self.permits, self.seconds)

    def acquire(self, get_num=1):
        """
        获取令牌, 返回的5个参数，目前来看只有结果和需要等待的时间是有用的，因此只返回这两个值
        正常能访问的情况下，wait_seconds=-1,
        :param get_num: 获取的个数，一般都是1
        :return success, wait_seconds when token will be available（-1 if success）
        """
        success, capacity, token_num_left, wait_seconds, full_seconds = \
            self.redis.cl_throttle(self.cache_key, self.capacity, self.permits, self.seconds, get_num)
        return success, wait_seconds

    def reset_limit(self):
        """
        重置
        """
        self.redis.delete(self.cache_key)
