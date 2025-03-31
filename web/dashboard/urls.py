from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = [
    re_path(r'^board/$', views.BoardView.as_view()),
    re_path(r'^plannames/$', views.plan_name_list),
    re_path(r'^users/$', views.user_name_list),
    re_path(r'^groupnames/$', views.group_name_list),
    re_path(r'^login/$', views.login),
    re_path(r'^syncftest/$', views.sync_ftest),
    # re_path(r'^plan/(?P<pk>[0-9]+)$', views.PlanView.as_view()),
    # re_path(r'^plan/$', views.PlanView.as_view()),
]


router = DefaultRouter()
router.register(r'plan', viewset=views.PlanViewSet)
router.register(r'planrecord', viewset=views.PlanRecordViewSet)
router.register(r'caserecord', viewset=views.CaseRecordViewSet)
router.register(r'user', viewset=views.OaUserViewSet)
router.register(r'problem', viewset=views.ProblemViewSet)
# router.register(r'board', viewset=views.BoardView)
urlpatterns += router.urls
