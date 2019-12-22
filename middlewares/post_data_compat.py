# -*- coding:utf-8 -*-

"""
解决部分客户端POST请求时，实际格式是`application/x-www-form-urlencoded`，即`key1=val1&key2=val2`
但是Content-Type误写为`application/json`的问题

保证类似于请求能被正确处理
curl -v --data 'username=a&password=a' -H 'Content-Type: application/json' 'http://127.0.0.1:8000/api/accounts/login'

注：实际上是客户端的bug，但是由于包括合作方等接口较多，全部修改较为困难，服务器做下兼容吧。。。。
"""
from __future__ import absolute_import

from django.http import QueryDict


class PostContentTypeFixMiddleware(object):
    def process_request(self, request):
        if request.method != 'POST' or request.content_type != "application/json":
            return

        try:
            # 如果的确是application/json类型的数据，为了方便在elapse log中搜索，也加入到POST里，形如"{'a':'b'}="
            request.POST = QueryDict(request.body, encoding=request.encoding)
        except BaseException:
            pass
