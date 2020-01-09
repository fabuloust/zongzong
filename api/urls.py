from django.urls import path

import footprint.views
from api.view import get_nearby_activities_view, discovery_view
from api.views import footprint_views


urlpatterns = [
    # 附近活动
    path('get_nearby_activities/', get_nearby_activities_view),
    path('discovery/', discovery_view),
    # profile相关
    path('get_brief_introduction/', footprint_views.get_user_brief_profile_view),
]
