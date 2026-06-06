# 学生校内双证管理系统

基于 Flask + SQLAlchemy + Bootstrap 5 的学生证书考试全生命周期管理平台。

## 功能模块

### V1 核心功能
- **认证模块**：JWT 登录，区分管理员/学生角色
- **证书管理**：证书类型（人社/专业/校内引进）CRUD
- **考试管理**：考试安排、报名时间段、容量控制
- **学生报名**：在线浏览考试、提交报名、唯一性校验
- **AI 审核**：集成 LLM API 自动审核报名信息
- **人工审核**：管理端审核队列，支持通过/拒绝/要求补充
- **批量导入**：Excel/CSV 导入学生、成绩、证书记录
- **材料归档**：按"考试/班级"目录结构自动归档
- **培训材料**：管理端上传，学生端查看公开材料
- **数据统计**：仪表盘展示证书总数、考试场次、报名趋势、通过率等图表

### V2 拓展功能（待实现）
- 短信通知（报名/审核/考试提醒）
- 教务系统对接（外部 API + API Key 鉴权）
- 证书推荐（基于专业+年级规则引擎）
- 数据大屏（全屏 ECharts 可视化）
- 操作日志（审计追踪）

## 技术栈

- **后端**：Python 3.11+, Flask, SQLAlchemy, Flask-JWT-Extended
- **前端**：Bootstrap 5, ECharts, 原生 JavaScript
- **数据库**：SQLite（开发）/ MySQL（生产）
- **部署**：Waitress WSGI 服务器

## 快速开始

### 1. 克隆仓库

```bash
git clone <仓库地址>
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
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
# AI 审核 API 配置（可选，未配置则使用模拟审核）
AI_API_KEY=your-ai-api-key
AI_API_BASE=https://api.openai.com/v1
AI_MODEL=gpt-3.5-turbo
```

### 4. 启动应用

```bash
python app.py
```

访问 http://localhost:5000

### 5. 默认账号

- **管理员**：用户名 `admin`，密码 `admin123`
- **学生**：使用学号登录，密码为身份证后 6 位

## 项目结构

```
.
├── app/
│   ├── __init__.py          # 应用工厂
│   ├── models/              # 数据库模型
│   ├── routes/              # API 路由
│   ├── services/            # 业务服务
│   ├── static/              # 静态资源
│   └── templates/           # HTML 模板
├── app.py                   # 应用入口
├── config.py                # 配置文件
├── requirements.txt         # 依赖列表
└── README.md
```

## 迭代记录

- **V1**（2026-06-06）：基础框架完成，包含核心功能模块
- **V2**（计划中）：短信通知、教务对接、证书推荐、数据大屏、操作日志
