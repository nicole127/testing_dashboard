import json
import logging
import requests
# from dashboard.models import Plan
# from dashboard.serializers import PlanSerializer

logger = logging.getLogger()


def get_cookie():
    # search db
    cookie = "username=autoweb; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTc2MjE4NTMsImlhdCI6MTY5NzUzNTQ1MywibmJmIjoxNjk3NTM1NDUzLCJ1c2VybmFtZSI6ImF1dG93ZWIifQ.Y_eCeIkU8GAyEqqkq6YII10bNwuuRLeoqIXXUcq0fu4"
    return cookie


def get_plan_detail(id):
    '''
    根据测试计划id获取测试计划详情
    :param id:
    :return:
    '''
    response = send_get_request("testplan/" + str(id) + "/")
    test_plan = response.get("testplan")
    # plan = Plan()
    plan = {
        "id": test_plan.get("id"),
        "name": test_plan.get("name"),
        "memo": test_plan.get("memo"),
        "person_in_charge": test_plan.get("person_in_charge"),
        "mode": test_plan.get("mode"),
        "schedule_is_stop": test_plan.get("schedule_is_stop"),
        "schedule_time": test_plan.get("schedule_time"),
        "case_quantity": len(test_plan.get("case_list")),
        "user": test_plan.get("user"),
        "create_time": test_plan.get("create_time"),
        "last_modify_user": test_plan.get("last_modify_user"),
        "update_time": test_plan.get("update_time"),
        "is_disable": 0
    }
    # 可能添加了用例树，需要将用例树下的用例数量计入
    if test_plan.get("tree_list"):
        for tree in test_plan.get("tree_list"):
            plan["case_quantity"] += int(send_get_request("cases/filter_all/", tree_id=tree["id"]).get("case_total_num"))

    return plan


def get_plan_records(plan):
    '''
    根据plan对象获取执行记录：ftest只支持按照测试计划名称模糊搜索，因此这里要转换处理成精确匹配查询
    :param name:
    :return:
    '''
    offset = 0
    limit = 200
    include_rerun = 1
    # 存储获取的所有数据
    all_results = []
    while True:
        response = send_get_request("testplanresults/all", name=plan.name, offset=offset, limit=limit, include_rerun=include_rerun)
        results = response.get("testplanresults")
        all_results.extend(results)
        # 判断是否已获取所有数据
        if response.get("paging")["next"]:
            offset = (response.get("paging")["next"]).split("offset=")[1].split("&")[0]
        else:
            break

    plan_records = []
    for result in all_results:
        if result["testplan_id"] == plan.id:
            # 去掉被终止的执行记录、去掉数据初始化失败（成功0失败0）的执行记录
            if (result["status"] == 7) or (result["fail_count"] == result["success_count"] == 0):
                continue
            else:
                print(result["id"], result["duration"])
                plan_record = {
                    "id": result["id"],
                    "plan_id": result["testplan_id"],
                    "name": result["testplan"]["name"],
                    "create_time": result["create_time"],
                    "update_time": result["update_time"],
                    "duration": result["duration"],
                    "fail_count": result["fail_count"],
                    "success_count": result["success_count"],
                    "total_count": result["total_count"],
                    "is_success": result["is_success"],
                    "user": result["user"],
                    "is_disable": 0,
                    "is_rerun": 0
                }
                # 区分是否为重跑，重跑要和原来的执行记录统计为1次执行记录
                if "(失败用例重跑 原测试计划ID=" in result["testplan"]["name"]:
                    plan_record["is_rerun"] = 1
                plan_records.append(plan_record)

    return plan_records


def get_plan_record_detail(plan_record_id):
    '''
    根据record_id获取执行结果详情，然后存入case_record表，存入problem表
    :param name:
    :return: case_records、problems
    '''
    response = send_get_request("testplanresult/" + str(plan_record_id))
    # print(json.dumps(response, indent=4))
    plan_id = response.get("testplanresult")["testplan_id"]
    plan_record_create_time = response.get("testplanresult")["create_time"]
    cases_result = response.get("cases_result")
    case_records = {}
    problems = {}
    for result in cases_result:
        if not result["is_success"]:
            # ftest失败原因映射：缺省0/代码问题1与数据库取值一致
            # 失败原因：环境问题
            if result["fail_type"] in (2, 6):
                result["fail_type"] = 2
            # 失败原因：用例问题
            elif result["fail_type"] in (4, 5, 7, 8):
                result["fail_type"] = 3
            # 失败原因：平台问题
            elif result["fail_type"] in (3, 9, 10, 11, 12):
                result["fail_type"] = 4
            case_record = {
                "id": result["id"],
                "case_id": result["case"]["id"],
                "name": result["case"]["name"],
                "plan_record_id": plan_record_id,
                "plan_id": plan_id,
                "plan_record_create_time": plan_record_create_time,
                "fail_type": result["fail_type"],
                "fail_reason": result["fail_reason"],
                "is_success": result["is_success"],
                "finish_time": result["finish_time"],
                "create_time": result["create_time"],
                "duration": result["duration"],
                "person_in_charge": result["case"]["person_in_charge"]
            }
            # 失败重试3次的用例只记录最后一次的执行结果
            case_records[result["case"]["id"]] = case_record
            # # 1个问题导致的8条用例失败，需要映射成1个问题存到problem表中
            # if not result["is_success"]:
            #     key = (plan_id, plan_record_id, plan_record_create_time, result["fail_type"], result["fail_reason"])
            #     if key in problems:
            #         problems[key]["affect_case_qty"] += 1
            #         problems[key]["case_record_ids"] += ";" + str(result["id"])
            #     else:
            #         problems[key] = {
            #             "fail_type": result["fail_type"],
            #             "fail_reason": result["fail_reason"],
            #             "affect_case_qty": 1,
            #             "create_time": plan_record_create_time,
            #             "plan_record_id": plan_record_id,
            #             "plan_id": plan_id,
            #             "case_record_ids": str(result["id"]),
            #             "person_in_charge": result["case"]["person_in_charge"],
            #             "is_disable": 0
            #         }

    return {
        "case_records": list(case_records.values()),
        # "problems": list(problems.values())
    }


def set_case_fail_reason(case_record_ids, fail_type, fail_reason):
    '''
    批量更新用例失败原因：失败重试3次的case_record应该去重只记录一次@nicole还未做
    :param name:
    :return:
    '''
    # 失败原因映射到ftest
    # 失败原因：缺省=0 -> 缺省=0
    # 失败原因：代码问题=1 -> 被测环境问题-代码bug=1
    # 失败原因：环境问题=2 -> 被测环境问题-其他=2
    # 失败原因：用例问题 -> 用例问题-其他
    if fail_type == 3:
        fail_type = 8
    # 失败原因：平台问题 -> 平台问题-其他
    if fail_type == 4:
        fail_type = 12
    params = {
        # "id": 1,  # 批量更新id没有用处，可以不传
        "case_task_ids": case_record_ids,   # 批量更新要传这个字段，多个case_record_id,以分号间隔如"122353670;122353801"
        "fail_type": fail_type,
        "fail_reason": fail_reason
    }
    response = send_put_request(url="casetask/1/", **params)
    return response


def send_get_request(url, **kwargs):
    host = "http://ftest.server.com/api/"
    headers = {
        "Content-Type": "application/json",
        "Cookie": get_cookie()
    }

    try:
        request = requests.get(url=host+url, headers=headers, params=kwargs)
        if request.status_code == 200:
            return request.json().get("data")
        else:
            logger.info("request ftest failed {}", request)
    except Exception as e:
        logger.info("request ftest failed {} {}", url, **kwargs)
        pass
    return None


def send_put_request(url, **kwargs):
    host = "http://ftest.server.com/api/"
    headers = {
        "Content-Type": "application/json",
        "Cookie": get_cookie()
    }

    try:
        request = requests.put(url=host+url, headers=headers, data=json.dumps(kwargs))
        if request.status_code == 200:
            # return request.json().get("data")
            return request.status_code
        else:
            logger.info("request ftest failed {}", request)
    except Exception as e:
        logger.info("request ftest failed {} {}", url, **kwargs)
        pass
    return None


if __name__ == "__main__":
    pass

    # 查询测试计划详情
    # res = get_plan_detail(1994)
    # print(json.dumps(res, indent=4))

    # # 根据plan_id查询执行记录列表
    # res = get_plan_records(2529)
    # print(json.dumps(res, indent=4))

    # 根据执行id查询执行详情
    res = get_plan_record_detail(6005295)
    print(json.dumps(res, indent=4))

    # # 更新用例失败原因
    # res = set_case_fail_reason("122353670;122353801;122353232", 22, "test_1")
    # print(res)

    # AUTH_TICKET = 'kpVMYq8OV9oBsiJ_1GVGS7UpTj0wHkMeGKXU-SAz5zSBlnW6G40AJTnNo7xrawFWw6JKz9Q5dUE-Z6pFyg1DrW2LnNGUjPQTvHXbpw9DeqY%3D&LANG=ZH-CN'
    # AUTH_DOMAIN = '192.168.32.45'
    # url = "https://passport.futuoa.com/site/validate-ticket.html?AUTH_TICKET=" + AUTH_TICKET + "&AUTH_DOMAIN=" + AUTH_DOMAIN
    # response = requests.get(url=url)
    # print(response)
    # print(response.text)









