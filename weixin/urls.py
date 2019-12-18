from django.urls import path

import weixin.views

urlpatterns = [
    # 痕迹相关
    path('get_session_id/', weixin.views.login_and_get_session_id_view),

]
