# -*- coding:utf-8 -*-

from __future__ import absolute_import

import json
from http import HTTPStatus

import time

from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

from log_utils.loggers import elapsed_logger

__all__ = ["ElapsedTimeMiddleware"]


def build_request_items(request):
    get_items = []
    for key, value in request.GET.items():
        if 'password' in key and value:
            continue
        get_items.append('%s=%s' % (key, value))

    post_items = []
    if request.META.get('CONTENT_TYPE') == 'application/json':
        try:
            post_data = json.loads(request.body)
        except:
            raise Exception(request.body)
    else:
        post_data = request.POST
    for key, value in post_data.items():
        if 'password' in key and value:
            continue
        # 因为日志太大，过滤steps_data和sleep_raw_data value的存储，健康助手工程接口：upload_steps_data，upload_sleep_raw_data
        if key in ['steps_data', 'sleep_raw_data'] and len(value) > 64:
            continue

        post_items.append('%s=%s' % (key, value))
    return get_items, post_items


def get_ip_from_request(request):
    """
    从request请求中提取访问ip
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


class ElapsedTimeMiddleware(MiddlewareMixin):
    """
    期待记录当前的callback, 并且在Elapsed Log中打印出 callback
    """

    def __init__(self, get_response=None):
        super(ElapsedTimeMiddleware, self).__init__(get_response)
        self.pstart_time = time.time()

    def process_request(self, request):
        self._reset()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        """
        期待记录当前的callback, 并且在Elapsed Log中打印出 callback
        :param request:
        :param callback:
        :param callback_args:
        :param callback_kwargs:
        :return:
        """
        try:
            view_name = callback.func_name  # If it's a function
        except AttributeError:
            # 如果是对象
            view_name = callback.__class__.__name__ + '.__call__'  # If it's a class

        self.view_name = "%s.%s" % (callback.__module__, view_name)

    def process_response(self, request, response):
        # 这说明Elapsed View的process_request, process_view根本没有被调用
        if not hasattr(self, "view_name"):
            return response

        if response.status_code in [HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.FOUND, HTTPStatus.GATEWAY_TIMEOUT,
                                    HTTPStatus.BAD_REQUEST, 499,
                                    HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.UNAUTHORIZED,
                                    HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND]:
            request_item = build_request_items(request)

            if hasattr(request, 'session'):
                try:
                    if request.user and not isinstance(request.user, AnonymousUser):
                        request_item[0].append('uid=%s' % request.user.id)
                except:
                    pass

            user_agent = request.META.get('HTTP_USER_AGENT', '')
            user_agent = user_agent

            ip = get_ip_from_request(request)
            ip = ip

            http_referer = request.META.get('HTTP_REFERER', '')

            info = "Time Elapsed: %.6fs, Path: %s, Code: %s, Get: %s, Post: %s, %s, %s, view_name: %s, scheme: %s, %s" % (
                (time.time() - self.pstart_time),
                request.path,
                response.status_code,
                request_item[0],
                request_item[1],
                ip,
                user_agent,
                self.view_name,
                "https" if request.is_secure() else "http",
                http_referer
            )
            elapsed_logger.info(info)

        self._reset()  # 避免被下一个异常接口使用

        return response

    def _reset(self):
        self.view_name = ""
        self.pstart_time = time.time()
