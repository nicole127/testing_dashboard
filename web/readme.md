# project
基于Django + Django-rest-framework 实现的Web 后台
* api: DRF
* 认证: drf-simple-jwt
* 查询: django-filters
* 数据库: mysqlclient
* 定时任务: django-apscheduler
* web 服务器: uwsgi

## 部署
### 创建数据库
```sql
CREATE DATABASE regression_testing CHARACTER SET utf8mb4;
```

### 初始化项目
```shell
# 进入后台代码根目录
cd web
# 创建虚拟环境
python -m venv venv
# 激活虚拟环境
source venv/bin/activate
# 安装依赖
pip install -r requirements.txt
```

### 初始化数据库
django 迁移
```shell
# 进入后台代码根目录
cd web
# 激活虚拟环境
source venv/bin/activate
# django 迁移
python manage.py makemigrations
python manage.py migrate
```

### 启动项目
```shell
# 进入后台代码根目录
cd web
# 激活虚拟环境
source venv/bin/activate
# 启动项目
python manage.py runserver
# 生产环境启动项目(uwsgi)
uwsgi --ini uwsgi.ini
# 重启项目
uwsgi --reload ./logs/dashboard-master.pid
# 停止项目
uwsgi --stop ./logs/dashboard-master.pid
```
