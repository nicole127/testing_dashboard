<template>
  <div class="data-container">
    <el-form :inline="true" :model="search_form" class="search-form">
      <el-form-item label="部门">
        <el-select v-model="search_form.group_ids" multiple collapse-tags collapse-tags-tooltip :max-collapse-tags="1"
                   filterable clearable placeholder="..." style="width: 20em;"
                   :disabled="search_form.plan_ids.length > 0" >
          <el-option
              v-for="item in group_options"
              :key="item.id"
              :value="item.id"
              :label="item.name"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="测试计划">
        <el-select v-model="search_form.plan_ids" multiple collapse-tags collapse-tags-tooltip :max-collapse-tags="1"
                   filterable clearable placeholder="..." style="width: 20em"
                   :disabled="search_form.group_ids.length > 0">
          <el-option
              v-for="item in plan_options"
              :key="item.id"
              :value="item.id"
              :label="item.name"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="时间">
        <el-date-picker v-model="search_form.create_time" type="monthrange" range-separator="~"
                        value-format="YYYY-MM-DD" :clearable="false"/>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="getData">搜索</el-button>
        <el-button @click="resetData">重置</el-button>
      </el-form-item>
    </el-form>
    <div class="data-statistic">
      <div class="data-statistic-item">
        <div class="data-statistic-icon-container">
          <WarnTriangleFilled class="data-statistic-icon data-statistic-bug-icon"/>
        </div>
        <div class="data-statistic-content-container">
          <div class="data-static-item-title">
            发现问题量
          </div>
          <div class="data-static-item-content">
            <span class="data-static-item-content-value data-statistic-bug-value">{{
                summary_data.total_code_bug_quantity
              }}</span>
            <!--            <span class="data-static-item-content-value data-static-item-content-value2">/{{-->
            <!--                summary_data.total_bug_quantity-->
            <!--              }}</span>-->
            <span class="data-static-item-content-suffix">个</span>
          </div>
        </div>
      </div>
      <div class="data-statistic-item">
        <div class="data-statistic-icon-container">
          <Checked class="data-statistic-icon data-statistic-pass-icon"/>
        </div>
        <div class="data-statistic-content-container">
          <div class="data-static-item-title">
            用例通过率
          </div>
          <div class="data-static-item-content">
            <span class="data-static-item-content-value data-statistic-pass-value">{{
                summary_data.total_case_pass_percent
              }}</span>
            <span class="data-static-item-content-suffix">%</span>
          </div>
        </div>
      </div>
      <div class="data-statistic-item">
        <div class="data-statistic-icon-container">
          <Histogram class="data-statistic-icon data-statistic-count-icon"/>
        </div>
        <div class="data-statistic-content-container">
          <div class="data-static-item-title">
            用例运行量
          </div>
          <div class="data-static-item-content">
            <span class="data-static-item-content-value data-statistic-count-value">{{
                summary_data.total_case_records_count
              }}</span>
            <span class="data-static-item-content-suffix">条</span>
          </div>
        </div>
      </div>
      <div class="data-statistic-item">
        <div class="data-statistic-icon-container">
          <TrendCharts class="data-statistic-icon data-statistic-duration-icon"/>
        </div>
        <div class="data-statistic-content-container">
          <div class="data-static-item-title">
            计划执行时长
          </div>
          <div class="data-static-item-content">
            <span class="data-static-item-content-value data-statistic-duration-value">{{
                summary_data.total_plan_records_duration
              }}</span>
            <span class="data-static-item-content-suffix">分钟</span>
          </div>
        </div>
      </div>
    </div>
    <div class="data-chart">
      <div class="data-chart-line">
        <div id="data-chart-bug-quantity" class="data-chart-item"/>
        <div id="data-chart-case-pass-percent" class="data-chart-item"/>
      </div>
      <div class="data-chart-line">
        <div id="data-chart-case-records-count" class="data-chart-item"/>
        <div id="data-chart-plan-records-duration" class="data-chart-item"/>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, reactive, ref} from 'vue'
import {
  Histogram,
  Checked,
  Failed,
  SuccessFilled,
  WarnTriangleFilled,
  Opportunity,
  TrendCharts
} from "@element-plus/icons-vue";
import {Board, BoardData, BoardReq, BoardResp} from "~/api/board";
import * as echarts from 'echarts';
import {Plan} from "~/api/plan";
import {useAppStore} from "~/store";
import router from "~/router";
import {Group} from "~/api/group";
import {toDate, toDateTime} from "~/utils/common";

const appStore = useAppStore();

onMounted(() => {
  buildCharts();
  buildOptions();
  getData();
})

let chart_bug_quantity_id = null;
let chart_case_pass_percent_id = null;
let chart_case_records_count_id = null;
let chart_plan_records_duration_id = null;

const planName2PlanId = new Map();
const groupName2GroupId = new Map();

const group_options = ref([]);
const plan_options = ref([]);
const search_form = reactive({
  group_ids: [],
  create_time: [],
  plan_ids: [],
  create_time__gte: 0,
  create_time__lte: 0,
});
const summary_data = reactive({
  total_bug_quantity: 0,
  total_case_pass_percent: 0,
  total_case_records_count: 0,
  total_plan_records_duration: 0,
  total_code_bug_quantity: 0,
  total_plan_execution_count: 0,
});
const chart_data = reactive({
  xData: [],
  chart_bug_quantity: {
    series: []
  },
  chart_case_pass_percent: {
    series: []
  },
  chart_case_records_count: {
    series: []
  },
  chart_plan_records_duration: {
    series: []
  },
});

function buildOptions() {
  Plan.getPlanNames().then(resp => {
    plan_options.value = resp.data
  });
  Group.getGroupNames().then(resp => {
    group_options.value = resp.data
  });
}

function buildCharts() {
  initCharts();
  updateCharts();
  chart_bug_quantity_id.on('click', function (params) {
    appStore.search_form.clicked = true;

    const startDate = new Date(toDateTime(search_form.create_time__gte / 1000));
    startDate.setMonth(startDate.getMonth() + params.dataIndex);

    const endDate = new Date(startDate.getFullYear(), startDate.getMonth() + 1, 0);

    appStore.search_form.create_time = [toDate(startDate), toDate(endDate)];
    if (groupName2GroupId.size > 0) {
      appStore.search_form.plan_id = '';
      appStore.search_form.group_id = groupName2GroupId.get(params.seriesName);
    } else {
      appStore.search_form.plan_id = planName2PlanId.get(params.seriesName);
      appStore.search_form.group_id = '';
    }
    router.push('/problem')
  });
}

function initCharts() {
  echarts.dispose(document.getElementById('data-chart-bug-quantity') as HTMLElement)
  echarts.dispose(document.getElementById('data-chart-case-pass-percent') as HTMLElement);
  echarts.dispose(document.getElementById('data-chart-case-records-count') as HTMLElement);
  echarts.dispose(document.getElementById('data-chart-plan-records-duration') as HTMLElement);

  chart_bug_quantity_id = echarts.init(document.getElementById('data-chart-bug-quantity'));
  chart_case_pass_percent_id = echarts.init(document.getElementById('data-chart-case-pass-percent'));
  chart_case_records_count_id = echarts.init(document.getElementById('data-chart-case-records-count'));
  chart_plan_records_duration_id = echarts.init(document.getElementById('data-chart-plan-records-duration'));
}

function updateCharts() {
  chart_bug_quantity_id.setOption({
    // graphic: [
  //   {
  //     type: "text",
  //     left: "center",
  //     top: "center",
  //     style: {
  //       text: "No data available"
  //     }
  //   }
  // ],
    title: {
      // text: "{a| 发现问题量}",
      text: "发现问题量",
      padding: [10, 0, 0, 15],
      textStyle: {
        rich: {
          a: {}
        }
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      valueFormatter: (value) => value + '个'
    },
    //是否显示图例
    legend: {
      type: 'scroll',
      top: '5%',
      left: '20%',
      //上右下左
      // padding: [5, 5, 5, 5],
    },
    xAxis: {
      type: 'category',
      data: chart_data.xData
    },
    yAxis: {
      type: 'value',
      // min: 1,
      minInterval: 1,
      axisLabel: {
        formatter: '{value}个'
      }
    },
    series: chart_data.chart_bug_quantity.series
  });
  chart_case_pass_percent_id.setOption({
    title: {
      text: '用例通过率',
      padding: [10, 0, 0, 15],
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      valueFormatter: (value) => value + '%'
    },

    legend: {
      type: 'scroll',
      top: '5%',
      left: '20%',
    },
    xAxis: {
      type: 'category',
      data: chart_data.xData
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: chart_data.chart_case_pass_percent.series
  });
  chart_case_records_count_id.setOption({
    title: {
      text: '用例运行量',
      padding: [10, 0, 0, 15],
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      valueFormatter: (value) => value + '条'
    },

    legend: {
      type: 'scroll',
      top: '5%',
      left: '20%',
    },
    xAxis: {
      type: 'category',
      data: chart_data.xData
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: {
        formatter: '{value}条'
      }
    },
    series: chart_data.chart_case_records_count.series
  });
  chart_plan_records_duration_id.setOption({
    title: {
      text: '计划执行时长',
      padding: [10, 0, 0, 15],
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      valueFormatter: (value) => value + '分钟'
    },

    legend: {
      type: 'scroll',
      top: '5%',
      left: '20%',
    },
    xAxis: {
      type: 'category',
      data: chart_data.xData
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: {
        formatter: '{value}分钟'
      },
    },
    series: chart_data.chart_plan_records_duration.series
  });
}

function getData() {
  if (!search_form.create_time || search_form.create_time.length < 2 || !search_form.create_time[0] || !search_form.create_time[1]) {
    buildDate(null, null);
  } else {
    buildDate(new Date(search_form.create_time[0]), new Date(search_form.create_time[1]));
  }
  Board.get(search_form as BoardReq)
      .then(resp => {
        const data: BoardResp = resp.data;

        Object.assign(summary_data, data.summary);

        chart_data.xData = data.x_data;

        let yData = data.y_data;

        const chart_bug_quantity = [];
        const chart_case_pass_percent = [];
        const chart_case_records_count = [];
        const chart_plan_records_duration = [];
        planName2PlanId.clear();
        groupName2GroupId.clear();

        const noData = !yData || yData.length == 0;
        if (noData) {
          const data = Array(chart_data.xData.length).fill(0);
          const boardData = {
            'id': '',
            'name': '',
            'bug_quantity': data,
            'code_bug_quantity': data,
            'environment_bug_quantity': data,
            'case_bug_quantity': data,
            'platform_bug_quantity': data,
            'default_bug_quantity': data,
            'plan_records_duration': data,
            'case_records_count': data,
            'case_pass_percent': data,
            'plan_execution_count': data,
          } as BoardData;
          yData = [];
          yData.push(boardData);
        }

        for (let i = 0; i < yData.length; i++) {
          const boardData = yData[i];
          if(boardData.name) {
            if (search_form.group_ids && search_form.group_ids.length > 0) {
              groupName2GroupId.set(boardData.name, boardData.id);
            } else {
              planName2PlanId.set(boardData.name, boardData.id);
            }
          }

          const code_bug_quantity = {
            name: '',
            type: noData?'line':'bar',
            stack: '',
            data: [],
          };
          code_bug_quantity.name = boardData.name;
          // code_bug_quantity.stack = boardData.plan_name;
          code_bug_quantity.data = boardData.code_bug_quantity;
          chart_bug_quantity.push(code_bug_quantity);

          const environment_bug_quantity = {
            name: '',
            type: 'bar',
            stack: '',
            data: [],
          };
          environment_bug_quantity.name = boardData.name + '_环境问题';
          environment_bug_quantity.stack = boardData.name;
          environment_bug_quantity.data = boardData.environment_bug_quantity;
          // chart_bug_quantity.push(environment_bug_quantity);

          const case_bug_quantity = {
            name: '',
            type: 'bar',
            stack: '',
            data: [],
          };
          case_bug_quantity.name = boardData.name + '_用例问题';
          case_bug_quantity.stack = boardData.name;
          case_bug_quantity.data = boardData.case_bug_quantity;
          // chart_bug_quantity.push(case_bug_quantity);

          const platform_bug_quantity = {
            name: '',
            type: 'bar',
            stack: '',
            data: [],
          };
          platform_bug_quantity.name = boardData.name + '_平台问题';
          platform_bug_quantity.stack = boardData.name;
          platform_bug_quantity.data = boardData.platform_bug_quantity;
          // chart_bug_quantity.push(platform_bug_quantity);

          const default_bug_quantity = {
            name: '',
            type: 'bar',
            stack: '',
            data: [],
          };
          default_bug_quantity.name = boardData.name + '_缺省问题';
          default_bug_quantity.stack = boardData.name;
          default_bug_quantity.data = boardData.default_bug_quantity;
          // chart_bug_quantity.push(default_bug_quantity);

          const case_pass_percent = {
            name: '',
            type: 'line',
            stack: '',
            data: [],
          };
          case_pass_percent.name = boardData.name;
          case_pass_percent.stack = boardData.name;
          case_pass_percent.data = boardData.case_pass_percent;
          chart_case_pass_percent.push(case_pass_percent);

          const case_records_count = {
            name: '',
            type: noData?'line':'bar',
            data: [],
          };
          case_records_count.name = boardData.name;
          case_records_count.data = boardData.case_records_count;
          chart_case_records_count.push(case_records_count);

          const plan_records_duration = {
            name: '',
            type: 'line',
            stack: '',
            data: [],
          };
          plan_records_duration.name = boardData.name;
          plan_records_duration.stack = boardData.name;
          plan_records_duration.data = boardData.plan_records_duration;
          chart_plan_records_duration.push(plan_records_duration);
        }

        if (search_form.plan_ids.length == 0 && search_form.group_ids.length == 0) {
          search_form.plan_ids = Array.from(planName2PlanId.values());
        }

        chart_data.chart_bug_quantity.series = chart_bug_quantity;
        chart_data.chart_case_pass_percent.series = chart_case_pass_percent;
        chart_data.chart_case_records_count.series = chart_case_records_count;
        chart_data.chart_plan_records_duration.series = chart_plan_records_duration;

        buildCharts();
      })
}

function resetData() {
  search_form.group_ids = [];
  search_form.create_time = [];
  search_form.plan_ids = [];
  search_form.create_time__gte = 0;
  search_form.create_time__lte = 0;

  getData();
}

function buildDate(startDate: Date | null, endDate: Date | null) {
  if (!startDate || !endDate) {
    const today = new Date()
    startDate = new Date(today.getFullYear(), today.getMonth() - 5, 1);
    endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
  } else {
    endDate = new Date(endDate.getFullYear(), endDate.getMonth() + 1, 0);
  }

  let startDay = startDate.getDate() + '';
  if (parseInt(startDay) < 10) {
    startDay = 0 + startDay;
  }

  let endDay = endDate.getDate() + '';
  if (parseInt(endDay) < 10) {
    endDay = 0 + endDay;
  }

  let startMonth = (startDate.getMonth() + 1) + '';
  if (parseInt(startMonth) < 10) {
    startMonth = 0 + startMonth;
  }

  let endMonth = (endDate.getMonth() + 1) + '';
  if (parseInt(endMonth) < 10) {
    endMonth = 0 + endMonth;
  }

  const startDateStr = startDate.getFullYear() + '-' + startMonth + '-' + startDay;
  const endDateStr = endDate.getFullYear() + '-' + endMonth + '-' + endDay;
  search_form.create_time = [startDateStr, endDateStr];
  search_form.create_time__gte = new Date(startDateStr).getTime();
  search_form.create_time__lte = new Date(endDateStr).getTime();
}
</script>

<style lang="scss" scoped>
.data-container {
  width: 100%;
  font-size: 20px;
}

.data-statistic {
  display: flex;
  height: 6em;
  justify-content: space-between;
  //margin-top: 1em;
  //margin-bottom: 1em;
  width: 100%;

}

.data-statistic .data-statistic-item {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0em 1em 1em 1em;
  border-radius: 15px;
  box-shadow: var(--el-box-shadow-light);

  &:hover {
    .data-statistic-icon-container {
      color: #fff;
    }

    .data-statistic-bug-icon {
      color: #fff;
      background: orangered;
    }

    .data-statistic-pass-icon {
      color: #fff;
      background: limegreen;
    }

    .data-statistic-count-icon {
      color: #fff;
      background: dodgerblue;
    }

    .data-statistic-duration-icon {
      color: #fff;
      background: darkorange;
    }
  }

  .data-statistic-bug-icon {
    color: orangered;
  }

  .data-statistic-pass-icon {
    color: limegreen;
  }

  .data-statistic-count-icon {
    color: dodgerblue;
  }

  .data-statistic-duration-icon {
    color: darkorange;
  }

  .data-statistic-icon {
    width: 4em;
    height: 4em;
    padding: 0.5em;
  }

}

.data-statistic .data-statistic-item .data-statistic-icon-container {
  transition: all 0.40s ease-out;
}

.data-statistic .data-statistic-item .data-statistic-content-container {
  display: flex;
  flex-direction: column;
  padding-left: 1em;
  margin-right: 1.5em;

  .data-static-item-title {
    font-size: 17px;
    font-weight: 600;
  }

  .data-static-item-content {
    margin-top: 10px;
    align-self: center;

    .data-static-item-content-value {
      font-size: 29px;
    }

    .data-statistic-bug-value {
      color: orangered !important;
    }

    .data-statistic-pass-value {
      color: limegreen !important;
    }

    .data-statistic-count-value {
      color: dodgerblue !important;
    }

    .data-statistic-duration-value {
      color: darkorange !important;
    }

    .data-static-item-content-suffix {
      font-size: 15px;
    }
  }
}

.data-chart {
  display: flex;
  flex-direction: column;

  .data-chart-line {
    display: flex;
    height: 20em;
    justify-content: space-between;

    .data-chart-item {
      flex: 0 0 47%;
      border-radius: 15px;
      box-shadow: var(--el-box-shadow-light);
      margin: 1em;
      padding-top: 0.7em;
    }
  }
}
</style>