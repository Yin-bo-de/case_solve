# 福尔摩斯式探案游戏 - 项目概览

**更新日期**: 2026-04-12
**当前分支**: ralph/sherlock-holmes-detective-game
**项目状态**: 开发中

---

## 项目概述

AI驱动的福尔摩斯式探案游戏 - 用户以侦探视角参与，所有嫌疑人由AI扮演，华生NPC全程陪伴，在维多利亚时代的迷雾伦敦中体验演绎推理乐趣。

### 核心玩法
1. **开局阶段** - 贝克街221B，难度选择，案件生成
2. **勘查阶段** - 现场勘查，观察记录，线索收集
3. **推理阶段** - 构建推理链条，提出假设，验证假设
4. **质询阶段** - 单独审讯，全体质询，发现矛盾
5. **结案阶段** - 指认凶手，展示推理，揭露真相

---

## 当前进度

### 总体进度: ~85% 完成

### 已完成的用户故事 (15/21) + 额外修复

| ID | 标题 | 状态 | 完成日期 |
|----|------|------|----------|
| US-001 | 项目基础结构与配置 | ✅ | 初始提交 |
| US-002 | 设计案件数据模型 | ✅ | 2026-04-12 |
| US-003 | 实现案件生成 Agent（维多利亚版） | ✅ | 2026-04-12 |
| US-004 | 实现后端游戏服务基础 API | ✅ | 2026-04-12 |
| US-005 | 创建前端起始页面（贝克街221B） | ✅ | 2026-04-12 |
| US-006 | 实现现场勘查页面（观察记录系统） | ✅ | 2026-04-12 |
| US-007 | 实现华生 Agent 基础 | ✅ | 2026-04-12 |
| US-008 | 在勘查页面集成华生提示 | ✅ | 2026-04-12 |
| US-009 | 实现嫌疑人 Agent | ✅ | 2026-04-12 |
| US-010 | 创建单独审讯页面 | ✅ | 2026-04-12 |
| US-011 | 实现全体质询功能 | ✅ | 2026-04-12 |
| US-012 | 设计推理链条数据结构 | ✅ | 2026-04-12 |
| US-013 | 创建推理链条页面（演绎推理板） | ✅ | 2026-04-12 |
| US-014 | 实现假设验证功能 | ✅ | 2026-04-12 |
| US-015 | 创建结案阶段页面 | ✅ | 2026-04-12 |
| US-021 | 实现华生全程对话陪伴功能 | ✅ | 2026-04-12 |
| - | 修复前后端字段命名不一致 | ✅ | 2026-04-12 |
| - | 实现华生对话框可拖拽移动 | ✅ | 2026-04-12 |
| - | 修复审讯页面 lie_detection 错误 | ✅ | 2026-04-12 |

### 待完成的用户故事 (6/21)

| ID | 标题 | 优先级 | 备注 |
|----|------|--------|------|
| US-016 | 实现系统判断与反馈 | 16 | 需要后端逻辑和前端集成 |
| US-017 | 实现难度系统 | 17 | 需要影响线索明显度、华生主动性等 |
| US-018 | UI风格改造为维多利亚哥特风 | 18 | 部分已有基础样式 |
| US-019 | 实现前端 Zustand 状态管理 | 19 | 需要创建 stores（部分完成） |
| US-020 | 集成所有模块并端到端测试 | 20 | 完整流程测试 |

---

## 项目结构

```
.
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── agents/                   # LangChain Agents
│   │   │   ├── case_generator_agent.py   # 案件生成
│   │   │   ├── suspect_agent.py          # 嫌疑人对话
│   │   │   └── watson_agent.py           # 华生NPC
│   │   ├── models/                   # Pydantic 数据模型
│   │   │   ├── case.py                   # 案件、推理相关模型
│   │   │   └── game.py                   # 游戏状态模型
│   │   ├── routers/                  # API 路由
│   │   │   └── game.py                   # 游戏API端点
│   │   ├── services/                 # 业务服务
│   │   │   └── game_service.py           # 游戏核心逻辑
│   │   ├── config.py                 # 配置管理
│   │   └── main.py                   # FastAPI 入口
│   ├── requirements.txt              # pip3 依赖
│   ├── pyproject.toml                # Poetry 配置（保留）
│   └── .env.example                  # 环境变量示例
│
├── frontend/                         # React + Vite 前端
│   ├── src/
│   │   ├── hooks/                    # 自定义 Hooks
│   │   │   └── useDrag.ts               # 拖拽 Hook
│   │   ├── pages/                    # 页面组件
│   │   │   ├── StartPage.tsx             # 起始页面
│   │   │   ├── InvestigationPage.tsx     # 勘查页面
│   │   │   ├── InterrogationPage.tsx     # 质询页面
│   │   │   ├── DeductionBoard.tsx        # 推理板页面
│   │   │   └── ConclusionPage.tsx        # 结案页面
│   │   ├── store/                    # Zustand 状态管理
│   │   │   ├── index.ts                  # 导出所有 store
│   │   │   ├── gameStore.ts              # 游戏状态
│   │   │   ├── cluesStore.ts             # 线索状态
│   │   │   ├── deductionStore.ts         # 推理状态
│   │   │   ├── uiStore.ts                # UI状态
│   │   │   └── watsonChatStore.ts        # 华生对话状态
│   │   ├── components/                 # 通用组件
│   │   │   └── WatsonChatDialog.tsx      # 华生对话框组件
│   │   ├── services/                 # API 服务
│   │   │   └── api.ts                    # API 客户端（含字段转换）
│   │   ├── types/                    # TypeScript 类型
│   │   │   └── game.ts                   # 游戏类型定义
│   │   ├── App.tsx                   # 路由配置
│   │   ├── main.tsx                  # 应用入口
│   │   └── index.css                 # 全局样式（维多利亚风格）
│   ├── package.json
│   └── .env.example
│
├── scripts/ralph/                    # Ralph Agent 配置
│   ├── prd.json                      # 产品需求文档
│   ├── progress.txt                  # 开发进度日志
│   ├── CLAUDE.md                     # Ralph Agent 指令
│   └── ralph.sh                      # Ralph 启动脚本
│
├── README.md                         # 项目说明
├── CLAUDE.md                         # Claude Code 项目指南
└── project_overview.md               # 本文件 - 项目概览
```

---

## 技术架构

### 后端技术栈
- **框架**: FastAPI 0.109+
- **Python**: 3.11+
- **包管理**: pip3 (requirements.txt)
- **AI框架**: LangChain 0.1+
- **日志**: loguru
- **配置**: pydantic-settings

### 前端技术栈
- **框架**: React 18.2+
- **语言**: TypeScript 5.2+
- **构建工具**: Vite 5.0+
- **状态管理**: Zustand 4.4+
- **路由**: React Router 6.21+
- **HTTP客户端**: Axios 1.6+

### 关键设计模式
1. **Singleton Pattern**: 所有 Agent 和 Service 使用单例模式
2. **Async/Await**: 所有 Agent 方法为 async 以支持 LangChain 集成
3. **Mock 实现**: 当前所有 LLM 调用使用 mock 数据，便于开发
4. **类型安全**: 前后端都使用类型注解 (Pydantic / TypeScript)
5. **日志规范**: 后端使用 loguru，前端使用 console 分级日志
6. **字段自动转换**: API 层自动转换 snake_case ↔ camelCase

### 命名规范
- **后端**: snake_case (Python 惯例)
- **前端**: camelCase (JavaScript/TypeScript 惯例)
- **API**: snake_case (与后端一致)，通过响应拦截器自动转换

---

## 最近的关键变更

### 2026-04-12
- ✅ 完成 US-021: 华生全程对话陪伴功能 - 在所有页面集成可拖拽的华生对话框，支持自由对话、快捷提问、对话历史保持
- ✅ 完成 US-015: 结案阶段页面
- ✅ 完成 US-014: 假设验证功能
- ✅ 完成 US-013: 推理链条页面
- ✅ 完成 US-011: 全体质询功能
- ✅ 完成 US-010: 单独审讯页面
- ✅ 完成 US-009: 嫌疑人 Agent
- ✅ 将后端依赖从 Poetry 改为 pip3 (requirements.txt)
- ✅ 添加 LLM base_url 配置支持 (.env 中的 OPENAI_BASE_URL)
- ✅ **修复前后端字段命名不一致问题**: 添加响应拦截器自动转换 snake_case ↔ camelCase
- ✅ **实现华生对话框可拖拽移动**: 创建 useDrag Hook，支持鼠标/触摸事件，边界检查
- ✅ **修复审讯页面 lie_detection 错误**: 添加防御性检查，支持两种命名格式

---

## 下一步开发建议

### 优先级排序
1. **US-019**: 完善前端 Zustand 状态管理（已创建 stores，需要在页面中集成使用）
2. **US-016**: 实现系统判断与反馈（结案阶段核心逻辑）
3. **US-017**: 实现难度系统（影响游戏体验的关键）
4. **US-018**: UI风格改造（已有基础样式，可逐步完善）
5. **US-020**: 集成所有模块并端到端测试（最后验证）

### 待解决的问题
- LLM 调用目前都是 mock 实现，需要接入真实的 LangChain
- 难度系统尚未实现，目前只有基础框架
- 维多利亚哥特风 UI 需要进一步完善
- 缺少端到端测试

---

## 开发命令参考

### 后端
```bash
cd backend
pip3 install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端
```bash
cd frontend
npm install
npm run dev
npm run typecheck
npm run lint
```

### 环境变量
- 后端需要: `OPENAI_API_KEY`, `OPENAI_BASE_URL` (可选)
- 前后端都需要各自的 `.env` 文件

---

## 备注

- 本文档应在每次 significant 变更后更新
- 详细进度请查看 `scripts/ralph/progress.txt`
- 详细需求请查看 `scripts/ralph/prd.json`
- Git 分支: `ralph/sherlock-holmes-detective-game`
