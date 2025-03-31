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
      <el-form-item label="负责人">
        <el-select v-model="search_form.person_in_charge" filterable clearable placeholder="...">
          <el-option
              v-for="item in user_options"
              :key="item"
              :value="item"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="问题类型">
        <el-select v-model="search_form.fail_type" filterable clearable placeholder="...">
          <el-option
              v-for="item in fail_type_options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="问题描述">
        <el-input v-model="search_form.fail_reason" filterable clearable placeholder="..." style="width: 250px;">
        </el-input>
      </el-form-item>
      <el-form-item label="时间">
        <el-date-picker v-model="search_form.create_time" type="daterange" range-separator="~"
                        value-format="YYYY-MM-DD HH:mm:ss" :default-time="default_time" style="width: 231px"/>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="searchData(1)">搜索</el-button>
        <el-button @click="resetData">重置</el-button>
      </el-form-item>
    </el-form>
    <div class="table-info">
      <span class="table-name">问题分析</span>
    </div>
    <div class="data-dialog">
      <el-dialog v-model="add_dialog_visible" title="关联缺陷单" width="40vw"
                 :show-close="false"
                 :close-on-click-modal-close="false"
                 :close-on-press-escape="false"
      >
        <el-form :model="add_form">
          <el-form-item label="飞书缺陷链接:">
            <el-input v-model="add_form.bug_link" placeholder="请输入飞书缺陷链接"/>
          </el-form-item>
          <el-form-item>
            <div class="form-button">
              <el-button @click="closeDialog" v-if="!loading">取消</el-button>
              <el-button type="primary" @click="onSubmit" :loading="loading">确定</el-button>
            </div>
          </el-form-item>
        </el-form>
      </el-dialog>
    </div>
    <div class="data-table-container">
      <el-table :data="table_data.data" stripe header-row-class-name="data-table-header"
                show-overflow-tooltip highlight-current-row height="35em"
                tooltip-effect="light" style="max-width: 100%">
        <el-table-column prop="id" label="ID" fixed width="100em"/>
        <el-table-column prop="fail_reason" label="问题描述" width="500em"/>
        <el-table-column prop="fail_type" label="问题类型">
          <template #default="scope">
            <el-tag :type=getFailTypeColor(scope.row.fail_type) style="width: 6em">
              {{ getFailTypeName(scope.row.fail_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="affect_case_qty" label="失败用例" width="120em">
          <template #default="scope">
            <el-popover placement="right" :width="100" trigger="click">
              <template #reference>
                <el-button text type="primary">
                  {{ getCaseRecordCount(scope.row.case_record_ids) }}
                </el-button>
              </template>
              <template #default>
                <el-table :data="getCaseRecords(scope.row.case_record_ids)">
                  <el-table-column label="失败用例记录" align="center">
                    <template #default="subScope">
                      <el-link underline type="primary" :href=subScope.row.url target="_blank">
                        {{ subScope.row.id }}
                      </el-link>
                    </template>
                  </el-table-column>
                </el-table>
              </template>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="发现时间" width="200em">
          <template #default="scope">
            {{
              toDateTime(scope.row.create_time)
            }}
          </template>
        </el-table-column>
        <el-table-column prop="person_in_charge" label="负责人" width="150em">
          <template #default="scope">
            <el-text class="user-name" type="primary">@{{ scope.row.person_in_charge }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="250em">
          <template #default="scope">
            <el-button type="primary" text @click="showDialog(scope.row.id)" style="padding-left: 0">关联缺陷单</el-button>
            <el-popover :width="100" placement="right" trigger="click" v-if="scope.row.bug_links.length > 1">
              <template #reference>
                <el-button text type="success" style="padding: 0; margin-left: 0">
                  飞书缺陷单
                </el-button>
              </template>
              <template #default>
                <el-table :data="scope.row.bug_links">
                  <el-table-column label="缺陷单地址" align="center">
                    <template #default="subScope">
                      <el-link underline type="success" :href=subScope.row.bug_link target="_blank">
                        {{ subScope.row.display_name }}
                      </el-link>
                    </template>
                  </el-table-column>
                </el-table>
              </template>
            </el-popover>
            <el-link v-else-if="scope.row.bug_links.length === 1" underline type="success" :href=scope.row.bug_link
                     target="_blank">
              飞书缺陷单
            </el-link>
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
import {Plan} from "~/api/plan"
import {User} from "~/api/user";
import {toDateTime} from "~/utils/common";
import {Problem, ProblemReq} from "~/api/problem";
import {useAppStore} from "~/store";
import {Group} from "~/api/group";

const appStore = useAppStore();
onMounted(() => {
  buildOptions();
  if (appStore.search_form.clicked) {
    appStore.search_form.clicked = false;
    search_form.group_id = appStore.search_form.group_id;
    search_form.plan_id = appStore.search_form.plan_id;
    if (appStore.search_form.create_time && appStore.search_form.create_time.length == 2) {
      search_form.create_time = [appStore.search_form.create_time[0]
      + ' 00:00:00', appStore.search_form.create_time[1] + ' 23:59:59'];
    }
    search_form.fail_type = appStore.search_form.fail_type;
  }
  getData();
})

const default_time = ref<[Date, Date]>([
  new Date(2023, 1, 1, 0, 0, 0),
  new Date(2023, 2, 1, 23, 59, 59),
])

const group_options = ref([])

const fail_type_options = [
  {
    value: 0,
    label: '缺省',
    color: ''
  },
  {
    value: 1,
    label: '代码原因',
    color: 'danger'
  },
  {
    value: 2,
    label: '环境原因',
    color: 'success'
  },
  {
    value: 3,
    label: '用例原因',
    color: 'warning'
  },
  {
    value: 4,
    label: '平台原因',
    color: 'info'
  },
]
const user_options = ref([])
const plan_options = ref([])

const loading = ref(false)

const search_form = reactive({
  group_id: '',
  person_in_charge: '',
  plan_id: '',
  create_time: [],
  fail_type: '',
  fail_reason: '',
  create_time__gte: '',
  create_time__lte: '',
})

const add_form = reactive({
  id: '',
  bug_link: ''
})

const page_data = reactive({
  count: 0,
  page: 1,
  size: 10
})

const table_data = reactive({
  data: []
})

const add_dialog_visible = ref(false)

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
  search_form.plan_id = '';
  search_form.person_in_charge = '';
  search_form.create_time = [];
  search_form.fail_type = '';
  search_form.fail_reason = '';
  search_form.create_time__gte = '';
  search_form.create_time__lte = '';

  page_data.page = 1;

  getData();
}

function getData() {
  searchData(page_data.page);
}

function searchData(page: number) {
  const queryReq = search_form as ProblemReq
  if (search_form.create_time && search_form.create_time.length == 2) {
    search_form.create_time__gte = new Date(search_form.create_time[0]).getTime() + '';
    search_form.create_time__lte = new Date(search_form.create_time[1]).getTime() + '';
  } else {
    queryReq.create_time__gte = null;
    queryReq.create_time__lte = null;
  }
  queryReq.page = page
  queryReq.size = page_data.size
  Problem.get(queryReq)
      .then(response => {
        page_data.count = response.data.count
        page_data.page = response.data.page
        page_data.size = response.data.size
        table_data.data = response.data.data
        table_data.data.forEach(temp => {
          temp.bug_links = getBugLinks(temp.bug_link);
        });
      })
}

function closeDialog() {
  add_dialog_visible.value = false;
  add_form.bug_link = '';
  loading.value = false;
}

function showDialog(id: number) {
  add_dialog_visible.value = true;
  add_form.id = String(id);
}

function getBugLinks(link: string) {
  const ret = [];
  if (link) {
    const bugLinks = link.split(';');
    bugLinks.forEach(temp => {
      let displayName = temp.trim();
      try {
        if (temp.endsWith('/')) {
          displayName = temp.substring(0, temp.length - 1);
        }
        var bugCode = displayName.split("?")[0].split('/');
        displayName = bugCode[bugCode.length - 1]
      } catch (e) {
        console.error(e)
      }
      const bugLink = {'bug_link': temp, 'display_name': displayName};
      ret.push(bugLink);
    })
  }
  return ret;
}

function onSubmit() {
  // loading.value = true;
  Problem.put(add_form.id, add_form.bug_link)
      .then(response => {
        //doing success msg
        add_dialog_visible.value = false;
        add_form.bug_link = '';
        getData();
        loading.value = false;
      }).catch(error => {
    loading.value = false;
  })
}

function getFailTypeName(failType: number) {
  if (failType >= 0 && failType < fail_type_options.length) {
    return fail_type_options[failType].label;
  }
  return fail_type_options[0].label;
}

function getFailTypeColor(failType: number) {
  if (failType >= 0 && failType < fail_type_options.length) {
    return fail_type_options[failType].color;
  }
  return '';
}

function getCaseRecords(ids: string | null | number) {
  const ret = [];
  if (!ids) {
    return ret;
  }
  const array = (ids + "").split(";");

  array.forEach(temp => {
    ret.push({
      id: temp,
      url: "http://ftest.server.com/testcase/result/?id=" + temp
    });
  })
  return ret;
}

function getCaseRecordCount(ids: string | null | number) {
  if (!ids) {
    return 0;
  }
  const array = (ids + "").split(";");
  return array.length;
}


</script>

<style lang="scss" scoped>
.form-button {
  margin-left: auto;
}

.user-name {
  font-style: italic;
  font-size: 14px;
}
</style>