import logging

from django.http import JsonResponse
from rest_framework import status

from dashboard.models import OaUser
from dashboard.util import CommonRequestUtil

logger = logging.getLogger()


class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info("call start: %s %s %s", request.path, CommonRequestUtil.get_request_ip(request), CommonRequestUtil.get_request_data(request))
        if request.path == '/dashboard/login/' or request.path == '/dashboard/syncftest/':
            return self.get_response(request)

        try:
            token = request.headers['Authorization']
            if token:
                exist_user = OaUser.objects.get(password=token)
                if exist_user:
                    request.oauser = exist_user
                    return self.get_response(request)
        except:
            pass

        return JsonResponse(status=status.HTTP_401_UNAUTHORIZED, data={})




