# 学生校内双证管理系统

基于 Flask + PostgreSQL + Bootstrap 5 的学生证书考试全生命周期管理平台，集成 AI 智能审核与知识库引导机器人。

## 技术栈

### 后端
- **Python 3.10+** / **Flask** — Web 框架
- **SQLAlchemy** — ORM 数据库操作
- **Flask-JWT-Extended** — JWT 身份认证
- **PostgreSQL** — 生产数据库（开发默认 SQLite 回退）
- **psycopg2-binary** — PostgreSQL 驱动
- **Werkzeug** — 密码加密与 WSGI

### 前端
- **Bootstrap 5** — UI 框架与响应式布局
- **ECharts 5** — 数据可视化图表（仪表盘、数据大屏）
- **原生 JavaScript** — 前端交互逻辑

### 扩展 API 与服务
- **AI 审核 API**（OpenAI 兼容接口）— 接入大语言模型自动审核报名材料，未配置时使用差异化模拟审核
- **Pollinations AI** — 学生头像自动生成
- **腾讯云 SMS SDK** — 短信通知服务（签名审核通过后可切换真实发送）
- **AI 知识库引导机器人** — 基于证书考试规则知识库的智能问答，关键词匹配 + 意图识别

## 功能模块

### 管理员端

| 功能 | 说明 |
|------|------|
| 管理仪表盘 | 统计卡片（证书/考试/报名/通过率）+ 报名趋势图 + 分类分布图 |
| 证书管理 | 证书类型 CRUD，支持人社类/专业类/校内引进三大分类 |
| 考试管理 | 考试安排、报名时间段、容量控制、费用设置 |
| 审核中心 | AI 自动审核 + 人工审核队列，支持通过/拒绝/要求补充，异步执行 |
| 数据大屏 | 全屏 ECharts 可视化，一屏展示关键业务指标，支持全屏切换 |

### 学生端

| 功能 | 说明 |
|------|------|
| 学生仪表盘 | 个人统计（报名数/通过数/待审核/证书数）+ 最近报名记录 |
| 证书浏览 | 按分类展示（全部/人社类/专业类/校内引进），卡片式布局 |
| 考试报名 | 浏览可报名考试，已报名显示灰色禁用按钮，重复报名提示 |
| AI 引导机器人 | 右下角浮动聊天窗口，基于知识库回答证书考试相关问题 |

### 系统功能

| 功能 | 说明 |
|------|------|
| JWT 认证 | 管理员/学生双角色登录，中文错误提示 |
| 批量导入 | Excel/CSV 导入学生、成绩、证书记录 |
| 材料归档 | 按考试/班级目录结构自动归档 |
| 培训材料 | 管理端上传，学生端查看 |
| 短信通知 | 腾讯云 SMS 结构，模拟发送模式 |
| 教务对接 | 外部 API + API Key 鉴权 |
| 证书推荐 | 基于专业+年级规则引擎 |
| 操作日志 | 审计追踪，自动记录关键操作 |

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/Nagato-YUKI/dual-cert-system.git
cd dual-cert-system
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，并填写必要配置：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# 安全配置（必填）
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# 数据库（默认使用 SQLite，生产建议 PostgreSQL）
# DATABASE_URL=postgresql://user:password@localhost:5432/dual_cert_db

# AI 审核 API（可选，未配置则使用模拟审核）
AI_API_KEY=your-ai-api-key
AI_API_BASE=https://api.openai.com/v1
AI_MODEL=gpt-3.5-turbo
```

### 4. 初始化数据库

```bash
# 使用 PostgreSQL 时先创建数据库
# createdb dual_cert_db

# 生成模拟数据
python seed_real_data.py
```

### 5. 启动应用

```bash
python app.py
```

访问 http://localhost:5000

### 6. 默认账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 管理员 | admin | admin123 |
| 学生 | 学号（如 20240001） | 身份证后6位（如 010001） |

## 项目结构

```
.
├── app/
│   ├── __init__.py              # 应用工厂与蓝图注册
│   ├── models/                  # 数据库模型
│   │   ├── user.py              # 管理员用户
│   │   ├── student.py           # 学生信息
│   │   ├── cert_type.py         # 证书类型
│   │   ├── exam.py              # 考试安排
│   │   ├── registration.py      # 报名记录
│   │   ├── registration_rule.py # 报名规则
│   │   ├── certificate_record.py# 证书记录
│   │   ├── class_.py            # 班级信息
│   │   ├── training_material.py # 培训材料
│   │   ├── review_log.py        # 审核日志
│   │   └── operation_log.py     # 操作日志
│   ├── routes/                  # API 路由
│   │   ├── auth.py              # 认证接口
│   │   ├── admin.py             # 管理员接口
│   │   ├── student.py           # 学生接口
│   │   ├── api.py               # AI 聊天接口
│   │   ├── review.py            # 审核接口
│   │   └── views.py             # 页面路由
│   ├── services/                # 业务服务
│   │   ├── ai_review.py         # AI 审核服务
│   │   ├── sms_service.py       # 短信通知服务
│   │   ├── import_service.py    # 批量导入服务
│   │   ├── archive_service.py   # 材料归档服务
│   │   └── audit_service.py     # 审计日志服务
│   ├── static/
│   │   ├── css/                 # 样式文件
│   │   ├── js/main.js           # 全局 JS（状态映射、API 请求）
│   │   └── data/knowledge_base.json  # AI 知识库数据
│   └── templates/               # Jinja2 HTML 模板
│       ├── base.html            # 基础布局（含 AI 聊天组件）
│       ├── login.html           # 登录页面
│       ├── admin/               # 管理员页面
│       └── student/             # 学生页面
├── app.py                       # 应用入口
├── config.py                    # 配置文件
├── seed_real_data.py            # 模拟数据生成脚本
├── requirements.txt             # 依赖列表
├── .env.example                 # 环境变量模板
└── README.md
```

## 迭代记录

### V1 — 基础框架（2026-06-06）
- Flask 应用工厂 + SQLAlchemy 数据库模型
- JWT 双角色认证（管理员/学生）
- 证书类型 CRUD + 考试管理 + 学生报名
- AI 审核集成（LLM API）
- 人工审核队列
- 批量导入 + 材料归档
- 管理仪表盘 + 学生仪表盘

### V2 — 拓展功能（2026-06-06）
- 短信通知（腾讯云 SMS SDK）
- 教务系统对接（外部 API）
- 证书推荐引擎（专业+年级规则）
- 数据大屏（全屏 ECharts 可视化）
- 操作日志审计

### V3 — 数据库迁移与 UI 重构（2026-06-07）
- 数据库从 SQLite 迁移到 PostgreSQL
- UI 全面重构（Bootstrap 5 响应式布局）
- 安全加固（.env 配置、默认值回退）
- API 路由与页面路由冲突修复

### V4 — 用户体验增强（2026-06-07）
- 登录错误提示中文化
- 全局状态标签统一中文映射（18种状态）
- AI 审核优化：差异化模拟结果 + 异步执行 + 前端轮询
- 证书分类对齐（人社类/专业类/校内引进）+ Tab 切换
- 报名按钮状态反馈（已报名灰色禁用 + 重复报名提示）
- 模拟数据完善（真实姓名、报名规则、培训材料、AI 审核结果）
- AI 知识库引导机器人（11种证书知识库 + 智能问答）
- 数据大屏增加退出按钮 + 不可滚动 + 一屏布局

## 证书知识库覆盖

| 分类 | 证书 |
|------|------|
| 人社类 | CET-4、CET-6、普通话水平测试 |
| 专业类 | 计算机二级 Python、计算机二级 MS Office、教师资格证、会计初级 |
| 校内引进 | 办公软件应用、网页设计、数据库管理、创新创业 |

## License

MIT
