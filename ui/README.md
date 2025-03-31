# 回归测试看板

## 用法

```bash
# 安装node.js 前往官网下载安装
# 安装vite
npm i vite@latest -g
# 安装依赖
cd ui
npm i
# 启动项目
npm run dev
# 打包项目
npm run build
```

## 技术栈

| 组件                          | 版本      | 介绍                         |
|-----------------------------|---------|----------------------------|
| node                        | 18.18.2 | javascript/typescript 运行环境 |
| vite                        | 4.4.9   | 前端构建工具, 替代webpack          |
| vue                         | 3.3.4   | 前端框架                       |
| vue-router                  | 4.2.4   | 路由功能                       |
| pinia                       | 2.1.6   | 全局状态管理                     |
| pinia-plugin-persistedstate | 3.2.0   | 将全局状态持久化到localStorage      |
| element-plus                | 2.4.2   | 组件库                        |
| typescript                  | 5.2.2   | 脚本语言, 替代javascript         |
| axios                       | 1.5.0   | 网络请求                       |
| echarts                     | 5.4.3   | 报表组件库                      |

## 目录
| 目录             | 介绍                           |
|----------------|------------------------------|
| node_modules   | 依赖库, 需要删除由npm install 命令自动生成 |
| index.html     | 前端入口文件, 配置网站名称和图标            |
| package.Json   | 依赖管理文件                       |
| tsconfig.json  | ts 配置文件                      |
| vite.config.ts | vite 配置文件                    |
| vite.config.ts | vite 配置文件                    |
| api            | 网络请求                         |
| assets         | 静态资源                         |
| router         | 路由配置                         |
| store          | 全局状态库配置                      |
| styles         | 全局样式                         |
| utils          | 工具类                          |
| views          | 前端界面                         |
| App.vue        | 前端主界面                        |
| *.d.ts         | ts 类型声明                      |
| main.ts        | 全局ts                         |
