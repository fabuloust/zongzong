# -*- coding: utf-8 -*-

"""
encoding
========

编码相关


from：
-----
* chunyu/utils/general/encoding_utils.py
* medweb_utils/text_utils.py
* api/utilities/base_utils.py

TODO:
* 处理 hash 有关的
* 处理 client 有关的
"""

from __future__ import absolute_import
import hashlib


def ensure_utf8(str1, errors='strict'):
    if not str1:
        return ''
    if isinstance(str1, str):
        return str1.encode('utf-8', errors)
    return str1


def ensure_unicode(str1, errors='strict'):
    if not str1:
        return u''
    if isinstance(str1, str):
        return str1
    else:
        return str1.decode('utf-8', errors)


def convert_to_unicode_and_strip_space(value):
    """
    保证value为unicode
    """
    if isinstance(value, (float, int)):
        return str(int(value))
    else:
        return ensure_unicode(value).strip()


def md5_hex(url):
    """
    返回url的utf8编码对应的hex digest
    """
    url = ensure_utf8(url)
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


def encode_for_client(content):
    """
    为了fix客户端的bug：\n, %, "
    """
    ENCODE_DICT = {'\n': ' ', '%': u'％', '"': "'", '/': u'/'}

    for key, value in ENCODE_DICT.items():
        content = content.replace(key, value)

    return content


def convert_to_unicode_string(value):
    """
    将value转换成unicode格式的字符串
    """
    return ensure_unicode(str(ensure_utf8(value)))
