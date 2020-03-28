from django.contrib import admin
from reversion.admin import VersionAdmin

from commercial.models import Club, CommercialActivity, TopBanner


class ClubAdmin(VersionAdmin):
    list_display = ['id', 'name', 'address', 'telephone']
    search_fields = ['=id', 'name']


admin.site.register(Club, ClubAdmin)


class ActivityAdmin(VersionAdmin):
    list_display = ['club', 'name', 'address']


admin.site.register(CommercialActivity, ActivityAdmin)


class TopBannerAdmin(VersionAdmin):
    list_display = ['title']


admin.site.register(TopBanner, TopBannerAdmin)
