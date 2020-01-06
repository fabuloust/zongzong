import json
PAGE_SIZE = 20


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
            try:
                return json.loads(request.body)
            except:
                raise Exception(request.body)
        else:
            return request.POST
    return {}


def get_page_range(page, count_per_page=PAGE_SIZE):
    """
    获取某一页的起始下标值
    """
    page = max(page, 1)
    start_num = (page - 1) * count_per_page
    end_num = start_num + count_per_page
    return start_num, end_num
