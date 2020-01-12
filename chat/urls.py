from django.urls import path

from chat.views import get_my_conversation_list_view, post_content_view#, get_conversation_detail_view

urlpatterns = [
    path('conversation_list/', get_my_conversation_list_view),
    path('post_content/', post_content_view),
    # path('get_conversation_detail/', get_conversation_detail_view),
]
