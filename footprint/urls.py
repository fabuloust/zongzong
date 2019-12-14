from django.urls import path

import footprint.views


urlpatterns = [
    # 痕迹相关
    path('footprint/create/', footprint.views.post_footprint_view),

    path('footprint/favor/', footprint.views.add_favor_view),
    path('footprint/forward', footprint.views),


]