# -*- coding: utf-8 -*-

"""
定制化 Response 返回
"""

from __future__ import absolute_import

import datetime
import decimal

from http import HTTPStatus

import json
from django.http import HttpResponse
from django.utils import datetime_safe
from django.views.decorators.cache import cache_page

PAGE_SIZE = 20


def json_http_page_response(result, object_total_count, current_page, page_size=PAGE_SIZE):
    """
    统一分页数据的页码返回格式
    {page: {num_pages, total_count}
    @:param object_list: 当前分页的数据，数量不超过page_size
    @:param object_total_count: 所有符合条件的数据总量，用于计算总页码
    @:param current_page: 当前请求的页码
    @:param page_size: 每页数据条目数
    """
    page_num = (object_total_count + page_size - 1) / page_size
    result = result or {}
    # result不能有page_info字段
    assert "page_info" not in result
    result["page_info"] = {"num_pages": page_num, "total_count": object_total_count, "current_page": current_page}
    return json_http_success(result)


def json_http_success(result=None):
    """
    统一接口正常返回格式
    接口正常时的返回json数据，会额外添加{error_code:0, error_msg: ''}
    """
    return json_http_response_extend(result)


def json_http_error(error_msg, error_code=1, result=None, status=HTTPStatus.BAD_REQUEST):
    """
    统一接口错误返回格式
    :param error_msg: 错误消息
    :param error_code: 错误代码，默认为1
    :param result: 附带的错误数据，一般不需要用
    :param status: 状态码，默认为400
    :return:
    """
    return json_http_response_extend(result, error_code, error_msg, status)
g

def json_http_response_extend(result=None, error_code=0, error_msg=u'', status=HTTPStatus.OK):
    response = {"error_code": error_code, "error_msg": error_msg}
    if result:
        response.update(result)
    return json_http_response(response, status=status)


# Copied. DjangoJSONEncoder from Django 1.3
# 新版Django日期格式做了调整
class DjangoJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    """

    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, o):
        if isinstance(o, datetime.datetime):
            d = datetime_safe.new_datetime(o)
            return d.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        elif isinstance(o, datetime.date):
            d = datetime_safe.new_date(o)
            return d.strftime(self.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        else:
            return super(DjangoJSONEncoder, self).default(o)


def json_http_response(result, status=HTTPStatus.OK, cls=DjangoJSONEncoder):
    return HttpResponse(content=json.dumps(result, cls=cls, ensure_ascii=True).encode('utf-8'),
                        content_type="application/json; charset=UTF-8", status=status)


def string_http_response(result, status=HTTPStatus.OK):
    return HttpResponse(content=result,
                        content_type="application/json; charset=UTF-8", status=status)


@cache_page(60 * 5)
def json_http_response_with_client_cache(request, result, status=HTTPStatus.OK):
    """在"客户端"缓存数据5分钟(因为很多情况下客户端的数据不大可能变化), 使用场景:
       1. 科室，医生问题列表；搜索结果列表
       2. 其他
    """
    return HttpResponse(content=json.dumps(result, ensure_ascii=True, encoding="utf-8"),
                        content_type="application/json; charset=UTF-8", status=status)


class JsonResponse(HttpResponse):
    """
    An HTTP response class that consumes data to be serialized to JSON.
    从 Django 1.1 框架中复制过来

    :param data: Data to be dumped into json. By default only ``dict`` objects
      are allowed to be passed due to a security flaw before EcmaScript 5. See
      the ``safe`` parameter for more information.
    :param encoder: Should be an json encoder class. Defaults to
      ``django.core.serializers.json.DjangoJSONEncoder``.
    :param safe: Controls if only ``dict`` objects may be serialized. Defaults
      to ``True``.
    :param json_dumps_params: A dictionary of kwargs passed to json.dumps().
    """

    def __init__(self, data, encoder=DjangoJSONEncoder, safe=True,
                 json_dumps_params=None, **kwargs):
        if safe and not isinstance(data, dict):
            raise TypeError(
                'In order to allow non-dict objects to be serialized set the '
                'safe parameter to False.'
            )
        if json_dumps_params is None:
            json_dumps_params = {}
        kwargs.setdefault('content_type', 'application/json')
        data = json.dumps(data, cls=encoder, **json_dumps_params)
        super(JsonResponse, self).__init__(content=data, **kwargs)
