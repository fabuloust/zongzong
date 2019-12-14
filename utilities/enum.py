# -*- coding: utf-8 -*-

"""
枚举类
"""


from __future__ import absolute_import

from utilities.encoding import ensure_unicode


class _EnumMeta(type):
    def __init__(cls, name, bases, attr_dict):
        super(_EnumMeta, cls).__init__(name, bases, attr_dict)

        enum_items = []
        value_set = set()
        verbose_set = set()
        for _name, _instance in attr_dict.items():
            if isinstance(_instance, EnumItem):
                assert _instance.value not in value_set
                assert _instance.verbose not in verbose_set
                value_set.add(_instance.value)
                verbose_set.add(_instance.verbose)
                _instance.name = _name
                enum_items.append(_instance)

        enum_items.sort(key=lambda x: x.count)

        choices = []
        values_to_items = {}
        for _instance in enum_items:
            choices.append((_instance.value, _instance.verbose))
            values_to_items[_instance.value] = _instance

        if choices:
            cls.choices = choices
            cls.values_to_items = values_to_items

    def __iter__(cls):
        return iter(cls.choices)

    def __contains__(cls, v):
        return v in cls.values_to_items


class EnumItem(object):
    __count = 0
    __slots__ = ("name", "value", "verbose", "count")

    def __init__(self, value, verbose):
        self.value = value
        self.verbose = verbose
        self.name = ""
        self.count = EnumItem.__count
        EnumItem.__count += 1

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        raise AttributeError(u"不能修改枚举值")

    def __str__(self):
        return "%s: %s" % (self.name, self.value)

    def __repr__(self):
        return "<%s>" % self.__str__()


class EnumBase(metaclass=_EnumMeta):
    """
    An Enum base class for more readable enumerations,
    and compatible with Django's choice convention.
    You may just pass the instance of this class as the choices
    argument of model/form fields.

    Example:
    >>> class TestEnum(EnumBase):
    ...     A = EnumItem('a', 'first')
    ...     B = EnumItem('b', 'second')
    ...
    ...
    >>> TestEnum.A
    'a'
    >>> TestEnum.values()
    ['a', 'b']
    >>> list(TestEnum)
    [('a', 'first'), ('b', 'second')]
    >>> TestEnum.verbose(TestEnum.A)
    'first'
    >>> TestEnum.verbose_safe('c', default=u'未知')
    u'未知'
    """
    __metaclass__ = _EnumMeta

    @classmethod
    def get_key_by_value(cls, v):
        item = cls.values_to_items[v]
        return item.name

    @classmethod
    def verbose(cls, v):
        item = cls.values_to_items[v]
        return item.verbose

    @classmethod
    def verbose_safe(cls, v, default=None):
        try:
            return cls.verbose(v)
        except KeyError:
            return default

    @classmethod
    def values(cls):
        return [_info[0] for _info in cls.choices]

    @classmethod
    def get_value_by_verbose(cls, v):
        unicode_verbose = ensure_unicode(v)
        for value, verbose in cls.choices:
            if ensure_unicode(verbose) == unicode_verbose:
                return value
        raise Exception(u'没有找到对应的verbose')

    def __iter__(self):
        # 当作为django.forms.fields.MultipleChoiceField的choices 要求实例可迭代
        return iter(self.choices)


if __name__ == "__main__":
    # simple test
    # duplicated value
    try:
        class TestEnum1(EnumBase):
            A = EnumItem('a', 'first')
            B = EnumItem('a', 'second')
    except:
        pass
    else:
        assert False

    # duplicated verbose
    try:
        class TestEnum2(EnumBase):
            A = EnumItem('a', 'first')
            B = EnumItem('b', 'first')
    except:
        pass
    else:
        assert False


    class TestEnum(EnumBase):
        A = EnumItem('a', 'first')
        B = EnumItem('b', 'second')


    # __contains__
    assert 'a' in TestEnum
    assert 'c' not in TestEnum

    # __getattr__
    assert TestEnum.A == 'a'
    assert TestEnum.B == 'b'
    try:
        print(TestEnum.C)
        assert False
    except AttributeError:
        pass

    # __iter__
    assert list(TestEnum) == [('a', 'first'), ('b', 'second')]
    assert list(TestEnum()) == [('a', 'first'), ('b', 'second')]

    # get_key_by_value
    assert TestEnum.get_key_by_value('a') == 'A'
    assert TestEnum.get_key_by_value('b') == 'B'

    # values
    assert set(TestEnum.values()) == {'a', 'b'}

    # verbose
    assert TestEnum.verbose('a') == 'first'
    assert TestEnum.verbose('b') == 'second'
    try:
        print(TestEnum.verbose('c'))
    except:
        pass
    else:
        assert False
    assert TestEnum.get_value_by_verbose('first') == 'a'
    assert TestEnum.get_value_by_verbose('second') == 'b'
