from django.urls import path

import footprint.views
from api.views import footprint_views, my_profile_views



urlpatterns = [
    path('user/tag_list/', my_profile_views.get_tag_list_view),
    path('user/set_tag_list/', my_profile_views.set_tag_list_view),
    path('user/profile/', my_profile_views.get_my_profile_view),
    path('user/set_profile/', my_profile_views.set_my_profile_view),

    path('user/set_profile/', my_profile_views.set_my_profile_view),
    path('user/brief_introduction/', footprint_views.get_user_brief_profile_view),

    # 痕迹先关
    path('footprint/create/', footprint.views.post_footprint_view),


    # 微信相关

]