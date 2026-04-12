# 福尔摩斯式探案游戏

AI驱动的福尔摩斯式探案游戏 - 用户以侦探视角参与，所有嫌疑人由AI扮演，华生NPC全程陪伴，在维多利亚时代的迷雾伦敦中体验演绎推理乐趣。

## 项目结构

```
.
├── backend/          # FastAPI 后端服务
│   ├── app/
│   │   ├── agents/       # LangChain Agents
│   │   ├── models/       # 数据模型
│   │   ├── routers/      # API 路由
│   │   ├── services/     # 业务服务
│   │   ├── config.py     # 配置管理
│   │   └── main.py       # 应用入口
│   └── pyproject.toml
├── frontend/         # React + Vite 前端应用
│   ├── src/
│   │   ├── components/   # UI 组件
│   │   ├── pages/        # 页面组件
│   │   ├── services/     # API 服务
│   │   ├── store/        # Zustand 状态管理
│   │   ├── types/        # TypeScript 类型定义
│   │   └── main.tsx
│   └── package.json
└── ralph/            # Ralph Agent 配置
```

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- pip3 (Python 包管理)
- npm 或 yarn

### 后端设置

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API Key

pip3 install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端设置

```bash
cd frontend
cp .env.example .env

npm install
npm run dev
```

## 开发指南

详见 [【PRD】福尔摩斯式探案游戏 产品文档.md](./【PRD】福尔摩斯式探案游戏%20产品文档.md)
