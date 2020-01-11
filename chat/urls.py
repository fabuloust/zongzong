from django.urls import path

from commercial.views import get_club_info_view, activity_detail_view, \
    get_top_banner_view  # , participate_activity_view

urlpatterns = [
    path('conversation_list/', get_top_banner_view),
    path('post_content/', get_club_info_view),
    path('get_activity_detail/', activity_detail_view),
    # path('participate_activity/', participate_activity_view),

]
