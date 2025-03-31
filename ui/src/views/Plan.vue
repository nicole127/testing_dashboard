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
        <el-select v-model="search_form.id" filterable clearable placeholder="..." style="width: 250px;">
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
      <el-form-item>
        <el-button type="primary" @click="searchData(1)">搜索</el-button>
        <el-button @click="resetData">重置</el-button>
      </el-form-item>
    </el-form>
    <div class="table-info">
      <span class="table-name">已接入的测试计划</span>
      <el-button type="primary" class="table-operation" @click="add_dialog_visible=true">接入测试计划</el-button>
    </div>
    <div class="data-dialog">
      <el-dialog v-model="add_dialog_visible" title="添加测试计划" width="40vw"
                 :show-close="false"
                 :close-on-click-modal-close="false"
                 :close-on-press-escape="false"
      >
        <el-form :model="add_form">
          <el-form-item label="Ftest测试计划:">
            <el-input v-model="add_form.plan_url" placeholder="请输入Ftest测试计划链接"/>
          </el-form-item>
          <el-form-item>
            <div class="form-button">
              <el-button @click="closeDialog" v-if="!loading">取消</el-button>
              <el-button type="primary" @click="addPlan" :loading="loading">确定</el-button>
            </div>
          </el-form-item>
        </el-form>
      </el-dialog>
    </div>
    <div class="data-table-container">
      <el-table :data="table_data.data" stripe header-row-class-name="data-table-header"
                show-overflow-tooltip highlight-current-row height="35em"
                tooltip-effect="light" style="max-width: 100vw">
        <el-table-column prop="id" label="ID" fixed width="100em">
          <template #default="scope">
            <!--站外链接href以http/https开头, target 用来配置是否开启一个新标签页-->
            <el-link underline type="primary" :href=getDetail(scope.row.id) target="_blank">{{ scope.row.id }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="测试计划名称" width="300em"/>
        <el-table-column prop="memo" label="描述" width="300em"/>
        <el-table-column prop="case_quantity" label="用例数量"/>
        <el-table-column prop="mode" label="运行模式">
          <template #default="scope">
            <el-tag v-if="scope.row.mode == 'serial'" type="warning" style="width: 5em">串行</el-tag>
            <el-tag v-else type="success" style="width: 5em">并行</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="schedule_is_stop" label="定时运行">
          <template #default="scope">
            {{ scope.row.schedule_is_stop == true ? '否' : scope.row.schedule_is_stop == false ? '是' : '' }}
          </template>
        </el-table-column>
        <el-table-column prop="person_in_charge" label="负责人">
          <template #default="scope">
            <el-text class="user-name" type="primary">@{{ scope.row.person_in_charge }}</el-text>
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
import {Plan, PlanReq} from "~/api/plan"
import {User} from "~/api/user";
import {ElMessage} from "element-plus";
import {Group} from "~/api/group";

onMounted(() => {
  buildOptions();
  getData();
})

const group_options = ref([])
const user_options = ref([])
const plan_options = ref([])

const loading = ref(false)

const search_form = reactive({
  group_id: '',
  person_in_charge: '',
  id: '',
})

const add_form = reactive({
  plan_url: ''
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

function getDetail(id) {
  return "http://ftest.server.com/testplan/form/?id=" + id
}

function resetData() {
  search_form.group_id = '';
  search_form.id = '';
  search_form.person_in_charge = '';

  page_data.page = 1;

  getData();
}

function getData() {
  searchData(page_data.page);
}

function searchData(page: number) {
  const planReq = search_form as PlanReq
  planReq.page = page
  planReq.size = page_data.size
  Plan.get(planReq)
      .then(response => {
        page_data.count = response.data.count
        page_data.page = response.data.page
        page_data.size = response.data.size
        table_data.data = response.data.data
      })
}

function closeDialog() {
  add_dialog_visible.value = false;
  add_form.plan_url = '';
  loading.value = false;
}

function addPlan() {
  // loading.value = true;
  add_dialog_visible.value = false;
  // add_form.plan_url = '';
  // ElMessage.success('后台同步数据中')
  ElMessage({
    showClose: true,
    message: '后台数据同步中~',
    type: 'primary',
    duration: 3000,
    onClose: () => {
      getData();
      // loading.value = false;
      add_form.plan_url = '';
    }
  })
  Plan.post({url: add_form.plan_url})
      .then(response => {
        //doing success msg

        getData();
        // loading.value = false;
        add_form.plan_url = '';
      }).catch(error => {
    // loading.value = false;
    // add_dialog_visible.value = false;
  })
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