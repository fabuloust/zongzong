# -*- coding:utf-8 -*-
import datetime

from django.contrib.auth.models import User

__global_index = 1


def _random_username():
    global __global_index
    __global_index += 1
    return 'username%s' % __global_index


def _random_password():
    global __global_index
    __global_index += 1
    return 'password%s' % __global_index


def _random_email():
    global __global_index
    __global_index += 1
    return 'email-%s@gmail.com' % __global_index


def _random_sex():
    global __global_index
    __global_index += 1
    return 'm' if __global_index % 2 == 0 else 'f'


def _random_date():
    '''
    随机日期, yyyy-MM-dd
    '''
    now = datetime.datetime.now()
    return "%s-%s-%s" % (now.year, now.month, now.day)


def _random_time():
    '''
    随机时间, yyyy-MM-dd HH:mm:ss
    '''
    now = datetime.datetime.now()
    return "%s-%s-%s %s:%s:%s" % (now.year, now.month, now.day, now.hour, now.minute, now.second)


def _random_timestamp():
    return datetime.datetime.now()


def _random_varchar_id():
    """
    获取随机的varchar类型的id，保证了和时间的有序性
    """
    return _current_sec_str()


def _random_int(size=None):
    if size is None:
        return int(_current_sec_str())
    else:
        return int(_current_sec_str()) % size


def _random_float():
    return float(_current_sec_str())


def _current_sec_str():
    global __global_index
    __global_index += 1
    now = datetime.datetime.now()
    return "%s%s" % (now.microsecond, __global_index)


def create_user(password=None, is_staff=False, username=None, is_super=False):
    password = password or '1qaz2wsx'
    username = username or _random_username()
    user = User.objects.create_user(username=username, password=password)
    return user
