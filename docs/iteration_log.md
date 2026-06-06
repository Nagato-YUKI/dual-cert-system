# 学生校内双证管理系统 — 迭代记录

---

## V1 基础框架

**版本日期**：2026-06-06
**版本目标**：搭建系统核心架构，实现证书管理、考试管理、学生报名、AI审核等基础功能闭环

### 新增功能

#### 1. Flask 应用工厂 + SQLAlchemy 数据库模型

- 采用 Flask 应用工厂模式（`create_app`），支持多配置环境切换
- SQLAlchemy ORM 定义 11 个核心数据模型：User、Student、Class、CertType、RegistrationRule、Exam、Registration、ReviewLog、CertificateRecord、TrainingMaterial、OperationLog
- Blueprint 路由分模块注册：auth、admin、student、review、api、views
- 数据库自动建表 + 默认管理员账号初始化

#### 2. JWT 双角色认证

- 基于 Flask-JWT-Extended 实现 Token 认证
- 支持 admin / student 双角色权限隔离
- 登录接口返回 JWT Token，后续请求携带 Token 鉴权
- 默认管理员账号：admin / admin123

#### 3. 证书类型 CRUD + 考试管理 + 学生报名

- **证书类型管理**：管理员可增删改查证书类型，支持分类（人社类/专业类/校内引进）、报名条件、考试科目、费用等字段
- **考试管理**：管理员可发布考试计划，关联证书类型，设置考试时间、地点、名额限制
- **学生报名**：学生端浏览考试列表，选择考试提交报名，填写报名信息并上传材料

#### 4. AI 审核集成

- 集成 OpenAI 兼容 LLM API，对报名信息进行智能审核
- 审核维度：学生信息完整性、报名条件匹配、材料齐全性、重复报名检测
- 返回结构化审核结果：result（approved/rejected/need_more_info）、score（0-100）、reason、issues
- 支持 Mock 模式：未配置 API Key 时自动降级为模拟审核

#### 5. 人工审核队列

- AI 审核结果为 need_more_info 或 rejected 的报名进入人工审核队列
- 管理员可逐条查看审核详情，执行通过/拒绝操作
- 审核操作记录 ReviewLog，包含审核人、审核时间、审核意见

#### 6. 批量导入 + 材料归档

- 基于 openpyxl / pandas 实现 Excel 批量导入学生信息和报名数据
- 文件上传限制 16MB，上传目录自动创建
- 报名材料上传后归档至 `static/uploads/` 目录

#### 7. 管理仪表盘 + 学生仪表盘

- **管理仪表盘**：证书总数、考试数量、待审核报名数、报名趋势等概览
- **学生仪表盘**：已报名考试、审核状态、历史记录等个人概览

### 技术栈

Flask + Flask-SQLAlchemy + Flask-JWT-Extended + Flask-CORS + SQLite + openpyxl + pandas

---

## V2 拓展功能

**版本日期**：2026-06-06
**版本目标**：在基础框架上拓展通知、推荐、数据可视化等增值功能

### 新增功能

#### 1. 短信通知（阿里云 SMS SDK）

- 集成阿里云 Dysmsapi SDK（`alibabacloud_dysmsapi20170525`）
- 支持审核结果通知和考试提醒两类短信场景
- `notify_registration_status()`：通知学生审核结果
- `notify_exam_reminder()`：考试前提醒学生考试时间、地点
- Mock 模式支持：`SMS_MOCK_MODE=true` 或未配置签名/模板时自动降级为控制台日志输出
- 环境变量管理：`ALIBABA_ACCESS_KEY_ID`、`ALIBABA_ACCESS_KEY_SECRET`、`ALIBABA_SMS_SIGN_NAME`、`ALIBABA_SMS_TEMPLATE_CODE`

#### 2. 教务系统对接

- 预留教务系统数据对接接口
- 支持从教务系统同步学生基本信息、班级数据
- 数据格式适配层，兼容不同教务系统数据结构

#### 3. 证书推荐引擎

- 基于学生专业、年级、已获证书等信息，推荐适合报考的证书
- 推荐逻辑：专业匹配 → 前置证书检查 → 报名条件筛选
- 在学生端证书浏览页面展示个性化推荐

#### 4. 数据大屏

- 基于 ECharts 实现管理端数据可视化大屏
- 图表包括：
  - 证书报考人数统计（柱状图）
  - 报名趋势折线图
  - 审核通过率饼图
  - 各证书分类占比
  - 实时数据刷新

#### 5. 操作日志审计

- OperationLog 模型记录管理员关键操作
- 记录字段：操作人、操作类型、操作对象、操作时间、IP 地址
- 支持按时间范围、操作类型查询审计日志

### 技术栈变更

新增：alibabacloud_dysmsapi20170525、alibabacloud_tea_openapi、alibabacloud_tea_util、ECharts

---

## V3 数据库迁移与UI重构

**版本日期**：2026-06-07
**版本目标**：完成生产级数据库迁移，重构前端为响应式布局，修复已知问题

### 变更内容

#### 1. SQLite → PostgreSQL 迁移

- 数据库从 SQLite 迁移至 PostgreSQL，支持生产级并发访问
- 新增 `psycopg2-binary` 依赖
- 数据库连接通过环境变量 `DATABASE_URL` 配置
- 保留 SQLite 作为开发环境默认数据库（未配置 `DATABASE_URL` 时自动降级）
- 迁移脚本执行数据库建表和种子数据导入

#### 2. Bootstrap 5 响应式布局

- 前端框架从基础 HTML 升级为 Bootstrap 5
- 实现响应式布局，适配桌面端和平板端
- 统一页面模板结构：`base.html` 基础布局 + 各模块子模板
- 管理端页面：dashboard、certificates、exams、reviews、bigscreen
- 学生端页面：dashboard、certificates、exams
- 登录页面：居中卡片式布局

#### 3. 安全加固

- 密码存储使用 Werkzeug `generate_password_hash` 哈希加密
- 敏感配置项通过环境变量管理（`.env` 文件 + `python-dotenv`）
- `Config.validate()` 方法校验必需配置项
- JWT Secret Key 独立配置，与 Flask Secret Key 分离
- 文件上传目录安全隔离

#### 4. API 路由冲突修复

- 修复 `review_bp` 与 `admin_bp` 的 URL 前缀冲突问题
- review 路由合并至 admin_bp，避免 `/admin` 前缀重复注册
- Blueprint 注册顺序调整：views_bp 优先注册，确保页面路由不被 API 路由覆盖

### 技术栈变更

新增：psycopg2-binary、Bootstrap 5
移除：基础 HTML/CSS 内联样式

---

## V4 用户体验增强

**版本日期**：2026-06-07
**版本目标**：全面优化用户体验，完善 AI 功能，提升系统完成度

### 变更内容

#### 1. 登录错误提示中文化 + 内联显示

- 登录错误信息从英文改为中文提示（如"用户名或密码错误"）
- 错误提示从 alert 弹窗改为页面内联显示，提升用户体验
- 登录表单增加输入校验和实时反馈

#### 2. 全局状态标签统一中文映射

- 所有状态字段统一中文映射：
  - `pending` → 待审核
  - `approved` → 已通过
  - `rejected` → 已拒绝
  - `need_more_info` → 需补充材料
- 状态标签使用 Bootstrap Badge 组件，不同状态对应不同颜色

#### 3. AI 审核差异化 + 异步执行

- Mock 模式审核结果差异化：根据是否提交材料生成不同的审核结果
  - 有材料：60% 通过、25% 通过（低分）、15% 需补充
  - 无材料：50% 需补充、30% 拒绝、20% 通过
- 审核理由和问题列表随机化，模拟真实审核场景
- AI 审核改为异步执行，避免阻塞页面响应

#### 4. 证书分类对齐 + Tab 切换

- 证书浏览页面按分类（人社类/专业类/校内引进）Tab 切换展示
- 证书分类与知识库数据对齐，确保前后端分类一致
- Tab 切换无刷新，使用 Bootstrap Tab 组件

#### 5. 报名按钮状态反馈

- 报名按钮根据考试状态和报名情况动态显示：
  - 可报名 → 蓝色"立即报名"按钮
  - 已报名 → 灰色"已报名"按钮（不可点击）
  - 名额已满 → 红色"名额已满"按钮（不可点击）
  - 报名截止 → 灰色"已截止"按钮
- 点击报名后按钮显示 Loading 状态，提交完成后更新

#### 6. 模拟数据完善

- `seed_real_data.py` 种子数据脚本完善，覆盖全部证书类型
- 知识库 JSON 数据扩充至 11 种证书，每种证书包含完整的报考条件、考试安排、费用、科目、FAQ
- 新增通用问答（general_qa）：报名流程、费用查询、考试时间、通过标准、材料准备、有效期等

#### 7. AI 知识库引导机器人

- 基于本地 JSON 知识库的智能问答机器人
- 支持自然语言问答，关键词匹配 + 上下文理解
- 覆盖证书信息查询、报考指导、常见问题解答
- 学生端浮动按钮入口，点击展开对话窗口
- 快捷问题按钮引导用户提问

#### 8. 数据大屏优化

- 优化 ECharts 图表样式和配色方案
- 增加数据卡片展示关键指标（总报名数、通过率、待审核数等）
- 图表交互优化：悬浮提示、数据缩放、图例筛选
- 响应式适配，支持全屏展示

### 技术栈变更

新增：AI 知识库机器人（本地 JSON + 关键词匹配）
优化：ECharts 图表配置、Bootstrap Tab/Badge 组件应用

---

## 版本总览

| 版本 | 日期 | 核心变更 | 状态 |
|------|------|---------|------|
| V1 | 2026-06-06 | 基础框架搭建，核心功能闭环 | ✅ 已完成 |
| V2 | 2026-06-06 | 拓展功能（短信、推荐、大屏、审计） | ✅ 已完成 |
| V3 | 2026-06-07 | PostgreSQL 迁移 + Bootstrap 5 重构 | ✅ 已完成 |
| V4 | 2026-06-07 | 用户体验增强 + AI 知识库机器人 | ✅ 已完成 |
