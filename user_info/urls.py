from django.urls import path

from user_info.views import set_my_profile_view

urlpatterns = [
    # path('get_user_info/', my_profile_views.get_my_profile_viewile_view),
    path('my_profile/edit/', set_my_profile_view),
]