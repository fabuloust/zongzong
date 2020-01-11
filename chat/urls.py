from django.urls import path

from chat.views import get_my_conversation_list_view, post_content_view

urlpatterns = [
    path('conversation_list/', get_my_conversation_list_view),
    path('post_content/', post_content_view),
    # path('get_conversation_detail/', activity_detail_view),
    # path('participate_activity/', participate_activity_view),

]
