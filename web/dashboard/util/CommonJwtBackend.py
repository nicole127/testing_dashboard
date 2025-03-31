from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

"""自定义认证后台
默认根据username 和password 登录合法性
"""
class CommonJwtBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = User.objects.get(Q(username=username))
        if user.check_password(password):
            return user
        return None
