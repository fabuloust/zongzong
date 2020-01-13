from django.urls import path

from user_info.views import set_my_profile_view, get_my_profile_view, get_user_brief_profile_view

urlpatterns = [
    path('my_profile/', get_my_profile_view),
    path('my_profile/edit/', set_my_profile_view),
    path('get_user_info/', get_user_brief_profile_view),
]
