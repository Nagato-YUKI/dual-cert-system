# Tasks

## V1: 基础框架（先完成并推送到GitHub）

- [ ] Task 1: 项目脚手架搭建
  - [ ] SubTask 1.1: 创建项目目录结构（app/models, app/routes, app/services, app/static, app/templates, data/）
  - [ ] SubTask 1.2: 编写 requirements.txt（Flask, SQLAlchemy, Flask-JWT-Extended, openpyxl, pandas, python-dotenv, waitress）
  - [ ] SubTask 1.3: 编写 config.py（数据库配置、JWT密钥、上传路径）
  - [ ] SubTask 1.4: 编写 app/__init__.py（Flask应用工厂，注册蓝图，初始化数据库）
  - [ ] SubTask 1.5: 编写根目录 app.py（应用入口）
  - [ ] SubTask 1.6: 创建 .env.example 模板文件

- [ ] Task 2: 数据库模型创建
  - [ ] SubTask 2.1: 编写 app/models/__init__.py（统一导入）
  - [ ] SubTask 2.2: 实现 Class 模型
  - [ ] SubTask 2.3: 实现 Student 模型
  - [ ] SubTask 2.4: 实现 CertType 模型
  - [ ] SubTask 2.5: 实现 Exam 模型
  - [ ] SubTask 2.6: 实现 Registration 模型
  - [ ] SubTask 2.7: 实现 ReviewLog 模型
  - [ ] SubTask 2.8: 实现 CertificateRecord 模型
  - [ ] SubTask 2.9: 实现 TrainingMaterial 模型
  - [ ] SubTask 2.10: 实现 RegistrationRule 模型
  - [ ] SubTask 2.11: 实现 User 模型

- [ ] Task 3: 认证模块
  - [ ] SubTask 3.1: 编写 app/routes/auth.py（管理员登录、学生登录、获取当前用户）
  - [ ] SubTask 3.2: 创建 JWT 装饰器区分 admin/student 权限

- [ ] Task 4: 管理端API - 证书与考试管理
  - [ ] SubTask 4.1: 编写 app/routes/admin.py 中证书类型CRUD接口
  - [ ] SubTask 4.2: 编写考试管理CRUD接口
  - [ ] SubTask 4.3: 编写报名规则管理接口

- [ ] Task 5: 学生端API - 浏览与报名
  - [ ] SubTask 5.1: 编写 app/routes/student.py 中证书类型浏览接口
  - [ ] SubTask 5.2: 编写可报名考试列表接口
  - [ ] SubTask 5.3: 编写在线报名接口（含唯一性校验）
  - [ ] SubTask 5.4: 编写我的报名记录接口
  - [ ] SubTask 5.5: 编写我的证书获取记录接口

- [ ] Task 6: AI审核模块
  - [ ] SubTask 6.1: 编写 app/services/ai_review.py（构造Prompt，调用LLM API）
  - [ ] SubTask 6.2: 编写管理端审核接口（触发AI审核、人工审核、批量AI审核）
  - [ ] SubTask 6.3: 实现审核结果存储到 ReviewLog

- [ ] Task 7: 批量导入模块
  - [ ] SubTask 7.1: 编写 app/services/import_service.py（Excel/CSV读取、校验、处理）
  - [ ] SubTask 7.2: 编写管理端导入接口（学生/成绩/证书记录）
  - [ ] SubTask 7.3: 编写导入模板下载接口

- [ ] Task 8: 材料归档模块
  - [ ] SubTask 8.1: 编写 app/services/archive_service.py（按班级分组、创建目录、复制文件）
  - [ ] SubTask 8.2: 编写管理端归档查询和导出接口

- [ ] Task 9: 培训材料与信息公开
  - [ ] SubTask 9.1: 编写培训材料CRUD接口（管理端）
  - [ ] SubTask 9.2: 编写学生端公开材料浏览接口

- [ ] Task 10: 前端页面 - 基础框架与公共模板
  - [ ] SubTask 10.1: 编写 app/templates/base.html（Bootstrap5布局、导航栏、JWT处理）
  - [ ] SubTask 10.2: 编写登录页面（区分管理员/学生）

- [ ] Task 11: 前端页面 - 管理端
  - [ ] SubTask 11.1: 编写 admin/dashboard.html（数据统计卡片+ECharts图表）
  - [ ] SubTask 11.2: 编写 admin/certificates.html（证书类型CRUD）
  - [ ] SubTask 11.3: 编写 admin/exams.html（考试管理）
  - [ ] SubTask 11.4: 编写 admin/reviews.html（AI+人工审核界面）
  - [ ] SubTask 11.5: 编写 admin/import.html（批量导入+模板下载）
  - [ ] SubTask 11.6: 编写 admin/archive.html（按班级查看归档）
  - [ ] SubTask 11.7: 编写 admin/materials.html（培训材料管理）

- [ ] Task 12: 前端页面 - 学生端
  - [ ] SubTask 12.1: 编写 student/dashboard.html（个人概览）
  - [ ] SubTask 12.2: 编写 student/certificates.html（证书浏览）
  - [ ] SubTask 12.3: 编写 student/exams.html（考试报名）
  - [ ] SubTask 12.4: 编写 student/my_registrations.html（我的报名）
  - [ ] SubTask 12.5: 编写 student/materials.html（培训材料查看）

- [ ] Task 13: 前端JS交互
  - [ ] SubTask 13.1: 编写 static/js/main.js（通用工具：API请求封装、Token管理）
  - [ ] SubTask 13.2: 编写 static/js/admin.js（管理端各页面交互）
  - [ ] SubTask 13.3: 编写 static/js/student.js（学生端各页面交互）

- [ ] Task 14: V1 GitHub推送
  - [ ] SubTask 14.1: 编写 README.md（项目说明、技术栈、运行步骤）
  - [ ] SubTask 14.2: 创建 GitHub 仓库并通过 MCP 推送代码
  - [ ] SubTask 14.3: 验证仓库可正常访问

## V2: 拓展功能（V1完成后迭代）

- [ ] Task 15: 短信通知模块
  - [ ] SubTask 15.1: 引导用户获取阿里云/腾讯云短信API Key
  - [ ] SubTask 15.2: 编写 app/services/sms_service.py（封装短信发送）
  - [ ] SubTask 15.3: 在报名/审核/考试节点集成短信发送

- [ ] Task 16: 教务系统对接接口
  - [ ] SubTask 16.1: 编写 app/routes/api.py 外部API（学生查询、证书记录同步）
  - [ ] SubTask 16.2: 实现 API Key 鉴权

- [ ] Task 17: 证书推荐功能
  - [ ] SubTask 17.1: 编写推荐规则引擎（基于专业+年级匹配）
  - [ ] SubTask 17.2: 在学生端证书列表增加"推荐"标识

- [ ] Task 18: 数据大屏
  - [ ] SubTask 18.1: 编写 admin/bigscreen.html（全屏ECharts可视化）
  - [ ] SubTask 18.2: 编写大屏数据聚合接口

- [ ] Task 19: 操作日志
  - [ ] SubTask 19.1: 增加 OperationLog 模型
  - [ ] SubTask 19.2: 编写装饰器自动记录关键操作
  - [ ] SubTask 19.3: 管理端日志查询页面

## Task Dependencies
- Task 2 依赖 Task 1
- Task 3 依赖 Task 2
- Task 4 依赖 Task 3
- Task 5 依赖 Task 3
- Task 6 依赖 Task 4, Task 5
- Task 7 依赖 Task 2
- Task 8 依赖 Task 5, Task 6
- Task 9 依赖 Task 4
- Task 10 依赖 Task 3
- Task 11 依赖 Task 4, Task 6, Task 7, Task 8, Task 9, Task 10
- Task 12 依赖 Task 5, Task 9, Task 10
- Task 13 依赖 Task 11, Task 12
- Task 14 依赖 Task 1-13
- Task 15 依赖 Task 14
- Task 16 依赖 Task 14
- Task 17 依赖 Task 14
- Task 18 依赖 Task 14
- Task 19 依赖 Task 14