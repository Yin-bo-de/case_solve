# 福尔摩斯式探案游戏

AI驱动的福尔摩斯式探案游戏 - 用户以侦探视角参与，所有嫌疑人由AI扮演，华生NPC全程陪伴，在维多利亚时代的迷雾伦敦中体验演绎推理乐趣。

## 项目结构

```
.
├── backend/              # FastAPI 后端服务
│   ├── app/
│   │   ├── agents/           # LangChain Agents
│   │   ├── models/           # 数据模型
│   │   ├── routers/          # API 路由
│   │   ├── services/         # 业务服务
│   │   ├── config.py         # 配置管理
│   │   └── main.py           # 应用入口
│   ├── Dockerfile            # 后端容器镜像
│   ├── .dockerignore         # Docker 构建排除文件
│   └── requirements.txt      # Python 依赖
├── frontend/             # React + Vite 前端应用
│   ├── src/
│   │   ├── components/       # UI 组件
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API 服务
│   │   ├── store/            # Zustand 状态管理
│   │   ├── types/            # TypeScript 类型定义
│   │   └── main.tsx
│   ├── Dockerfile            # 前端容器镜像（多阶段构建）
│   ├── nginx.conf            # Nginx 生产配置
│   ├── .dockerignore         # Docker 构建排除文件
│   └── package.json
├── docker-compose.yml        # Docker 开发环境编排
├── docker-compose.prod.yml   # Docker 生产环境编排
├── .env.example              # 环境变量模板
└── ralph/                    # Ralph Agent 配置
```

## 快速开始

### 方式一：Docker 一键部署（推荐）

#### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

#### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 OpenAI API Key
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
# OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，使用第三方代理时修改
```

#### 2. 开发环境启动

```bash
# 构建并启动（支持热重载）
docker compose up --build

# 后台运行
docker compose up -d --build

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 停止服务
docker compose down
```

**访问地址：**
- 前端页面: http://localhost
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

#### 3. 生产环境部署

```bash
# 使用生产环境配置
docker compose -f docker-compose.prod.yml up -d --build

# 查看服务健康状态
docker compose -f docker-compose.prod.yml ps

# 查看后端健康检查日志
docker compose -f docker-compose.prod.yml logs -f backend

# 停止生产服务
docker compose -f docker-compose.prod.yml down
```

**生产环境特性：**
- 后端无 `--reload`，使用生产级启动
- 后端增加健康检查（每 30s 检测 `/health`）
- 容器资源限制（后端：1 CPU / 512MB；前端：0.5 CPU / 128MB）
- 不挂载代码卷，确保运行时环境稳定

---

### 方式二：本地手动启动

#### 前置要求

- Python 3.11+
- Node.js 18+
- pip3 (Python 包管理)
- npm 或 yarn

#### 后端设置

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API Key

pip3 install -r requirements.txt
uvicorn app.main:app --reload
```

#### 前端设置

**开发模式：**

```bash
cd frontend
cp .env.example .env

npm install
npm run dev
```

**生产构建：**

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本（输出到 dist/ 目录）
npm run build

# 预览生产构建
npm run preview

# 使用任意静态文件服务器部署 dist/ 目录
# 例如使用 npx serve
npx serve dist
```

**前端环境变量说明：**

前端 `.env` 文件支持以下变量：

```bash
# API 基础地址（开发环境）
VITE_API_BASE_URL=http://localhost:8000
```

- 开发模式：`npm run dev` 会自动读取 `.env` 中的 `VITE_API_BASE_URL`
- Docker 环境：通过 `docker-compose.yml`（或新版 `compose.yml`）注入环境变量，前端通过 Nginx 反向代理访问后端
- 生产部署：如前端和后端分离部署，需将 `VITE_API_BASE_URL` 指向实际后端地址

---

## 开发指南

详见 [【PRD】福尔摩斯式探案游戏 产品文档.md](./【PRD】福尔摩斯式探案游戏%20产品文档.md)
