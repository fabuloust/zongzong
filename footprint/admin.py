from django.contrib import admin
from reversion.admin import VersionAdmin

from footprint.models import Footprint, Comment


@admin.register(Footprint)
class FootprintAdmin(VersionAdmin):

    list_display = ['name', 'sex', 'content', 'hide']


@admin.register(Comment)
class CommentAdmin(VersionAdmin):
    list_display = ['name', 'comment', 'is_deleted']
