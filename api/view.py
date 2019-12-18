from utilities.response import json_http_response


def hello_view(request):
    """
    欢迎接口
    """
    return json_http_response('欢迎来到踪踪')
