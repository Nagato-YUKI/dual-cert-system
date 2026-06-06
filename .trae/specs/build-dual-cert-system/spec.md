# 学生校内双证管理系统 Spec

## Why
根据福软教师实战班第二阶段考核要求，需开发一个管理学生在校期间"人社证书"和"专业证书"全生命周期的Web系统。核心痛点是：当前学校缺乏统一平台管理证书考试报名、审核、归档及信息公开。

## What Changes
- 搭建 Flask + SQLAlchemy + 原生前端 的完整Web应用
- 实现管理端：证书/考试CRUD、AI+人工审核、批量导入、材料归档、数据统计
- 实现学生端：证书浏览、在线报名、进度查询、培训材料查看
- 基础框架完成后作为V1提交GitHub，再迭代拓展功能

## Impact
- 新增完整项目代码库
- 需要SQLite数据库文件和uploads上传目录
- 需要配置AI审核API密钥（环境变量）

## ADDED Requirements

### Requirement: 基础框架（V1 核心）
The system SHALL provide a runnable web application with:

#### Scenario: 项目脚手架
- **WHEN** 开发者启动应用
- **THEN** Flask服务正常运行，数据库自动初始化，静态资源可访问

#### Scenario: 认证模块
- **WHEN** 管理员/学生登录
- **THEN** JWT Token签发，角色区分（admin/student），受保护路由生效

#### Scenario: 证书与考试管理
- **WHEN** 管理员操作
- **THEN** 可完成证书类型（人社/专业/校内引进）和考试安排的增删改查

#### Scenario: 学生报名
- **WHEN** 学生浏览可报名考试并提交报名
- **THEN** 系统校验唯一性，保存报名记录，状态为pending

#### Scenario: 审核流程
- **WHEN** 报名提交后
- **THEN** 触发AI自动审核（LLM API），返回评分和结果；低分进入人工审核队列

#### Scenario: 材料归档
- **WHEN** 考试结束且审核通过
- **THEN** 系统按"年级/班级/考试"目录结构自动归档学生材料

#### Scenario: 批量导入
- **WHEN** 管理员上传Excel/CSV
- **THEN** 系统校验、预览、导入学生/成绩/证书记录，返回成功/失败明细

#### Scenario: 信息公开
- **WHEN** 学生访问公开页面
- **THEN** 可查看证书介绍、考试安排、报名规则、培训材料

#### Scenario: 数据统计仪表盘
- **WHEN** 管理员访问首页
- **THEN** 展示证书总数、考试场次、报名人数趋势、通过率等图表

### Requirement: 拓展功能（V2 迭代）
The system SHALL support the following enhancements:

#### Scenario: 短信通知
- **WHEN** 报名成功/审核结果变更/考试提醒
- **THEN** 调用短信API发送通知（需用户配置阿里云/腾讯云短信API Key）

#### Scenario: 教务系统对接
- **WHEN** 系统需要同步学生数据
- **THEN** 提供RESTful外部API，支持学生信息和证书记录的查询与同步

#### Scenario: 证书推荐
- **WHEN** 学生查看证书列表
- **THEN** 根据专业、年级智能推荐适合的证书（基于规则引擎）

#### Scenario: 数据大屏
- **WHEN** 管理员访问大屏页面
- **THEN** 展示实时统计数据的可视化大屏（ECharts全屏适配）

#### Scenario: 操作日志
- **WHEN** 关键操作发生
- **THEN** 记录操作人、时间、内容，支持审计追踪

## MODIFIED Requirements
无（新建项目）

## REMOVED Requirements
无