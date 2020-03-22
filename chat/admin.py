

from django.contrib import admin
from reversion.admin import VersionAdmin

from chat.models import ChatRecord


@admin.register(ChatRecord)
class UserBaseInfoAdmin(VersionAdmin):

    list_display = ['content', 'is_delete']
