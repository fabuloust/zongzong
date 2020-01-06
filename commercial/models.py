from django.db import models
from django.db.models import ForeignKey

from user_info.models import UserBaseInfo


class Club(models.Model):
    # 俱乐部名称
    def __unicode__(self):
        return '{name}_{id}'.format(name=self.name, id=self.id)

    name = models.CharField(max_length=40, verbose_name='俱乐部名称')
    fans_num = models.PositiveIntegerField(default=0, verbose_name='粉丝数量')
    address = models.CharField(max_length=100, verbose_name='俱乐部名称')
    avatar = models.CharField(max_length=100, verbose_name='头像')
    telephone = models.CharField(max_length=15, verbose_name='头像')
    lat = models.FloatField(verbose_name='维度')
    lon = models.FloatField(verbose_name='经度')
    created_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class CommercialActivity(models.Model):
    # 商业活动
    def __unicode__(self):
        return '{name}_{start_time}'.format(name=self.name, start_time=self.time_detail)
    club = ForeignKey(Club, on_delete=models.CASCADE)
    name = models.CharField(max_length=40, verbose_name='活动名称')
    address = models.CharField(max_length=100, verbose_name='活动地址')
    lat = models.FloatField(verbose_name='维度')
    lon = models.FloatField(verbose_name='经度')
    time_detail = models.CharField(max_length=100, verbose_name='活动时间')
    introduction = models.CharField(max_length=200, verbose_name='内容简介')
    description = models.CharField(max_length=100, verbose_name='活动说明')
    detail = models.TextField(verbose_name='详细描述')
    total_quota = models.IntegerField(default=0, verbose_name='总名额')
    participant_num = models.IntegerField(default=0, verbose_name='报名名额')
    top_image = models.CharField(max_length=200, verbose_name='顶部')
    image_list = models.TextField(verbose_name='图片列表')

    created_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class ActivityParticipant(models.Model):
    # 活动参加者
    def __unicode__(self):
        return '{}__{}'.format(self.activity.name, self.user_info.nickname)
    activity = ForeignKey(CommercialActivity, on_delete=models.CASCADE, help_text='活动')
    user_info = ForeignKey(UserBaseInfo, on_delete=models.CASCADE, verbose_name='用户信息')


class TopBanner(models.Model):
    """
    顶部banner
    """
    def __unicode__(self):
        return '{}'.format(self.title)
    title = models.CharField(max_length=40, verbose_name='标题')
    image = models.CharField(max_length=40, verbose_name='图片')
    activity_id = models.PositiveIntegerField(verbose_name='活动id')
    is_online = models.BooleanField(default=False, verbose_name='是否上线')
    created_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
