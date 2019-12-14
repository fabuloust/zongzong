# -*- coding:utf-8 -*-
"""
常量定义
"""
from utilities.enum import EnumBase, EnumItem


class GeoUnitEnum(EnumBase):
    """
    geo单位choices
    """
    M = EnumItem('m', u'米')
    KM = EnumItem('km', u'千米')
    MI = EnumItem('mi', u'英里')
    FT = EnumItem('ft', u'英尺')


class GeoSortEnum(EnumBase):
    """
    geo_radius操作返回值按距离的排序选择
    """
    ASC = EnumItem('ASC', u'升序')
    DESC = EnumItem('DESC', u'降序' )