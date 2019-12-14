from django.contrib.auth.models import User
from django.db import models

from user_info.consts import SexChoices
from utilities.time_utils import get_age_by_birthday


class UserBaseInfo(models.Model):
    """
    用户基础信息
    """
    user = models.ForeignKey(User, on_delete=models.SET)
    image = models.CharField(max_length=100, verbose_name=u'头像，同微信头像')
    open_id = models.CharField(unique=True, max_length=30, verbose_name="微信app的用户Id", null=True)
    nickname = models.CharField(max_length=20, verbose_name=u'昵称')
    signature = models.CharField(max_length=100, verbose_name=u'个性签名', null=True)
    sex = models.CharField(choices=SexChoices, verbose_name=u'性别', max_length=10, default=SexChoices.MALE)
    birthday = models.DateField(default=0, verbose_name=u'出生日期', null=True)
    tags = models.CharField(max_length=100, verbose_name=u'标签配置', default='[]')
    current_tag = models.CharField(max_length=20, verbose_name=u'当前展示的标签')
    wechat_no = models.CharField(max_length=50, verbose_name=u'微信号', null=True)
    show_wechat_no = models.BooleanField(default=False, verbose_name=u'是否展示微信号')
    created_time = models.DateTimeField(auto_now_add=True, db_index=True)
    last_modified = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        return get_age_by_birthday(self.birthday)

