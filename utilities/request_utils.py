import json


def get_data_from_request(request):
    """
    从request中提前数据
    :param request:
    :return:
    """
    if request.method == 'GET':
        return request.GET
    elif request.method == 'POST':
        if request.META.get('CONTENT_TYPE') == 'application/json':
            return json.loads(str(getattr(request, "raw_post_data", {}) or getattr(request, "body", {})))
        else:
            return request.POST
    return {}
