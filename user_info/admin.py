from django.contrib import admin
from reversion.admin import VersionAdmin


@admin.register
class UserBaseInfoAdmin(VersionAdmin):

    list_display = ['sex', 'location', 'nickname', 'birthday']