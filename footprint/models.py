import json

from django.contrib.auth.models import User
from django.db import models

from footprint.consts import CommentStatusChoices
from user_info.consts import SexChoices


class Footprint(models.Model):
    """
    姓名 性别  年龄  标签  时间 地点  距离
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, verbose_name=u'姓名')
    image = models.CharField(max_length=100, verbose_name=u'头像')
    sex = models.CharField(choices=SexChoices, verbose_name=u'性别', max_length=10)
    # tag = models.CharField(max_length=20, verbose_name=u'标签')
    lat = models.CharField(max_length=20, verbose_name=u'维度', null=True, blank=True)
    lon = models.CharField(max_length=20, verbose_name=u'经度', null=True, blank=True)
    place = models.CharField(max_length=50, verbose_name=u'地点')
    content = models.CharField(max_length=200, verbose_name=u'痕迹内容')
    image_list_str = models.TextField(verbose_name=u'图片列表json')
    favor_num = models.PositiveIntegerField(default=0, verbose_name=u'点赞数')
    comment_num = models.PositiveIntegerField(default=0, verbose_name=u'评论数')
    forward_num = models.PositiveIntegerField(default=0, verbose_name=u'转发数')
    hide = models.BooleanField(default=False, verbose_name=u'是否只有自己能看到')
    created_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    @property
    def image_list(self):
        return json.loads(self.image_list_str) if self.image_list_str else []

    @image_list.setter
    def image_list(self, image_list):
        self.image_list_str = json.dumps(image_list)


class FootprintComment(models.Model):
    """
    痕迹评论
    """
    footprint = models.ForeignKey(Footprint, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(verbose_name=u'评论内容')
    image_list = models.CharField(max_length=1000, default='[]', help_text=u'评论附带图片')

    status = models.CharField(max_length=1, choices=CommentStatusChoices, default=CommentStatusChoices.NORMAL)

    nick_name = models.CharField(max_length=50, default='', blank=True, null=True, help_text='评论者昵称')
    portrait = models.CharField(max_length=255, default='', blank=True, null=True, help_text='评论者头像')
    distance = models.IntegerField(default=0, verbose_name=u'距离话题主多远，创建的时候根据定位计算')

    reference_comment = models.ForeignKey("FootprintComment", null=True, blank=True, on_delete=models.SET_NULL)
    created_time = models.DateTimeField(auto_now_add=True, db_index=True)
    last_modified = models.DateTimeField(auto_now=True)


class FootprintFavor(models.Model):
    """
    痕迹点赞记录
    """
    footprint = models.ForeignKey(Footprint, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    favored = models.BooleanField(verbose_name=u'是否点赞', default=True)
    created_time = models.DateTimeField(auto_now_add=True, db_index=True)
    last_modified = models.DateTimeField(auto_now=True)


class FootprintCommentFavor(models.Model):
    """
    痕迹评论的点赞
    """
    footprint = models.IntegerField(verbose_name=u'话题id')
    footprint_comment_id = models.IntegerField(verbose_name='话题评论id')
    user_id = models.IntegerField(verbose_name=u'评论者user_id')
    favored = models.BooleanField(verbose_name=u'是否点赞', default=True)
    created_time = models.DateTimeField(auto_now_add=True, db_index=True)
    last_modified = models.DateTimeField(auto_now=True)

