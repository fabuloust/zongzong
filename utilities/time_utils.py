import datetime

from utilities.encoding import ensure_unicode


def get_time_show(real_time, just_now_range=60):
    """
    评论的时间显示逻辑
    """
    now = datetime.datetime.now().replace(tzinfo=None)
    seconds = int((now - real_time.replace(tzinfo=None)).total_seconds())
    if seconds < just_now_range:
        result = str(seconds) + u"秒前"
    elif seconds < 30 * 60:
        result = str(seconds / 60) + u"分钟前"
    elif seconds < 60 * 60:
        result = u"半小时前"
    elif seconds < 24 * 60 * 60:
        result = str(seconds / 3600) + u"小时前"
    else:
        result = real_time.strftime("%-m月%-d日")
    return ensure_unicode(result)


def get_age_by_birthday(birthday):
    """
    根据生日获取年龄，向上取整
    :param birthday: datetime.date
    :return: int
    """
    return ((datetime.date.today() - birthday).days + 364) / 365
