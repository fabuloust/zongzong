from django.contrib.auth.decorators import login_required


@login_required
def my_homepage_view(request):
    """
    我的主页
    """
    user = request.user
    