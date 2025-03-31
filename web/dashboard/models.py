from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class Plan(models.Model):
    id = models.BigIntegerField(db_comment='计划编号', primary_key=True, auto_created=False)
    name = models.CharField(max_length=256, db_comment='计划名称')
    memo = models.CharField(max_length=256, db_comment='计划描述', null=True, blank=True)
    person_in_charge = models.CharField(max_length=128, db_comment='负责人')
    mode = models.CharField(max_length=256, db_comment='运行模式：串行、并行')
    schedule_is_stop = models.BooleanField(db_comment='是否停止定时运行')
    schedule_time = models.CharField(max_length=256, db_comment='定时运行时间', null=True, blank=True)
    case_quantity = models.IntegerField(db_comment='用例数量')
    user = models.CharField(max_length=128, db_comment='创建人')
    create_time = models.CharField(max_length=256, db_comment='创建时间')
    last_modify_user = models.CharField(max_length=128, db_comment='更新人')
    update_time = models.CharField(max_length=256, db_comment='更新时间')
    is_disable = models.IntegerField(db_comment='测试计划从此平台删除：0未删除、1已删除', default=0)

    class Meta:
        db_table = "plan"


class PlanRecord(models.Model):
    id = models.BigIntegerField(db_comment='计划执行记录编号', primary_key=True, auto_created=False)
    plan_id = models.BigIntegerField(db_comment='所属的测试计划id')
    name = models.CharField(max_length=256, db_comment='测试计划执行名称:一般和测试计划名称相同，重跑不同')
    create_time = models.BigIntegerField(db_comment='创建时间/秒')
    update_time = models.BigIntegerField(db_comment='更新时间/秒')
    # ftest返回的字符串如"3min5s"
    duration = models.CharField(max_length=128, db_comment='执行耗时/秒')
    fail_count = models.IntegerField(db_comment='失败的用例数量')
    success_count = models.IntegerField(db_comment='成功的用例数量')
    total_count = models.IntegerField(db_comment='总用例数量')
    is_success = models.BooleanField(db_comment='执行成功True/失败False')
    user = models.CharField(max_length=128, db_comment='执行人')
    is_disable = models.IntegerField(db_comment='是否统计入看板:计入0;不计入1', default=0)
    is_rerun = models.IntegerField(db_comment='是否为重跑记录:否0;是1', default=0)

    class Meta:
        db_table = "plan_record"

    # def __repr__(self):
    #     return self.plan_num + '-' + self.plan_name + '-' + self.record_id


class CaseRecord(models.Model):
    id = models.BigIntegerField(db_comment='case执行记录编号', primary_key=True, auto_created=False)
    case_id = models.BigIntegerField(db_comment='所属的用例id')
    name = models.CharField(max_length=512, db_comment='用例名称')
    plan_record_id = models.BigIntegerField(db_comment='所属的测试计划执行记录plan_record_id')
    plan_id = models.BigIntegerField(db_comment='所属的测试计划plan_id')
    fail_type = models.IntegerField(db_comment='用例失败原因类型:0缺省/1代码原因/2环境原因/3用例原因/4平台原因')
    fail_reason = models.CharField(max_length=256, db_comment='用例失败原因详情', null=True, blank=True)
    is_success = models.BooleanField(db_comment='执行成功True/失败False')
    finish_time = models.BigIntegerField(db_comment='执行完成时间/秒')
    create_time = models.BigIntegerField(db_comment='case_record创建时间/秒')
    plan_record_create_time = models.BigIntegerField(db_comment='plan_record的创建时间/秒')
    # ftest返回的字符串如"3min5s"
    duration = models.CharField(max_length=128, db_comment='用例执行耗时/秒')
    person_in_charge = models.CharField(max_length=128, db_comment='负责人')
    is_disable = models.IntegerField(db_comment='是否统计入看板:计入0;不计入1', default=0)
    bug_link = models.CharField(max_length=512, db_comment='用例关联的bug单', null=True, blank=True, default=None)

    class Meta:
        db_table = "case_record"


class Problem(models.Model):
    id = models.AutoField(db_comment='问题id', primary_key=True, auto_created=True)
    fail_type = models.IntegerField(db_comment='用例失败原因类型:0缺省/1代码原因/2环境原因/3用例原因/4平台原因')
    fail_reason = models.CharField(max_length=256, db_comment='用例失败原因详情', null=True, blank=True)
    affect_case_qty = models.BigIntegerField(db_comment='该问题影响的用例数量，即导致多少条用例失败')
    plan_record_id = models.BigIntegerField(db_comment='所属的测试计划执行记录plan_record_id')
    plan_id = models.BigIntegerField(db_comment='所属的测试计划plan_id')
    case_record_ids = models.CharField(max_length=512, db_comment='用例执行id，以;分隔')
    create_time = models.BigIntegerField(db_comment='发现问题时间/秒=测试计划执行时间')
    person_in_charge = models.CharField(max_length=128, db_comment='负责人')
    bug_link = models.CharField(max_length=512, db_comment='关联缺陷单链接，可能存在多个以;分隔', null=True, blank=True, default=None)
    is_disable = models.IntegerField(db_comment='是否统计入看板:计入0;不计入1', default=0)

    class Meta:
        db_table = "problem"


class OaUser(AbstractUser):
    password = models.CharField(max_length=512, db_comment='AUTH_TICKET')
    group_id = models.BigIntegerField(db_comment='部门/小组id', default=0)

    class Meta:
        db_table = "oa_user"


class Group(models.Model):
    # id暂时先用自增，等接入组织架构后修改
    id = models.BigIntegerField(db_comment='部门/小组id', primary_key=True, auto_created=True)
    group_name = models.CharField(max_length=256, db_comment='部门/小组名称')
    group_level = models.BigIntegerField(db_comment='部门所属层级', default=0)

    class Meta:
        db_table = "group"