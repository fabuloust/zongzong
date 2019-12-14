import random


def random_str(length=8):
    """
    获取一个特定长度的随机串，只包括英文字母和数字
    """
    if length < 1:
        return ''
    return ''.join(random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', length))
