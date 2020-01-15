from django.urls import path

from footprint.views import post_footprint_view, comment_footprint_view, get_footprint_detail_view, \
    get_user_footprint_track_view

urlpatterns = [
    # 痕迹相关
    path('create/', post_footprint_view),
    path('comment/', comment_footprint_view),
    path('detail/', get_footprint_detail_view),
    path('get_user_track/', get_user_footprint_track_view),
]
