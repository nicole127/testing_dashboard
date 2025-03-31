import datetime
import calendar
import logging
import re

import requests
from django.forms import model_to_dict

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Avg, F, Count, Min, Value, CharField, BigIntegerField, IntegerField
from django.db.models.functions import Cast
from rest_framework.filters import OrderingFilter
from django.db.models.functions import Cast, Concat
from django.db.models.expressions import RawSQL

from dashboard import ftest_request
from dashboard.models import Plan, PlanRecord, CaseRecord, OaUser, Problem, Group
from dashboard.serializers import PlanSerializer, PlanRecordSerializer, CaseRecordSerializer, OaUserSerializer, ProblemSerializer
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view

logger = logging.getLogger()


def month_transfer(start_date, end_date):
    '''
    start_date/end_date: datetime
    return: [20231106, 20231107, 20231108]
    '''
    months = []
    while start_date < end_date:
        months.append(start_date.strftime("%Y%m"))
        # 计算下一个月的年份和月份
        if start_date.month == 12:
            next_month_year = start_date.year + 1
            next_month = 1
        else:
            next_month_year = start_date.year
            next_month = start_date.month + 1
        # 构造下一个月的日期对象
        start_date = datetime.datetime(next_month_year, next_month, 1)
    return months


def duration_transfer(duration):
    # 可能场景：1s、1min、1h、1h1s、1min1s、1h1min、1h1min1s
    hours = re.findall(r'(\d+)h', duration)
    minutes = re.findall(r'(\d+)min', duration)
    seconds = re.findall(r'(\d+)s', duration)
    hours = int(hours[0]) if len(hours) > 0 else 0
    minutes = int(minutes[0]) if len(minutes) > 0 else 0
    seconds = int(seconds[0]) if len(seconds) > 0 else 0
    duration = hours*3600+minutes*60+seconds
    return duration


def sync_plan(id):
    plan = ftest_request.get_plan_detail(id)
    try:
        exist_plan = Plan.objects.get(pk=id)
        serializer = PlanSerializer(data=plan, instance=exist_plan)
    except:
        serializer = PlanSerializer(data=plan)

    if serializer.is_valid():
        serializer.save()
    return plan


def sync_plan_records(plan_id):
    plan = Plan.objects.filter(pk=plan_id).first()
    if not plan:
        return None
    plan_records = ftest_request.get_plan_records(plan)
    disable_record_ids = [plan_record['id'] for plan_record in PlanRecord.objects.filter(is_disable=1).values('id')]
    PlanRecord.objects.filter(pk__in=[plan_record["id"] for plan_record in plan_records]).delete()
    for plan_record in plan_records:
        if plan_record['id'] in disable_record_ids:
            plan_record['is_disable'] = 1
    serializer = PlanRecordSerializer(data=plan_records, many=True)
    if serializer.is_valid():
        serializer.save()


def sync_case_records(plan_record_id):
    case_records = ftest_request.get_plan_record_detail(plan_record_id)['case_records']
    plan_record = PlanRecord.objects.filter(id=plan_record_id).first()
    is_disable = plan_record.is_disable if plan_record else 0
    exist_case_records = CaseRecord.objects.filter(plan_record_id=plan_record_id)
    for case_record in case_records:
        case_record['is_disable'] = is_disable
        # 已关联的bug_link保留不能清除
        exist_case_record = exist_case_records.filter(id=case_record['id']).first()
        if exist_case_record:
            case_record['bug_link'] = exist_case_record.bug_link
    CaseRecord.objects.filter(plan_record_id=plan_record_id).delete()
    serializer = CaseRecordSerializer(data=case_records, many=True)
    if serializer.is_valid():
        serializer.save()


def sync_problems(plan_record_id):
    plan_record = PlanRecord.objects.filter(id=plan_record_id).first()
    executor = plan_record.user if plan_record else ''
    is_disable = plan_record.is_disable if plan_record else 0
    sql_query = '''SELECT max(id) id, fail_type, fail_reason, plan_record_id, plan_id,
                          COUNT(id) as affect_case_qty,
                          GROUP_CONCAT(id SEPARATOR ';') AS case_record_ids,
                          COALESCE(NULLIF(GROUP_CONCAT(DISTINCT CASE WHEN bug_link = '' THEN NULL ELSE bug_link END SEPARATOR ';'),''), '') AS bug_links,
                          min(create_time) AS create_time_min
                   FROM case_record
                   where plan_record_id=%(plan_record_id)s and is_success=False
                   GROUP BY fail_type, fail_reason, plan_record_id, plan_id'''
    queryset = CaseRecord.objects.raw(sql_query, params={'plan_record_id': plan_record_id})
    if queryset:
        problems = []
        # 遍历查询集中的结果，将每个分组的数据存到problems
        for item in queryset:
            problem = {
                "fail_type": item.fail_type,
                "fail_reason": item.fail_reason,
                "plan_record_id": item.plan_record_id,
                "plan_id": item.plan_id,
                "affect_case_qty": item.affect_case_qty,
                "case_record_ids": item.case_record_ids,
                "bug_link": item.bug_links,
                "create_time": item.create_time_min,
                "person_in_charge": executor,
                "is_disable": is_disable
            }
            problems.append(problem)
        if problems:
            # 先清空plan_record_id对应的problem
            Problem.objects.filter(plan_record_id=plan_record_id).delete()
            # 将最新的problem存入数据库
            serializer = ProblemSerializer(data=problems, many=True)
            if serializer.is_valid():
                serializer.save()


class OaUserViewSet(viewsets.ModelViewSet):
    queryset = OaUser.objects.all()
    serializer_class = OaUserSerializer

    # def get_queryset(self):
    #     queryset = self.queryset
    #     # 将token信息 存在 password字段
    #     password = self.request.query_params.get('token')
    #     queryset = queryset.filter(password=password)
    #     return queryset

    def create(self, request, *args, **kwargs):
        username = request.data['username']
        password = request.data['token']
        user = {
            "username": username,
            "password": password
        }
        try:
            exist_user = OaUser.objects.get(username=username)
            serializer = OaUserSerializer(data=user, instance=exist_user, partial=True)
        except:
            serializer = OaUserSerializer(data=user)

        if serializer.is_valid():
            serializer.save()
        return Response(status=status.HTTP_200_OK, data=user)


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    # permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (OrderingFilter,)
    # filterset_fields = {
    #     'name': ['icontains'],
    #     'person_in_charge': ['exact'],
    #     'id': ['in'],
    # }
    ordering_fields = ('create_time', )

    def get_queryset(self):
        queryset = self.queryset
        group_id = self.request.query_params.get('group_id')
        id = self.request.query_params.get('id')
        name__in = self.request.query_params.get('name')
        person_in_charge = self.request.query_params.get('person_in_charge')
        if group_id:
            users = OaUser.objects.filter(group_id=group_id)
            usernames = [item.username for item in users]
            plan = Plan.objects.filter(person_in_charge__in=usernames)
            plan_ids = [item.id for item in plan]
            queryset = queryset.filter(id__in=plan_ids)
        if id:
            queryset = queryset.filter(id=id)
        if name__in:
            queryset = queryset.filter(name__in=name__in)
        if person_in_charge:
            queryset = queryset.filter(person_in_charge=person_in_charge)
        return queryset.order_by('-create_time')

    def create(self, request, *args, **kwargs):
        url = request.data["url"]
        id = url.split("/?id=")[-1]
        if not id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            exist_plan = Plan.objects.get(id=id)
            serializer = PlanSerializer(exist_plan).data
            return Response(status=status.HTTP_200_OK, data=serializer)
        except:
            sync_plan(id)
            sync_plan_records(id)
            plan_record_ids = PlanRecord.objects.filter(plan_id=id).values_list('id', flat=True)
            for plan_record_id in plan_record_ids:
                sync_case_records(plan_record_id)
                sync_problems(plan_record_id)
            # plan = ftest_request.get_plan_detail(id)
            # plan_serializer = PlanSerializer(data=plan)
            # if plan_serializer.is_valid():
            #     plan_serializer.save()
            #     plan_records = ftest_request.get_plan_records(Plan(**plan))
            #     plan_record_serializer = PlanRecordSerializer(data=plan_records, many=True)
            #     if plan_record_serializer.is_valid():
            #         plan_record_serializer.save()
            #     for plan_record in plan_records:
            #         sync_case_records(plan_record['id'])
            #         sync_problems(plan_record['id'])
            #         # ftest_response = ftest_request.get_plan_record_detail(plan_record['id'])
            #         # case_record_serializer = CaseRecordSerializer(data=ftest_response['case_records'], many=True)
            #         # if case_record_serializer.is_valid():
            #         #     case_record_serializer.save()
            return Response(status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        id = kwargs["pk"]
        try:
            exist_plan = Plan.objects.get(pk=id)
            plan = {'is_disable': 1}
            serializer = PlanSerializer(data=plan, instance=exist_plan, partial=True)
            if serializer.is_valid():
                serializer.save()
        except:
            pass
        return Response(status=status.HTTP_200_OK)


class PlanRecordViewSet(viewsets.ModelViewSet):
    queryset = PlanRecord.objects.all()
    serializer_class = PlanRecordSerializer
    filter_backends = (OrderingFilter,)
    # filterset_fields = {
    #     'plan_id': ['exact'],
    #     'person_in_charge': ['exact'],
    #     'user': ['exact'],
    #     'update_time': ['gte', 'lte'],
    #     'is_success': ['exact'],
    # }
    ordering_fields = ('create_time',)

    def create(self, request, *args, **kwargs):
        plan_id = request.data["plan_id"]
        sync_plan_records(plan_id)
        return Response(status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        id = kwargs["pk"]
        try:
            exist_plan_record = PlanRecord.objects.get(pk=id)
            plan_record = request.data
            print(plan_record)
            serializer = PlanRecordSerializer(data=plan_record, instance=exist_plan_record, partial=True)
            if serializer.is_valid():
                serializer.save()
                # 更新plan_record对应case_records
                case_records = CaseRecord.objects.filter(plan_record_id=id)
                if case_records:
                    case_records.update(is_disable=plan_record['is_disable'])
                # 更新plan_record对应发现的问题
                problems = Problem.objects.filter(plan_record_id=id)
                if problems:
                    problems.update(is_disable=plan_record['is_disable'])
        except:
            pass
        return Response(status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = self.queryset
        group_id = self.request.query_params.get('group_id')
        plan_id = self.request.query_params.get('plan_id')
        person_in_charge = self.request.query_params.get('person_in_charge')
        user = self.request.query_params.get('user')
        create_time__gte = self.request.query_params.get('create_time__gte')
        create_time__lte = self.request.query_params.get('create_time__lte')
        is_success = self.request.query_params.get('is_success')
        if group_id:
            users = OaUser.objects.filter(group_id=group_id)
            usernames = [item.username for item in users]
            plan = Plan.objects.filter(person_in_charge__in=usernames)
            plan_ids = [item.id for item in plan]
            queryset = queryset.filter(plan_id__in=plan_ids)
        if plan_id:
            queryset = queryset.filter(plan_id=plan_id)
        if person_in_charge:
            queryset = queryset.filter(person_in_charge=person_in_charge)
        if user:
            queryset = queryset.filter(user=user)
        if create_time__gte:
            create_time__gte = int(int(create_time__gte)/1000)
            queryset = queryset.filter(create_time__gte=create_time__gte)
        if create_time__lte:
            create_time__lte = int(int(create_time__lte)/1000)
            queryset = queryset.filter(create_time__lte=create_time__lte)
        if is_success:
            queryset = queryset.filter(is_success=is_success)
        return queryset.order_by('-create_time')


class CaseRecordViewSet(viewsets.ModelViewSet):
    queryset = CaseRecord.objects.all()
    serializer_class = CaseRecordSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    # filterset_fields = {
    #     'plan_record_id': ['exact'],
    #     'is_success': ['exact'],
    # }
    ordering_fields = ('create_time',)

    def get_queryset(self):
        queryset = self.queryset
        plan_record_id = self.request.query_params.get('plan_record_id')
        person_in_charge = self.request.query_params.get('person_in_charge')
        is_success = self.request.query_params.get('is_success')
        fail_type = self.request.query_params.get('fail_type')
        if plan_record_id:
            queryset = queryset.filter(plan_record_id=plan_record_id)
        if person_in_charge:
            queryset = queryset.filter(person_in_charge=person_in_charge)
        if is_success:
            queryset = queryset.filter(is_success=is_success)
        if fail_type:
            queryset = queryset.filter(fail_type=fail_type)
        return queryset

    def create(self, request, *args, **kwargs):
        plan_record_id = request.data["plan_record_id"]
        sync_case_records(plan_record_id)
        return Response(status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        # 更新失败原因
        case_record_ids = request.data["case_record_ids"]
        try:
            ftest_request.set_case_fail_reason(case_record_ids, request.data["fail_type"], request.data["fail_reason"])
        except:
            logger.info("set_case_fail_reason request ftest failed {}", request)
        try:
            case_records = CaseRecord.objects.filter(pk__in=case_record_ids.split(";"))
        except:
            logger.info("{} not find in dashbord_case_record", request)
            return None
        for case_record in case_records:
            exist_case_record = CaseRecord.objects.get(pk=case_record.id)
            case_record = {
                'fail_type': request.data["fail_type"],
                'fail_reason': request.data["fail_reason"]
            }
            serializer = CaseRecordSerializer(data=case_record, instance=exist_case_record, partial=True)
            if serializer.is_valid():
                serializer.save()

        return Response(status=status.HTTP_200_OK)


class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    # filterset_fields = {
    #     'plan_record_id': ['exact'],
    #     'fail_type': ['exact'],
    # }
    ordering_fields = ('create_time',)

    def get_queryset(self):
        queryset = self.queryset.filter(is_disable=0)
        group_id = self.request.query_params.get('group_id')
        plan_id = self.request.query_params.get('plan_id')
        person_in_charge = self.request.query_params.get('person_in_charge')
        fail_type = self.request.query_params.get('fail_type')
        fail_reason = self.request.query_params.get('fail_reason')
        create_time__gte = self.request.query_params.get('create_time__gte')
        create_time__lte = self.request.query_params.get('create_time__lte')
        if group_id:
            users = OaUser.objects.filter(group_id=group_id)
            usernames = [item.username for item in users]
            plan = Plan.objects.filter(person_in_charge__in=usernames)
            plan_ids = [item.id for item in plan]
            queryset = queryset.filter(plan_id__in=plan_ids)
        if plan_id:
            queryset = queryset.filter(plan_id=plan_id)
        if person_in_charge:
            queryset = queryset.filter(person_in_charge=person_in_charge)
        if create_time__gte:
            create_time__gte = int(int(create_time__gte)/1000)
            queryset = queryset.filter(create_time__gte=create_time__gte)
        if create_time__lte:
            create_time__lte = int(int(create_time__lte)/1000)
            queryset = queryset.filter(create_time__lte=create_time__lte)
        if fail_type:
            queryset = queryset.filter(fail_type=fail_type)
        if fail_reason:
            queryset = queryset.filter(fail_reason__contains=fail_reason)
        return queryset.order_by('-create_time')

    def create(self, request, *args, **kwargs):
        plan_record_id = request.data["plan_record_id"]
        sync_problems(plan_record_id)
        return Response(status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """
            关联缺陷单，将problem对应的caseRecord的bug_link也更新
        """
        id = kwargs["pk"]
        try:
            exist_problem = Problem.objects.get(pk=id)
            problem = request.data
            Problem.objects.filter(id=id).update(bug_link=problem["bug_link"])
            case_record_ids = exist_problem.case_record_ids.split(';')
            CaseRecord.objects.filter(id__in=case_record_ids).update(bug_link=problem["bug_link"])
        except Exception as e:
            logger.info("更新/关联飞书缺陷单失败, 问题 {} 不存在", id, **kwargs)
            pass
        return Response(status=status.HTTP_200_OK)


class BoardView(APIView):

    def get(self, request, *args, **kwargs):
        # 前端传的字段：group_ids[]、plan_ids[]=1&plan_ids[]=2、start_time、end_rime=时间戳
        group_ids = self.request.GET.getlist('group_ids[]')
        plan_ids = self.request.GET.getlist('plan_ids[]')
        create_time__gte = self.request.query_params.get('create_time__gte')
        create_time__lte = self.request.query_params.get('create_time__lte')
        user = request.oauser.username
        # 必须传时间范围
        if not create_time__gte or not create_time__lte:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        create_time__gte = int(int(create_time__gte) / 1000)
        create_time__lte = int(int(create_time__lte) / 1000)
        start_date = datetime.datetime.fromtimestamp(create_time__gte)
        end_date = datetime.datetime.fromtimestamp(create_time__lte)
        months = month_transfer(start_date, end_date)
        response_data = {
            "summary": {
                "total_bug_quantity": 0,
                "total_code_bug_quantity": 0,
                "total_case_pass_percent": 0,
                "total_plan_execution_count": 0,
                "total_case_records_count": 0,
                "total_plan_records_duration": 0
            },
            "x_data": [str(int(month) % 100)+'月' for month in months],
            "y_data": []
        }

        # 前端传了group_ids表示按照小组维度展示
        if group_ids:
            # 汇总数据
            # 1. 筛选当前group_id下的用户
            users = OaUser.objects.filter(group_id__in=group_ids)
            # 如查不到执行记录，直接返回空
            if not users:
                return Response(status=status.HTTP_200_OK, data=response_data)
            usernames = [user.username for user in users]
            # 2. 根据用户即负责人筛选plan_id
            plans = Plan.objects.filter(person_in_charge__in=usernames)
            if not plans:
                return Response(status=status.HTTP_200_OK, data=response_data)
            plan_ids = [plan.id for plan in plans]
            # 3. 根据plan_id查到执行记录plan_record
            plan_records = PlanRecord.objects.filter(plan_id__in=plan_ids, create_time__gte=create_time__gte, create_time__lte=create_time__lte, is_disable=0)
            if not plan_records:
                return Response(status=status.HTTP_200_OK, data=response_data)
            problems = Problem.objects.filter(plan_id__in=plan_ids, create_time__gte=create_time__gte, create_time__lte=create_time__lte, is_disable=0)
            response_data['summary']['total_bug_quantity'] = problems.count()
            response_data['summary']['total_code_bug_quantity'] = problems.filter(fail_type=1).count()
            response_data['summary']['total_plan_execution_count'] = plan_records.filter(is_rerun=0).count()
            response_data['summary']['total_case_records_count'] = plan_records.aggregate(total_count=Sum('total_count'))['total_count']
            response_data['summary']['total_case_pass_percent'] = round(plan_records.aggregate(success_count=Sum('success_count'))['success_count'] / response_data['summary']['total_case_records_count'] * 100) if response_data['summary']['total_case_records_count'] else 0
            response_data['summary']['total_plan_records_duration'] = sum(duration_transfer(plan_record.duration) for plan_record in plan_records)
            # 转成分钟返回给前端，不足1分钟算作1分钟
            response_data['summary']['total_plan_records_duration'] = max(response_data['summary']['total_plan_records_duration'] // 60, 1) if response_data['summary']['total_plan_records_duration'] else 0

            for group_id in group_ids:
                group = Group.objects.filter(id=group_id).first()
                if group:
                    group_name = group.group_name
                else:
                    group_name = ''
                group_users = users.filter(group_id=group_id)
                group_usernames = [user.username for user in group_users]
                group_plans = plans.filter(person_in_charge__in=group_usernames)
                group_plan_ids = [plan.id for plan in group_plans]
                y_data = {
                    "id": int(group_id),
                    "name": group_name,
                    "bug_quantity": [],
                    "code_bug_quantity": [],
                    "environment_bug_quantity": [],
                    "case_bug_quantity": [],
                    "platform_bug_quantity": [],
                    "default_bug_quantity": [],
                    "plan_records_duration": [],
                    "plan_execution_count": [],
                    "case_records_count": [],
                    "case_pass_percent": []

                }
                for i in range(len(months)):
                    month = datetime.datetime.strptime(str(months[i]), "%Y%m")
                    month_start = int(month.replace(day=1, hour=0, minute=0, second=0).timestamp())
                    month_end = int(month.replace(day=calendar.monthrange(month.year, month.month)[1], hour=23, minute=59, second=59).timestamp())
                    tmp_plan_records = plan_records.filter(plan_id__in=group_plan_ids, create_time__gte=month_start, create_time__lte=month_end)
                    tmp_problems = problems.filter(plan_id__in=group_plan_ids, create_time__gte=month_start, create_time__lte=month_end)
                    # 测试计划运行次数（重跑的不计入）
                    plan_execution_count = tmp_plan_records.filter(is_rerun=0).count()
                    # 测试计划执行时长-平均值
                    plan_records_duration = round(sum(duration_transfer(plan_record.duration) for plan_record in tmp_plan_records)/plan_execution_count) if plan_execution_count else 0
                    # 不足1min算1min，0表示没记录不能算作1min
                    plan_records_duration = max(plan_records_duration // 60, 1) if plan_records_duration else 0
                    case_records_count = tmp_plan_records.aggregate(total_count=Sum('total_count'))['total_count'] if tmp_plan_records else 0
                    # 用例通过率 80% 返回80
                    case_pass_percent = round(tmp_plan_records.aggregate(success_count=Sum('success_count'))['success_count'] / case_records_count * 100) if case_records_count else 0
                    bug_quantity = tmp_problems.count()
                    default_bug_quantity = tmp_problems.filter(fail_type=0).count()
                    code_bug_quantity = tmp_problems.filter(fail_type=1).count()
                    environment_bug_quantity = tmp_problems.filter(fail_type=2).count()
                    case_bug_quantity = tmp_problems.filter(fail_type=3).count()
                    platform_bug_quantity = tmp_problems.filter(fail_type=4).count()

                    y_data["bug_quantity"].append(bug_quantity)
                    y_data["code_bug_quantity"].append(code_bug_quantity)
                    y_data["environment_bug_quantity"].append(environment_bug_quantity)
                    y_data["case_bug_quantity"].append(case_bug_quantity)
                    y_data["platform_bug_quantity"].append(platform_bug_quantity)
                    y_data["default_bug_quantity"].append(default_bug_quantity)
                    y_data["plan_records_duration"].append(plan_records_duration)
                    y_data["plan_execution_count"].append(plan_execution_count)
                    y_data["case_records_count"].append(case_records_count)
                    y_data["case_pass_percent"].append(case_pass_percent)
                response_data["y_data"].append(y_data)

        # 前端传了plan_ids/user表示按测试计划维度展示
        elif plan_ids or user:
            # group_ids、plan_ids都没传表示默认数据：当前用户所在筛选时间内最新的执行数据
            if not plan_ids:
                plan_record = PlanRecord.objects.filter(user=user, create_time__gte=create_time__gte, create_time__lte=create_time__lte, is_disable=0).order_by('-create_time').first()
                if plan_record:
                    plan_ids = [plan_record.plan_id]
                else:
                    # # 如当前用户没有执行记录，则返回空
                    return Response(status=status.HTTP_200_OK, data=response_data)
            plan_records = PlanRecord.objects.filter(plan_id__in=plan_ids, create_time__gte=create_time__gte, create_time__lte=create_time__lte, is_disable=0)
            problems = Problem.objects.filter(plan_id__in=plan_ids, create_time__gte=create_time__gte, create_time__lte=create_time__lte, is_disable=0)
            # 如查不到执行记录，直接返回空
            if not plan_records:
                return Response(status=status.HTTP_200_OK, data=response_data)
            response_data['summary']['total_bug_quantity'] = problems.count()
            response_data['summary']['total_code_bug_quantity'] = problems.filter(fail_type=1).count()
            response_data['summary']['total_plan_execution_count'] = plan_records.filter(is_rerun=0).count()
            response_data['summary']['total_case_records_count'] = plan_records.aggregate(total_count=Sum('total_count'))['total_count'] if plan_records else 0
            response_data['summary']['total_case_pass_percent'] = round(plan_records.aggregate(success_count=Sum('success_count'))['success_count'] / response_data['summary']['total_case_records_count'] * 100) if \
            response_data['summary']['total_case_records_count'] else 0
            response_data['summary']['total_plan_records_duration'] = sum(duration_transfer(plan_record.duration) for plan_record in plan_records)
            # 转成分钟返回给前端，不足1分钟算作1分钟
            response_data['summary']['total_plan_records_duration'] = max(response_data['summary']['total_plan_records_duration'] // 60, 1) if response_data['summary']['total_plan_records_duration'] else 0

            for plan_id in plan_ids:
                plan = Plan.objects.filter(id=plan_id).first()
                if plan:
                    plan_name = plan.name
                else:
                    plan_name = ''
                y_data = {
                    "id": int(plan_id),
                    "name": plan_name,
                    "bug_quantity": [],
                    "code_bug_quantity": [],
                    "environment_bug_quantity": [],
                    "case_bug_quantity": [],
                    "platform_bug_quantity": [],
                    "default_bug_quantity": [],
                    "plan_records_duration": [],
                    "plan_execution_count": [],
                    "case_records_count": [],
                    "case_pass_percent": []

                }
                for i in range(len(months)):
                    month = datetime.datetime.strptime(str(months[i]), "%Y%m")
                    month_start = int(month.replace(day=1, hour=0, minute=0, second=0).timestamp())
                    month_end = int(month.replace(day=calendar.monthrange(month.year, month.month)[1], hour=23, minute=59, second=59).timestamp())
                    tmp_plan_records = plan_records.filter(plan_id=plan_id, create_time__gte=month_start, create_time__lte=month_end)
                    tmp_problems = problems.filter(plan_id=plan_id, create_time__gte=month_start, create_time__lte=month_end)

                    plan_execution_count = tmp_plan_records.filter(is_rerun=0).count()
                    plan_records_duration = round(sum(duration_transfer(plan_record.duration) for plan_record in tmp_plan_records) / plan_execution_count) if plan_execution_count else 0
                    plan_records_duration = max(plan_records_duration // 60, 1) if plan_records_duration else 0
                    case_records_count = tmp_plan_records.aggregate(total_count=Sum('total_count'))['total_count'] if tmp_plan_records else 0
                    # 用例通过率 80% 返回80
                    case_pass_percent = round(tmp_plan_records.aggregate(success_count=Sum('success_count'))['success_count'] / case_records_count * 100) if case_records_count else 0
                    bug_quantity = tmp_problems.count()
                    default_bug_quantity = tmp_problems.filter(fail_type=0).count()
                    code_bug_quantity = tmp_problems.filter(fail_type=1).count()
                    environment_bug_quantity = tmp_problems.filter(fail_type=2).count()
                    case_bug_quantity = tmp_problems.filter(fail_type=3).count()
                    platform_bug_quantity = tmp_problems.filter(fail_type=4).count()

                    y_data["bug_quantity"].append(bug_quantity)
                    y_data["code_bug_quantity"].append(code_bug_quantity)
                    y_data["environment_bug_quantity"].append(environment_bug_quantity)
                    y_data["case_bug_quantity"].append(case_bug_quantity)
                    y_data["platform_bug_quantity"].append(platform_bug_quantity)
                    y_data["default_bug_quantity"].append(default_bug_quantity)
                    y_data["plan_records_duration"].append(plan_records_duration)
                    y_data["plan_execution_count"].append(plan_execution_count)
                    y_data["case_records_count"].append(case_records_count)
                    y_data["case_pass_percent"].append(case_pass_percent)

                response_data["y_data"].append(y_data)

        # 传参不对
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK, data=response_data)


@api_view(['GET'])
def plan_name_list(request):
    """
    return all name in Plan
    """
    if request.method == 'GET':
        plans = Plan.objects.values('id', 'name')
        return Response(status=status.HTTP_200_OK, data=plans)


@api_view(['GET'])
def user_name_list(request):
    """
    return all username in Plan or PlanRecord
    """
    if request.method == 'GET':
        names_plan = Plan.objects.values('person_in_charge', 'user', 'last_modify_user')
        names_plan_record = PlanRecord.objects.values('user')
        names = set()
        for row in names_plan:
            names.add(row['person_in_charge'])
            names.add(row['user'])
            names.add(row['last_modify_user'])
        for row in names_plan_record:
            names.add(row['user'])
        return Response(status=status.HTTP_200_OK, data=names)


@api_view(['GET'])
def group_name_list(request):
    """
    return all group_name
    """
    if request.method == 'GET':
        group_names = Group.objects.values('id', 'group_name')
        group_names = [{'id': item['id'], 'name': item['group_name']} for item in group_names]
        return Response(status=status.HTTP_200_OK, data=group_names)


@api_view(['GET', 'POST'])
def login(request):
    """
    return username password
    """
    if request.method == 'POST':
        AUTH_TICKET = request.data['AUTH_TICKET']
        AUTH_DOMAIN = request.data['AUTH_DOMAIN']
        url = "https://passport.futuoa.com/site/validate-ticket.html?AUTH_TICKET=" + AUTH_TICKET + "&AUTH_DOMAIN=" + AUTH_DOMAIN
        response = requests.get(url=url)
        if response.status_code == 200:
            data = response.json()
            if data["result"] == 0:
                username = data["data"]["user_info"]["nick"]
                password = data["data"]["oa_token"]
                email = data["data"]["user_info"]["email"]
                user = {
                    "username": username,
                    "password": password,
                    "email": email
                }
                try:
                    exist_user = OaUser.objects.get(username=username)
                    serializer = OaUserSerializer(data=user, instance=exist_user)
                except:
                    serializer = OaUserSerializer(data=user)
                if serializer.is_valid():
                    serializer.save()
                    return Response(status=status.HTTP_200_OK, data=user)
                else:
                    logger.info("serializer id_vaild failed %s", serializer.errors)

        logger.info("request passport failed %s %s", request, response.text)
        return Response(status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
def sync_ftest(request):
    """
    update database by shell timer
    """
    if request.method == 'POST':
        plans = Plan.objects.filter(is_disable=0)
        for plan in plans:
            sync_plan(plan.id)
            sync_plan_records(plan.id)
            plan_record_ids = PlanRecord.objects.filter(plan_id=plan.id).values_list('id', flat=True)
            for plan_record_id in plan_record_ids:
                sync_case_records(plan_record_id)
                sync_problems(plan_record_id)

        return Response(status=status.HTTP_200_OK)


def sync():
    logger.info('sync start=====')
    plans = Plan.objects.filter(is_disable=0)
    for plan in plans:
        sync_plan(plan.id)
        sync_plan_records(plan.id)
        plan_record_ids = PlanRecord.objects.filter(plan_id=plan.id).values_list('id', flat=True)
        for plan_record_id in plan_record_ids:
            sync_case_records(plan_record_id)
            sync_problems(plan_record_id)
    logger.info('sync end=====')