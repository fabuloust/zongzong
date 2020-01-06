# -*- coding:utf-8 -*-
"""
RedisGeo
Redis对Geo算法的实现封装
"""
from redis import DataError

from redis_utils.container.api_redis_client import redis
from redis_utils.container.consts import GeoUnitEnum


class RedisGeo(object):
    """
    Redis Geo(地理位置)操作的封装
    RedisGeo通过对经纬度的算法实现包括计算距离，附近的单位查找等功能
    lon: 经度：东经为正
    lat: 维度：北纬为正
    """
    def __init__(self, key, redis_instance=redis):
        self.redis = redis_instance
        self.cache_key = 'redis_geo_' + key

    def add(self, *args):
        """
        添加位置到key集合中,支持一个地点或者多个地点
        :param args: lon, lat, place(如果传多个需要args是3的倍数)，限制为500个
        :return: 1(新增) or 0（修改）
        """
        if len(args) / 3 > 500:
            raise DataError(u"一次最多添加500个！")
        return self.redis.geoadd(self.cache_key, *args)

    def geo_distance(self, place1, place2, unit=GeoUnitEnum.KM):
        """
        计算集合key中两个位置的距离，距离默认为米
        :param place1: place1 name
        :param place2: place2 name
        :param unit: GeoUnit
        :return: float distance
        """
        if unit not in GeoUnitEnum.values():
            raise ValueError("unit is not in GeoUnit")
        return self.redis.geodist(self.cache_key, place1, place2, unit)

    def get_position(self, *places):
        """
        对应的地址如果不存在，则对应的值为None，否则为[lon, lat]
        :param places: 地点名
        :return: [[lon, lat], [lon1, lat1], ...]
        """
        return self.redis.geopos(self.cache_key, *places)

    def get_members_within_radius(self, longitude, latitude, radius, unit=GeoUnitEnum.KM,
                                  withdist=False, count=None, sort=None):
        """
        返回key集合中距离(longitude, latitude)的距离小于radius的单位
        :param longitude
        :param latitude:
        :param radius:
        :param unit: GeoUnit
        :param withdist: 是否返回距离
        :param count: 返回的数量
        :param sort: 是否按距离排序及排序方式
        :return 如果with_dist为true,则返回[[place1, place1_distance], [place2, place2_distance], ...]的二维数组
                否则返回 [place1, place2, ...]
        """

        return self.redis.georadius(self.cache_key, longitude, latitude, radius, unit=unit,
                                    withdist=withdist, count=count, sort=sort)

    def get_members_within_radius_by_member(self, member, radius, unit=GeoUnitEnum.KM,
                                            withdist=False, count=None, sort=None):
        """
        与上一方法的区别是返回集合中地点名代替了经纬度
        """
        if unit not in GeoUnitEnum.values():
            raise ValueError("unit is not in GeoUnit")
        return self.redis.georadiusbymember(self.cache_key, member, radius, unit=unit, withdist=withdist,
                                            count=count, sort=sort)

    def get_hash(self, *members):
        """
        获取集合name中members的哈希值, 对应的值不存在则为None
        :param members: 地点名
        :return: [hash1, hash2, ...]
        """
        return self.redis.geohash(self.cache_key, *members)
