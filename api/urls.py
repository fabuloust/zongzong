from django.urls import path

from api.view import get_nearby_activities_view, discovery_view, get_nearest_activity_view, get_upload_token

urlpatterns = [
    # 附近活动
    path('get_nearby_activities/', get_nearby_activities_view),
    path('discovery/', discovery_view),
    path('get_nearest_activity/', get_nearest_activity_view),
    path('get_upload_token/', get_upload_token),
]
