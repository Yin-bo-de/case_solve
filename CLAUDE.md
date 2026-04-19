# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 重要提示
**请先读取 `project_overview.md` 文件**，该文件包含了完整的项目概览、目录结构、关键文件说明和最近修复记录，可以帮助您快速了解项目。 

## 项目概述

AI驱动的福尔摩斯式探案游戏 - 用户以侦探视角参与，所有嫌疑人由AI扮演，华生NPC全程陪伴，在维多利亚时代的迷雾伦敦中体验演绎推理乐趣。

## 技术架构

### 后端 (FastAPI + LangChain)
- **框架**: FastAPI 0.109+
- **Python版本**: 3.11+
- **包管理**: pip3
- **AI框架**: LangChain 0.1+
- **日志**: loguru
- **配置**: pydantic-settings

### 前端 (React + Vite)
- **框架**: React 18.2+
- **语言**: TypeScript 5.2+
- **构建工具**: Vite 5.0+
- **状态管理**: Zustand 4.4+
- **路由**: React Router 6.21+
- **HTTP客户端**: Axios 1.6+

## 项目结构

```
.
├── backend/
│   ├── app/
│   │   ├── agents/          # LangChain Agents (案件生成、嫌疑人、华生)
│   │   ├── models/          # Pydantic 数据模型
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 业务服务层
│   │   ├── config.py        # 配置管理
│   │   └── main.py          # FastAPI 应用入口
│   ├── pyproject.toml       # Poetry 依赖配置
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      # UI 组件
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API 服务
│   │   ├── store/           # Zustand 状态管理
│   │   ├── types/           # TypeScript 类型定义
│   │   └── main.tsx
│   ├── package.json
│   └── .env.example
└── scripts/ralph/            # Ralph Agent 配置
```

## 常用命令

### 后端开发

```bash
# 进入后端目录
cd backend

# 安装依赖
source venv/bin/activate
pip3 install -r requirements.txt

# 复制环境变量
cp .env.example .env
# 编辑 .env 填入 OpenAI API Key

# 启动开发服务器 (带热重载)
uvicorn app.main:app --reload

# 类型检查
mypy app/

# 代码格式化
black app/
isort app/

# 运行测试
pytest
```

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 复制环境变量
cp .env.example .env

# 启动开发服务器
npm run dev

# 类型检查
npm run typecheck

# Lint检查
npm run lint

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 核心游戏流程

1. **开局阶段** (`/` - StartPage)
   - 难度选择 (简单/经典/硬核)
   - 生成维多利亚时代案件

2. **勘查阶段** (`/investigation/:gameId` - InvestigationPage)
   - 现场勘查，收集线索
   - 观察记录系统

3. **推理阶段** (`/deduction/:gameId` - DeductionBoard)
   - 构建推理链条
   - 创建和验证假设

4. **质询阶段** (`/interrogation/:gameId` - InterrogationPage)
   - 单独审讯嫌疑人
   - 全体质询对峙

5. **结案阶段** (`/conclusion/:gameId` - ConclusionPage)
   - 指认凶手
   - 案件真相揭露

## 关键模块说明

### 后端 Agent 系统

- `case_generator_agent.py`: 生成维多利亚时代背景的完整案件
- `suspect_agent.py`: 嫌疑人对话生成、谎言检测
- `watson_agent.py`: 华生NPC - 观察伙伴、推理质疑者、提示提供者

### 前端状态管理 (Zustand Stores)

- `gameStore.ts`: 游戏核心状态 (案件、难度、阶段、错误次数)
- `cluesStore.ts`: 线索收集状态
- `deductionStore.ts`: 推理链条和假设状态
- `uiStore.ts`: UI 交互状态

### 前端日志规范

所有 store 和组件使用 console 分级日志：
- `console.debug`: 模块加载、状态初始化
- `console.info`: 状态变更、用户关键操作
- `console.warn`: 警告信息
- `console.error`: 错误信息

日志格式: `[模块名] 描述 { 数据 }`

## API 端点

所有 API 端点位于 `/api/game` 前缀下：

- `POST /new` - 创建新案件
- `GET /{gameId}` - 获取游戏状态
- `POST /{gameId}/difficulty` - 设置难度
- `POST /{gameId}/watson/observation` - 获取华生观察评论
- `POST /{gameId}/watson/hint` - 获取华生提示
- `POST /{gameId}/interrogation/question` - 向嫌疑人提问
- `POST /{gameId}/interrogation/contradiction-check` - 检测证词矛盾
- `GET /{gameId}/deduction` - 获取推理链条
- `POST /{gameId}/deduction/inference` - 创建推理
- `POST /{gameId}/deduction/hypothesis` - 创建假设
- `POST /{gameId}/deduction/hypothesis/{id}/verify` - 验证假设
- `GET /{gameId}/conclusion/readiness` - 检查结案准备状态
- `POST /{gameId}/conclusion/accuse` - 指认凶手
- `GET /{gameId}/conclusion/reveal` - 获取案件真相

## 开发注意事项

1. **环境变量**: 后端需要 `OPENAI_API_KEY`，前后端都需要各自的 `.env` 文件
2. **CORS**: 开发环境后端允许所有来源，生产环境需配置具体域名
3. **代码风格**: 后端使用 Black + isort，前端使用 ESLint
4. **类型安全**: 前后端都使用类型注解 (Python Type Hints / TypeScript)
5. **日志记录**: 关键操作必须记录日志，便于调试和问题追踪

## Ralph Agent 开发流程

项目使用 Ralph 自主代理系统进行增量开发：
1. 读取 `prd.json` 中的用户故事
2. 按优先级实现未完成的故事
3. 提交前运行质量检查
4. 更新进度到 `progress.txt`


