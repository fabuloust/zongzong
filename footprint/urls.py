from django.urls import path

import footprint.views


urlpatterns = [
    # 痕迹相关
    path('create/', footprint.views.post_footprint_view),

    path('favor/', footprint.views.add_favor_view),
    # path('footprint/forward', footprint.views),


]