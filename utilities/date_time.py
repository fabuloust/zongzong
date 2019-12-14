# -*- coding: utf-8 -*-


"""
通用的时间处理函数


* 字符串转时间
* 时间转字符串
* 时间戳处理
* 微秒时间处理
* 用差值计算时间
* 计算时间差值
* 通用函数


from:
-----
* medweb_utils/utilities/date_time_utils.py
* chunyu/utils/general/date_time_utils.py
* cy_cache/base/utils/time_tools.py
* medweb_utils/util_funcs.py
* cy_common/utils/date_time.py
"""
import calendar
import datetime
import time

FORMAT_DATE_WITHOUT_SEPARATOR = '%Y%m%d'
FORMAT_DATETIME_WITHOUT_SEPARATOR = '%Y%m%d%H%M%S'
FORMAT_DATE = '%Y-%m-%d'
FORMAT_MONTH = '%Y-%m'
FORMAT_YEAR = '%Y'

FORMAT_DATETIME = '%Y-%m-%d %H:%M:%S'
FORMAT_DATETIME_MSEC = '%Y-%m-%d %H:%M:%S.%f'
FORMAT_HOUR_MIN = '%H:%M'

CHINA_FORMAT_DATE = u'%Y年%m月%d日'
CHINA_FORMAT_DATETIME = u'%Y年%m月%d日 %H:%M'
CHINA_FORMAT_DATETIME_WITHOUT_YEAR = u'%-m月%-d日 %H:%M'  # -表示去除前面的0

CURRENT_TIME_INFO = u'%s %s'
WEEK_LIST = [u'星期一', u'星期二', u'星期三', u'星期四', u'星期五', u'星期六', u'星期日']
SHORT_WEEK_LIST = [u'周一', u'周二', u'周三', u'周四', u'周五', u'周六', u'周日']
DEFAULT_DAYS_PER_MONTH = 30
MICROSECOND_MULTIPLE = 1000000  # 秒转换为微秒的倍数
MONTH_AVG_DAYS = 30.4   # 每个月的平均天数，365 / 12


############################################
# 字符串转时间
############################################


def str_to_datetime(date_str, date_format=FORMAT_DATE, process_none=False):
    """
    convert date string ('2011-01-12') into {@see datetime}
    """
    if process_none and not date_str:
        return None
    date = datetime.datetime.strptime(date_str, date_format)
    return date


def str_to_date(date_str, date_format=FORMAT_DATE, process_none=False):
    """
    convert date string ('2011-01-12') into {@see date}
    """
    dt = str_to_datetime(date_str, date_format, process_none)
    if dt is None:
        return None
    return dt.date()


def datetime_str_to_date(datetime_str, datetime_format=FORMAT_DATETIME):
    """
    给定时间字符串，返回日期
    """
    return datetime.datetime.strptime(datetime_str, datetime_format).date()


def convert_to_datetime(value, default_value=None):
    """
    '2015-10-01 1:1:1' -> datetime
    兼容 '2015-10-01' 格式
    """
    if isinstance(value, str):
        try:
            if u':' in value:
                value = str_to_datetime(value, FORMAT_DATETIME)
            else:
                value = str_to_datetime(value, FORMAT_DATE)
        except ValueError:
            value = default_value
    return value


def convert_to_date(value, default_value=None):
    """
    '2015-10-01' -> date
    """
    if isinstance(value, str):
        try:
            value = str_to_date(value, FORMAT_DATE)
        except ValueError:
            value = default_value
    return value


def convert_time(total_time):
    """
    秒转为HH:MM:SS
    """
    h = int(total_time / 3600)
    sup_h = total_time - 3600 * h
    m = int(sup_h / 60)
    sup_m = sup_h - 60 * m
    s = int(sup_m)
    return u"%s小时%s分%s秒" % (h, m, s)


def show_age_by_birthday(birthday):
    """
    根据生日返回显示的年龄
    """
    if not birthday:
        return ''
    if isinstance(birthday, str):
        birthday = convert_to_datetime(birthday)
    elif isinstance(birthday, datetime.date):
        birthday = datetime.datetime(birthday.year, birthday.month, birthday.day)
    now = datetime.datetime.now()
    diff = now - birthday
    if diff.days > 730:  # 2岁以上显示年龄xx岁
        return str(diff.days / 365) + u'岁'
    elif diff.days > 30:  # 一个月显示xx个月
        return str(diff.days / 30) + u'个月'
    elif diff.days > 1:  # 一天以上显示xx天
        return str(diff.days) + u'天'
    else:
        return u'1天'


############################################
# 时间转字符串
############################################


def datetime_to_str(date, date_format=FORMAT_DATE, process_none=False):
    """
    convert {@see datetime} into date string ('2011-01-12')
    """
    if process_none and date is None:
        return ''
    return date.strftime(date_format)


def date_to_str(date, date_format=FORMAT_DATE, process_none=False):
    """
    convert {@see date} into date string ('2011-01-12')
    """
    return datetime_to_str(date, date_format, process_none)


def date_to_str_china(date, date_format=CHINA_FORMAT_DATE, with_weekday=False):
    """
    convert {@see date} into date string ('2011年1月12日') ,with '星期X' when with_weekday is True
    """
    date_str = date.strftime(date_format.encode('utf-8')).decode('utf-8')
    if with_weekday:
        date_str = CURRENT_TIME_INFO % (date_str, WEEK_LIST[date.weekday()])

    return date_str


def earlier_date_to_str(date):
    """
    将日期转换成字符串
    在strftime不能处理时使用，可以处理早于1900年的日期
    RET: 1890-10-20
    """
    # earlier_datetime_to_str返回的时间形如：1890-10-20 12:00:00
    return earlier_datetime_to_str(date_to_datetime(date)).split(' ')[0]


def earlier_datetime_to_str(date_time):
    """
    将日期时间转换成字符串
    在strftime不能处理时使用，可以处理早于1900年的日期
    RET: 1890-10-20 12:00:00
    """
    return date_time.isoformat(' ').split('.')[0]


def get_chinese_noon_str(dt):
    """
    :param dt: datetime
    :return: 上午 or 下午
    """
    return u'上午' if 0 <= dt.hour < 12 else u'下午'


def build_datetime_detail_str(dt):
    """
    :param dt:_datetime:
    :return: 2015-08-21 周一上午 9:30
    """
    return '%s %s%s %s:%02d' % (datetime_to_str(dt), SHORT_WEEK_LIST[dt.weekday()], get_chinese_noon_str(dt),
                                12 if dt.hour == 12 else dt.hour % 12, dt.minute)


def convert_minutes_to_string(minutes):
    """
    将分钟数转换成一个字符串，如给190，则返回'3小时10分'; 给1443， 返回'1天3分'
    """
    day_minutes, hour_minutes = 24 * 60, 60
    day = minutes / day_minutes
    minutes -= (day_minutes * day)
    hour = minutes / hour_minutes
    minutes -= (hour_minutes * hour)
    result = u''
    if day:
        result += str(day) + u'天'
    if hour:
        result += str(hour) + u'小时'
    if minutes:
        result += str(minutes) + u'分'
    return result


def time_format(t, just_now_range=60, need_year=False):
    now = datetime.datetime.today()
    delta = now - t
    seconds = total_seconds(delta)
    if seconds < just_now_range:
        result = u"刚刚"
    elif seconds < 30 * 60:
        result = str(int(seconds / 60)) + u"分钟前"
    elif seconds < 60 * 60:
        result = u"半小时前"
    elif seconds < 24 * 60 * 60:
        result = str(int(seconds / 3600)) + u"小时前"
    else:
        result = t.strftime(u"%Y年%-m月%-d日") if t.year != now.year and need_year else t.strftime(u"%-m月%-d日")
    return result


def get_hour_minutes(t):
    result = t.strftime("%H:%M")
    return result


def get_day(t):
    result = t.strftime("%Y/%m/%d")
    return result


def build_weekday_str():
    """
    返回当天日期，星期几
    e.g. 2013-01-01 星期一
    """
    today = datetime.datetime.today()
    time_info_string = CURRENT_TIME_INFO % (datetime_to_str(today), WEEK_LIST[today.weekday()])
    return time_info_string


def convert_to_datetime_str(value):
    """
    datetime(2015-10-1 10:00:00) -> "2015-10-1 10:00:00"
    "2015-10-1" -> "2015-10-1 10:00:00"
    "2015-10-1 00:00:00" -> "2015-10-1 10:00:00"
    """
    if isinstance(value, datetime.datetime) or isinstance(value, datetime.date):
        value = datetime_to_str(value, FORMAT_DATETIME)
    elif isinstance(value, str):
        try:
            convert_datetime = str_to_datetime(value, FORMAT_DATETIME)
        except ValueError:
            convert_datetime = str_to_datetime(value, FORMAT_DATE)
        value = datetime_to_str(convert_datetime, FORMAT_DATETIME)
    return value


############################################
# 时间戳处理
############################################


def generate_timestamp():
    """
    Get seconds since epoch (UTC).
    """
    return int(time.time())


def convert_datetime_to_timestamp(convert_time):
    return time.mktime(convert_time.timetuple())


def convert_datetime_to_timestamp_ms(convert_time):
    result = 1000 * time.mktime(convert_time.timetuple())
    if isinstance(convert_time, datetime.datetime):
        result += convert_time.microsecond / 1000
    return result


def datetime_to_timestamp(time_):
    """
    datetime类型转换为unix时间戳*1000
    """
    timestamp = time.mktime(time_.timetuple())
    return int(timestamp * 1000)


def datetime_str_to_timestamp(time_str):
    """
    字符串时间类型转换为unix时间戳*1000
    """
    time_ = str_to_datetime(time_str, FORMAT_DATETIME)
    return datetime_to_timestamp(time_)


def created_time_ms(created_time):
    return 1000 * time.mktime(created_time.timetuple())


def timestamp_to_datetime(seconds):
    """
    将POSIX time (Unix timestamp)转换为datetime
    :param seconds: 从Epoch（1970年1月1日 00:00:00 UTC）开始所经过的秒数
    """
    return datetime.datetime.fromtimestamp(seconds)


def get_timestamp_from_time(time_):
    """
    把各种时间串变成 时间戳
    :param time_:
    :return: time stamp
    """
    if isinstance(time_, str):
        time_obj = str_to_datetime(time_, FORMAT_DATETIME)
    elif isinstance(time_, datetime.datetime):
        time_obj = time_
    else:
        time_obj = datetime.datetime.now()
    return convert_datetime_to_timestamp(time_obj)


def unix_time_2_datetime(now):
    """
    从 unix_time的seconds到datetime的转换
    :param now:表示unix时间(秒)
    :return:
    """
    return datetime.datetime.fromtimestamp(now)


def datetime_2_unix_time(dt):
    """
    从 datetime到 seconds的转换, 会丢失精度
    :param dt:(datetime)
    :return:
    """
    return int(time.mktime(dt.timetuple()))


def unix_time_2_date(now):
    return datetime.date.fromtimestamp(now)


############################################
# 微秒时间处理
############################################


def get_current_timestamp_microsecond():
    return int(time.time() * MICROSECOND_MULTIPLE)


def convert_timestamp_microsecond_to_datetime(timestamp_microsecond):
    return timestamp_to_datetime(float(timestamp_microsecond) / MICROSECOND_MULTIPLE)


def convert_datetime_to_timestamp_microsecond(dt):
    return MICROSECOND_MULTIPLE * time.mktime(dt.timetuple()) + dt.microsecond


############################################
# 用差值计算时间
############################################


def get_today():
    """
    RET: like 2014-07-14 00:00:00
    """
    today = datetime.datetime.now()
    return today.replace(hour=0, minute=0, second=0, microsecond=0)


def get_yesterday_and_today():
    today = get_today()
    yesterday = today - datetime.timedelta(days=1)
    return yesterday, today


def relative_date(date_str, days):
    """
    get relative date string: ('2011-01-12', -2) -> '2011-01-10'
    """
    date = time.strptime(date_str, FORMAT_DATE)
    date = datetime.datetime(*date[:6])
    #    print date
    new_date = date + datetime.timedelta(days=days)
    #    print new_date, new_date.strftime(FORMAT_DATE)
    return new_date.strftime(FORMAT_DATE)


def get_datetime_by_day_delta(days=0, today=None):
    if not today:
        today = datetime.datetime.today()

    dest_time = today + datetime.timedelta(days=days)

    if not isinstance(dest_time, datetime.datetime):
        dest_time = date_to_datetime(dest_time)
    return dest_time


def ordinal_2_date(ordinal):
    """
    由在日历里的日期序号反推日期
    """
    return datetime.date.fromordinal(ordinal)


def get_yesterday():
    return get_today() - datetime.timedelta(days=1)


def get_recent_weeks(week_num):
    """
    week_num为0时返回当前周
    :return: [(week_start_time_1, week_end_time_1), ...]
    """
    week_ranges = []
    start_time, end_time = get_current_week_range(datetime.datetime.today())
    week_ranges.append((start_time, end_time))
    for _ in range(week_num):
        start_time, end_time = get_previous_week_range(start_time)
        week_ranges.append((start_time, end_time))
    return week_ranges


def get_week_start_day(cal_date=None, return_datetime=True):
    """
    RET: 周一的日期(return datetime if return_datetime==True)
    """
    cal_date = cal_date or datetime.date.today()
    cal_datetime = datetime.datetime(cal_date.year, cal_date.month, cal_date.day)

    week_day = cal_datetime.weekday()
    start_datetime = cal_datetime - datetime.timedelta(days=week_day) if week_day else cal_datetime
    return start_datetime if return_datetime else start_datetime.date()


def get_current_week_range(cal_date=None, is_datetime=True):
    """
    RET: 周一的日期， 周日的日期 (return datetime if is_datetime==True)
    """
    start_day = get_week_start_day(cal_date, is_datetime)
    return start_day, start_day + datetime.timedelta(days=7)


def get_current_month(now=None):
    """
    得到当天月的第一天
    """
    if not now:
        now = datetime.datetime.today()
    return datetime.datetime(now.year, now.month, 1)


def get_last_month(now=None):
    """
    得到上个月的第一天
    """
    current_month = get_current_month(now)
    last_day = current_month - datetime.timedelta(days=1)
    return get_current_month(last_day)


def get_next_month(now=None, day=1):
    """
    得到下个月的某一天, day表示几号, 例如day=5表示下个月5号
    """
    if not now:
        now = datetime.datetime.today()
    start_time = datetime.datetime(now.year, now.month, day)
    range_days = calendar.monthrange(start_time.year, start_time.month)[1]
    return start_time + datetime.timedelta(days=range_days)


def get_previous_month_range(today=None):
    if not today:
        today = datetime.datetime.today()
    current_time = datetime.datetime(today.year, today.month, today.day)
    end_time = current_time - datetime.timedelta(days=current_time.day)
    start_time = end_time.replace(day=1)
    end_time = end_time + datetime.timedelta(days=1)
    return start_time, end_time


def get_month_range(today=None):
    """
    根据时间计算月份范围，采用前闭后开原则，最后一天则为下个月的第一天
    """
    if not today:
        today = datetime.datetime.today()
    current_time = datetime.datetime(today.year, today.month, today.day)
    current_year = current_time.year
    compute_month = current_time.month
    range_days = calendar.monthrange(current_year, compute_month)[1]
    start_time = current_time.replace(day=1)
    end_time = start_time + datetime.timedelta(days=range_days)
    return start_time, end_time


def get_born_time_by_age(age):
    """
    根据年龄默认出生日期
    默认出生日期为今年减去年龄的一月一日
    """
    now = datetime.datetime.now()
    return datetime.datetime(year=now.year - age, month=1, day=1)


def get_age_from_born_time(str_born_time, datetime_format=FORMAT_DATE):
    """
    根据字符串类型的出生日期得到年龄
    """
    if isinstance(str_born_time, str):
        born_date = datetime_str_to_date(str_born_time, datetime_format=datetime_format)
    else:
        born_date = str_born_time
    return datetime.datetime.today().year - born_date.year


def days_from_time(begin_time):
    """
    返回从begin_time到现在一共是多少天
    """
    return (datetime.datetime.now().date() - begin_time.date()).days


def get_birthday_from_age(age_type, age_value, return_str=False):
    """
    根据年龄获取生日(如果是月，都简单以30天为一月，保证和calculate_time_diff_months逻辑的一致性)
    :param: age_type: m 按月获取; y 按年获取
    :param: age_value:
    :param: return_str:
    RET:
        date if not format
        date_to_str(date, format) if format
    """
    today_date = datetime.date.today()
    # 如果是月，都简单以30天为一月，保证和calculate_time_diff_months逻辑的一致性
    if age_type == 'm':
        birthday = today_date - datetime.timedelta(days=DEFAULT_DAYS_PER_MONTH * age_value)
    else:
        birthday = today_date.replace(year=today_date.year - age_value)

    return earlier_date_to_str(birthday) if return_str else birthday


def get_month_age_by_age_days(age_days):
    """
    由出生的天数计算月龄
    :param age_days: 出生的天数，一般是：calculate_time_diff_days(born_time, created_time)
    :return: month_age
    """
    return int(round(age_days / MONTH_AVG_DAYS, 0)) if age_days > 0 else 0


def get_start_end_time(is_this_month):
    """
    根据是否是统计本月情况来返回开始时间和结束时间
    参数：is_this_month：是否计算本月的详细信息
    """
    if is_this_month:  # 统计本月，从1号开始统计
        end_date = datetime.datetime.today()
        start_date = datetime.datetime(end_date.year, end_date.month, 1)
    else:  # 统计上月
        date = datetime.datetime.today()
        end_date = datetime.datetime(date.year, date.month, 1)
        start_date = end_date - datetime.timedelta(days=15)
        start_date = datetime.datetime(start_date.year, start_date.month, 1)
    return start_date, end_date


def get_start_end_time_for_current_time(current_time):
    """
    获取当前时间所在天的时间间隔
    """
    start_time = datetime.datetime(current_time.year, current_time.month, current_time.day)
    end_time = start_time + datetime.timedelta(days=1)
    return start_time, end_time


def time_range_chunks(start_time, end_time, dt_timedelta=datetime.timedelta(days=1), reverse=False):
    """
    获取时间范围分段
    :param start_time:
    :param end_time:
    :param dt_timedelta: datetime.timedelta  默认一天
    :param reverse:
    :return: [(start_time_1, end_time_1), ...]
    """
    assert start_time < end_time, u'开始时间必须小于结束时间'
    # 如果dt_timedelta不是整天，而start_time/end_time是date类型，那么会出现dt_timedelta被取为整天数的问题
    # 如果小于1天，那么在date类型上的加操作不会改变原值，下面的while循环会无法跳出
    # 所以只要不是整天数或者days>0，都强转为datetime类型
    if dt_timedelta.days == 0 or dt_timedelta.seconds > 0 or dt_timedelta.microseconds > 0:
        if not isinstance(start_time, datetime.datetime):
            start_time = date_to_datetime(start_time)
        if not isinstance(end_time, datetime.datetime):
            end_time = date_to_datetime(end_time)
    result = []
    while start_time < end_time:
        current_end_time = min(start_time + dt_timedelta, end_time)
        result.append((start_time, current_end_time))
        start_time = current_end_time
    if reverse:
        result.reverse()

    return result


############################################
# 计算时间差值
############################################


def is_today(time_):
    """
    判断给定的时间是否是今天
    :param time_, 可能是unix timestamp，或者是datetime.date，或者是datetime.datetime
    :return: True/False
    """
    today_date = datetime.date.today()

    if isinstance(time_, (int, float)):
        time_ = timestamp_to_datetime(time_).date()

    if isinstance(time_, datetime.datetime):
        time_ = time_.date()

    return time_ == today_date


def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6


def timedelta_to_hour(delta):
    seconds = int(round(delta.total_seconds()))
    hour = seconds / 3600
    minute = (seconds % 3600) / 60
    second = (seconds % 3600) % 60
    return hour, minute, second


def get_previous_week_range(today=None):
    if not today:
        today = datetime.datetime.today()
    today = datetime.datetime(today.year, today.month, today.day)
    end_date = today - datetime.timedelta(days=today.weekday())
    start_date = end_date - datetime.timedelta(days=7)
    return start_date, end_date


def calculate_time_diff_seconds(end_time, start_time):
    """
    计算两个时间差的秒数（向下取整）
    """
    return int((end_time - start_time).total_seconds())


def calculate_time_diff_minutes(end_time, start_time, up_round=False):
    """
    计算两个时间差的分钟数，up_round=True表示向上取整
    """
    add_seconds = 59 if up_round else 0
    return (int((end_time - start_time).total_seconds()) + add_seconds) / 60


def calculate_time_diff_hours(end_time, start_time):
    """
    计算两个时间差的小时数（向下取整）
    """
    return int((end_time - start_time).total_seconds()) / (60 * 60)


def calculate_time_diff_days(end_time, start_time):
    """
    计算两个时间差的天数（向下取整）
    """
    return int((end_time - start_time).total_seconds()) / (60 * 60 * 24)


def calculate_time_diff_months(end_time, start_time):
    """
    计算两个时间差的月数（向下取整）
    各月天数不一，这里简单的将相差的天数除以30
    """
    return calculate_time_diff_days(end_time, start_time) / DEFAULT_DAYS_PER_MONTH


def calculate_time_diff_years(end_time, start_time):
    """
    计算两个时间差的年数（向下取整）
    同月同日表示整年数（如果是闰月，多的那一天不算入）
    """
    year_diff = end_time.year - start_time.year
    month_diff = end_time.month - start_time.month
    if month_diff > 0:
        return year_diff
    if month_diff < 0:
        return year_diff - 1
    # 月份相等，比较日期(闰2月的29日不算进来)
    start_day = 28 if start_time.month == 2 and start_time.day == 29 else start_time.day
    day_diff = end_time.day - start_day
    return year_diff if day_diff >= 0 else year_diff - 1


def calculate_month_delta_days(calculate_date=None):
    """
    计算某个时间到月底之间的间隔天数
    """
    calculate_date = calculate_date if calculate_date else datetime.date.today()
    return calendar.monthrange(calculate_date.year, calculate_date.month)[1] - calculate_date.day + 1


def exceed_time_limit(new_created_time, old_created_time):
    """
    计算两个时间的时间差，如果时间差超过24小时或者隔天超过8小时则返回True。
    """
    time_delta = (new_created_time - old_created_time).total_seconds() / (60 * 60)
    if time_delta >= 24:
        return True
    # 提问时间间隔隔天，且超过八小时
    if new_created_time.day != old_created_time.day and time_delta >= 8:
        return True
    return False


def date_2_ordinal(dt):
    """
    返回 dt 在日历里的日期序号， 0001-01-01 是 1
    datetime.datetime(1, 1, 2).toordinal() -> 2
    """
    return dt.toordinal()


############################################
# 通用函数
############################################


def date_to_datetime(date):
    """
    convert {@see date} into datetime
    """
    return datetime.datetime(date.year, date.month, date.day)


def get_midnight_datetime(_datetime):
    """
    获取午夜值
    RET: like 2018-07-14 00:00:00
    """
    return _datetime.replace(hour=0, minute=0, second=0, microsecond=0)


def convert_datime_to_timestamp(convert_time):
    return time.mktime(convert_time.timetuple())
