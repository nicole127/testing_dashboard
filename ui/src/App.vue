<template>
  <el-config-provider namespace="ep" :locale="locale" size="large">
    <el-container class="main-container">
      <el-header class="main-header">
        <el-menu
            class="nav-menu"
            :default-active="$route.path"
            :collapse="appStore.collapse"
            :collapse-transition=false
            :ellipsis="false"
            mode="horizontal"
            background-color="rgb(48, 65, 86)"
            text-color="#fff"
            active-text-color="#79bbff"
            router
        >
          <el-menu-item index="/">
            <div class="logo-link">
              <img src="./assets/logo.jpg" class="logo" alt="logo">
              <h1 v-if="!appStore.collapse" class="title">回归测试</h1>
            </div>
          </el-menu-item>
          <el-menu-item index="/board">
            <el-icon>
              <DataAnalysis/>
            </el-icon>
            <template #title><span class="el-menu-item-title">数据看板</span></template>
          </el-menu-item>
          <el-menu-item index="/problem">
            <el-icon>
              <DocumentDelete/>
            </el-icon>
            <template #title><span class="el-menu-item-title">问题分析</span></template>
          </el-menu-item>
          <el-menu-item index="/task">
            <el-icon>
              <Notebook/>
            </el-icon>
            <template #title><span class="el-menu-item-title">运行记录</span></template>
          </el-menu-item>
          <el-menu-item index="/plan">
            <el-icon>
              <Calendar/>
            </el-icon>
            <template #title><span class="el-menu-item-title">测试计划</span></template>
          </el-menu-item>
          <div class="flex-grow"/>
          <el-menu-item @click="handleDropDown('contact')">
            <el-icon>
              <Message/>
            </el-icon>
            <el-text class="right-text">
              咨询反馈
            </el-text>
          </el-menu-item>
          <el-menu-item>
            <el-icon>
              <UserIcon/>
            </el-icon>
            <el-text class="right-text">
              {{ authStore.user.name }}
            </el-text>
          </el-menu-item>
        </el-menu>
      </el-header>
      <el-main class="content-container">
        <router-view class="content"/>
      </el-main>
    </el-container>
  </el-config-provider>
</template>

<script lang="ts" setup>
import {
  DataAnalysis,
  Notebook,
  Calendar,
  Message,
  DocumentDelete,
  User as UserIcon,
} from "@element-plus/icons-vue";
import {useAppStore, useAuthStore} from "~/store";
import {reactive, ref} from "vue";
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import {User} from "~/api/user";

const locale = ref(zhCn)

const appStore = useAppStore()
const authStore = useAuthStore()

function toggleSideBar() {
  appStore.handleCollapse()
}

function handleDropDown(command: string) {
  switch (command) {
    case 'contact':
      window.open(import.meta.env.VITE_CONTACT_EMAIL);
      break;
    case 'logout':
      User.doLogin()
      break;
  }
}
</script>

<style lang="scss">
#app {
  //display: flex;
  height: 100vh;
  width: 100vw;

  //flex-direction: column;
  font-size: 20px;
}

.main-header {
  width: 100%;
  //background-color: rgb(48, 65, 86)
}

a {
  text-decoration: none;
}

.main-header .logo-link {
  display: flex;
  align-items: center;

  .logo {
    width: 2em;
    height: 2em;
    //margin-left: 15px;
  }

  .title {
    margin-left: 5px;
    //color: #000;
    font-weight: 600;
    font-size: 20px;
  }
}

.ep-header {
  padding: 0 0;
}

.ep-main {
  //padding: 1em 0;
}

.main-header .nav-menu {
}

/**
导航栏右侧
 */
.main-header .nav-menu .right-text {
  font-size: 14px;
  color: white;
}

.main-header .nav-menu .el-menu-item-title {
  font-weight: 600;
}

.main-header .right-container .flex-grow {
  flex-grow: 1;
}

.content-container {
}

.content-container .content {
  flex: 1;
  //margin-left: 2em;
  //margin-right: 2em;
  .search-form {
    //width: 90%;
    //min-height: 3em;
    margin-bottom: 1em;
    margin-left: 1em;
  }

  .ep-form-item__label {
    color: #000;
    font-weight: 600;
  }

  .data-table-header {
    color: #000;
    font-weight: 600;
  }

  .table-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-left: 6px solid var(--el-color-primary);
    //margin-top: 3em;
    margin-bottom: 1em;
    margin-left: 1em;
    height: 1.5em;

    .table-name {
      font-size: 18px;
      margin-left: 0.6em;
    }

    .table-operation {
      padding: 10px;
    }
  }

  .data-table-container {
      margin-left: 0.2em;
  }

  .page_container {
    margin-top: 1em;
    float: right;
  }
}
</style>
