<template>
  <div class="data-container">
    <el-form :inline="true" :model="search_form" class="search-form">
      <el-form-item label="部门">
        <el-select v-model="search_form.group_id" filterable clearable placeholder="..." style="width: 250px;">
          <el-option
              v-for="item in group_options"
              :key="item.id"
              :value="item.id"
              :label="item.name"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="测试计划">
        <el-select v-model="search_form.plan_id" filterable clearable placeholder="..." style="width: 250px;">
          <el-option
              v-for="item in plan_options"
              :key="item.id"
              :label="item.name"
              :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="执行人">
        <el-select v-model="search_form.user" filterable clearable placeholder="...">
          <el-option
              v-for="item in user_options"
              :key="item"
              :value="item"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="结果">
        <el-select v-model="search_form.is_success" clearable placeholder="...">
          <el-option
              v-for="item in is_success_options"
              :key="item.key"
              :label="item.key"
              :value="item.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="时间">
        <el-date-picker v-model="search_form.create_time" type="daterange" range-separator="~"
                        value-format="YYYY-MM-DD HH:mm:ss" :default-time="default_time" style="width: 231px;"/>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="searchData(1)">搜索</el-button>
        <el-button @click="resetData">重置</el-button>
      </el-form-item>
    </el-form>
    <div class="table-info">
      <span class="table-name">运行记录</span>
    </div>
    <div class="data-dialog">
      <el-dialog v-model="update_dialog_visible" title="更新/关联">
        <el-button type="primary" @click="batchUpdateReason">批量更新</el-button>
        <el-button type="primary" @click="batchUpdateLink">批量关联</el-button>
        <el-table :data="dialog_data.data" stripe header-row-class-name="data-table-header"
                  show-overflow-tooltip highlight-current-row height="20em" tooltip-effect="light"
                  @selection-change="handleCaseSelection" @filter-change="getCaseList" style="font-size: 13px">
          <el-table-column type="selection" width="55"/>
          <el-table-column prop="name" label="用例名称"/>
          <el-table-column label="失败原因">
            <template #default="scope">
              {{ getFailType(scope.row.fail_type) }}<br>{{ getFailReason(scope.row.fail_reason) }}
            </template>
          </el-table-column>
          <el-table-column prop="bug_link" label="关联缺陷单"/>
          <el-table-column prop="person_in_charge" label="执行人"/>
        </el-table>
      </el-dialog>
    </div>
    <div class="data-table-container">
      <el-table :data="table_data.data" stripe header-row-class-name="data-table-header"
                show-overflow-tooltip highlight-current-row height="35em" tooltip-effect="light">
        <el-table-column prop="id" label="ID" fixed width="100em">
          <template #default="scope">
            <!--站外链接href以http/https开头, target 用来配置是否开启一个新标签页-->
            <el-link underline type="primary" :href=getDetail(scope.row.id) target="_blank">{{ scope.row.id }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="计划名称" width="300em"/>
        <el-table-column label="执行记录" width="210em">
          <template #default="scope">
            <div class="execute-record">
              <el-text type="success" size="default">成功:{{ scope.row.success_count }}</el-text>
              <el-text type="warning" size="default"> 失败:{{ scope.row.fail_count }}</el-text>
            </div>
            <!--            <el-progress :percentage="getPercentage(scope.row.success_count, scope.row.total_count)"-->
            <!--                         :show-text="false" :stroke-width="12" class="bug-process">-->
            <!--              <template #default="{ percentage }">-->
            <!--                <span class="percentage-value">{{ scope.row.success_count }}</span>-->
            <!--              </template>-->
            <!--            </el-progress>-->
          </template>
        </el-table-column>
        <el-table-column label="结果">
          <template #default="scope">
            <el-tag v-if="scope.row.is_success" type="success" style="width: 5em">通过</el-tag>
            <el-tag v-else type="warning" style="width: 5em">不通过</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开始执行时间" width="180em">
          <template #default="scope">
            {{
              toDateTime(scope.row.create_time)
            }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="总耗时"/>
        <el-table-column prop="user" label="执行人">
          <template #default="scope">
            <el-text class="user-name" type="primary">@{{ scope.row.user }}</el-text>
          </template>
        </el-table-column>
        <el-table-column fixed="right" label="操作" width="120em">
          <template #default="scope">
            <!--            <el-link underline type="primary" :href=getDetail(scope.row.id) target="_blank" class="operation-link">详情</el-link>-->
            <!--          <el-button text type="primary" class="operation-button" @click="showDialog(scope.row.id)">更新/关联</el-button>-->
            <el-popconfirm :title="'数据看板将' + (scope.row.is_disable ? '统计' : '不统计') + '本次执行记录'" width="20em"
               @confirm="updateItem(scope.row.id, scope.row.is_disable)">
              <template #reference>
                <el-button text type="danger" class="operation-button">
                  <div v-if=scope.row.is_disable>计入</div>
                  <div v-else>不计入</div>
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="page_container">
      <el-pagination background
                     :hide-on-single-page=false
                     layout="total, prev, pager, next"
                     :total="page_data.count"
                     v-model:current-page="page_data.page"
                     @current-change="getData"/>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, reactive, ref} from 'vue'
import {Task, TaskReq} from "~/api/task";
import {Case, CaseReq, CaseResp} from "~/api/case";
import {Plan} from "~/api/plan";
import {User} from "~/api/user";
import {toDateTime} from "~/utils/common";
import {Group} from "~/api/group";

onMounted(() => {
  buildOptions();
  getData();
})

const update_dialog_visible = ref(false)

const group_options = ref([])
const user_options = ref([])
const is_success_options = [
  {
    key: '通过',
    value: 1,
  },
  {
    key: '不通过',
    value: 0,
  },
]
const plan_options = ref([])

const search_form = reactive({
  group_id: '',
  user: '',
  plan_id: '',
  create_time: [],
  is_success: '',
})

const page_data = reactive({
  count: 0,
  page: 1,
  size: 10
})

const dialog_page_data = reactive({
  count: 0,
  page: 1,
  size: 10
})

const table_data = reactive({
  data: []
})

const dialog_data = reactive({
  data: []
})

const default_time = ref<[Date, Date]>([
  new Date(2023, 1, 1, 0, 0, 0),
  new Date(2023, 2, 1, 23, 59, 59),
])

function getPercentage(successCount: number, totalCount: number) {
  if (!totalCount) {
    return 0;
  }
  return successCount / totalCount * 100;
}

function buildOptions() {
  Group.getGroupNames().then(resp => {
    group_options.value = resp.data
  });
  Plan.getPlanNames().then(resp => {
    plan_options.value = resp.data
  });

  User.getUsers().then(resp => {
    user_options.value = resp.data
  });
}

function resetData() {
  search_form.group_id = '';
  search_form.create_time = [];
  search_form.plan_id = '';
  search_form.user = '';
  search_form.is_success = '';

  page_data.page = 1;

  getData();
}

function getData() {
  searchData(page_data.page);
}

function searchData(page: number) {
  const queryReq = search_form as TaskReq;
  queryReq.page = page;
  queryReq.size = page_data.size;
  const create_time = search_form.create_time;
  if (create_time && create_time.length == 2) {
    queryReq.create_time__gte = new Date(create_time[0]).getTime();
    queryReq.create_time__lte = new Date(create_time[1]).getTime();
  } else {
    queryReq.create_time__gte = null;
    queryReq.create_time__lte = null;
  }

  Task.get(queryReq)
      .then(response => {
        page_data.count = response.data.count;
        page_data.page = response.data.page;
        page_data.size = response.data.size;
        table_data.data = response.data.data;
      })
}

function getCaseList(plan_record_id: number) {
  const queryReq = {
    plan_record_id: plan_record_id
  } as CaseReq;
  Case.get(queryReq)
      .then(response => {
        dialog_page_data.count = response.data.count;
        dialog_page_data.page = response.data.page;
        dialog_page_data.size = response.data.size;
        dialog_data.data = response.data.data;
      })
}

function updateItem(id, is_disable) {
  Task.put(id, (is_disable + 1) % 2)
      .then(response => {
        getData();
      })
}

function getFailType(fail_type: number) {
  let type = '';
  switch (fail_type) {
    case 1:
      type = '代码原因';
      break;
    case 2:
      type = '环境原因';
      break;
    case 3:
      type = '用例原因';
      break;
    case 4:
      type = '平台原因';
      break;
  }
  type = '类型: ' + type;
  return type;
}

function getFailReason(fail_reason: string) {
  const reason = '具体原因: ' + fail_reason;
  return reason;
}

function getDetail(id) {
  return "http://ftest.server.com/testplanresult/form/?id=" + id
}

function showDialog(plan_record_id: number) {
  getCaseList(plan_record_id)
  update_dialog_visible.value = true
}

function handleCaseSelection(val: CaseResp[]) {

}

</script>

<style lang="scss">
.operation-button {
  padding-left: 0;
  //padding-right: 3px;
}

.operation-link {
  //font-size: 14px;
  //margin-bottom: 1px;
}

.ep-progress-bar__outer {
  background-color: #e57471;
}

//.des {
//  display: flex;
//  justify-content: space-between;
//  font-size: 14px;
//  font-weight: normal;
//  line-height: 20px;
//  color: #cecece;
//  margin-bottom: 4px;
//}
//.div {
//  display: flex;
//  gap: 5px;
//}
.num1 {
  color: #129bff;
}

.num2 {
  color: #e57471;
}

.user-name {
  font-style: italic;
  font-size: 14px;
}
</style>