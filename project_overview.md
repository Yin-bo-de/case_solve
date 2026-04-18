# 福尔摩斯式探案游戏 - 项目概览

**更新日期**: 2026-04-18
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

### 总体进度: ~98% 完成

### 已完成的用户故事 (18/21) + 额外修复 + 技术债务清理

| ID | 标题 | 状态 | 完成日期 |
|----|------|------|----------|
| US-001 | 项目基础结构与配置 | ✅ | 初始提交 |
| US-002 | 设计案件数据模型 | ✅ | 2026-04-12 |
| US-003 | 实现案件生成生成 Agent（维多利亚版） | ✅ | 2026-04-12 |
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
| US-016 | 实现系统判断与反馈 | ✅ | 2026-04-14 |
| US-017 | 实现难度系统 | ✅ | 2026-04-17 |
| US-018 | 维多利亚哥特风 UI 精致化 | ✅ | 2026-04-18 |
| US-019 | 完善前端 Zustand 状态管理 | ✅ | 2026-04-15 |
| US-021 | 实现华生全程对话陪伴功能 | ✅ | 2026-04-12 |
| - | 修复前后端字段命名不一致 | ✅ | 2026-04-12 |
| - | 实现华生对话框可拖拽移动 | ✅ | 2026-04-12 |
| - | 修复审讯页面 lie_detection 错误 | ✅ | 2026-04-12 |
| - | 修复华生对话框输入区域不显示问题 | ✅ | 2026-04-14 |
| - | 修复华生对话框重复显示问题 | ✅ | 2026-04-14 |
| - | 完善 Zustand 状态管理（中间件、持久化、状态管理器） | ✅ | 2026-04-15 |
| - | 修复圆桌对峙输入框宽度自适应问题 | ✅ | 2026-04-15 |
| - | 实现@提及菜单键盘导航功能 | ✅ | 2026-04-15 |
| - | 修复 watsonChatStore 类型错误 | ✅ | 2026-04-18 |

### 待完成的用户故事 (2/21)

| ID | 标题 | 优先级 | 备注 |
|----|------|--------|------|
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
│   │   │   ├── watson_agent.py           # 华生NPC
│   │   │   ├── _llm_helpers.py           # LLM调用通用封装
│   │   │   └── prompts/                 # Prompt模板集中管理
│   │   │       ├── __init__.py
│   │   │       ├── case_prompts.py       # 案件生成Prompt
│   │   │       ├── suspect_prompts.py    # 嫌疑人Prompt
│   │   │       └── watson_prompts.py     # 华生Prompt
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
│   │   │   ├── watsonChatStore.ts        # 华生对话状态
│   │   │   ├── storeManager.ts           # 统一状态管理器
│   │   │   └── README.md                # 状态管理文档
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
2.**Async/Await**: 所有 Agent 方法为 async 以支持 LangChain 集成
3. **LLM 集成**: 真实 LLM 调用 + mock 降级双路径，API key 缺失时自动降级
4. **重试/超时封装**: 统一的 `invoke_with_retry` 封装，支持重试、超时、JSON 解析、降级
5. **Prompt 工程化**: Prompt 模板集中管理在 `agents/prompts/` 目录
6. **类型安全**: 前后端都使用类型注解 (Pydantic / TypeScript)
7. **日志规范**: 后端使用 loguru，前端使用 console 分级日志
8. **字段自动转换**: API 层自动转换 snake_case ↔ camelCase
9. **Zustand 中间间**: 集成 DevTools（调试）和 Persist（持久化）中间间
10. **全局状态管理**: 使用 StoreManager 统一管理所有 Store（重置、快照、恢复）

### 命名规范
- **后端**: snake_case (Python 惯例)
- **前端**: camelCase (JavaScript/TypeScript 惯例)
- **API**: snake_case (与后端一致)，通过响应拦截器自动转换

---

## 最近的关键变更

### 2026-04-18
- ✅ **完成 US-018 维多利亚哥特风 UI 精致化**:
  - **T3.1**: 新增煤气灯光晕效果和壁灯装饰（StartPage）
  - **T3.2**: 添加木质纹理和羊皮纸纹理背景（卡片、面板、文档类元素）
  - **T3.3**: 19世纪化文案润色（阁下、勘查、细查等维多利亚用语）
  - **T3.4**: 引入 Google Fonts（Cinzel 标题、IM Fell English 正文）
  - **语法修复**: 修复 watsonChatStore 类型错误（response.messageType）

### 2026-04-17
- ✅ **完成 T2 LLM真实调用集成**:
  - **T2.1**: 创建 `backend/app/agents/prompts/` 目录和三个 prompt 模板文件（`case`、`suspect`、`watson`）
  - **T2.5**: 创建 `backend/app/agents/_llm_helpers.py`，统一封装重试/超时/日志/降级逻辑
  - **T2.2**: CaseGeneratorAgent 接入真实 LLM 调用，保留 mock 降级路径
  - **T2.3**: SuspectAgent 接入真实 LLM 调用（对话、谎言检测、插话）
  - **T2.4**: WatsonAgent 接入真实 LLM 调用（观察评论、推理质疑、知识提供、假设建议）
  - **语法验证**: 所有 8 个 Python 文件通过 py_compile 验证
- ✅ **完成 US-017 难度系统**:
  - **T1.1**: 案件生成端按难度调整红鲱鱼数量（Easy=1/Classic=2/Hardcore=3）和线索 `obviousness` 范围，新增 `Clue.obviousness` 字段
  - **T1.2**: WatsonAgent 新增 `proactive_rate` 参数和 `from_difficulty()` 工厂方法（Easy=0.8/Classic=0.5/Hardcore=0.2），`share_observation`/`question_reasoning` 加入概率门控；路由层按 game.difficulty 创建对应实例
  - **T1.3**: StartPage 三个难度卡片补充量化标签（线索明显度/华生活跃度/错误机会），新增 `.difficulty-option__stats` 样式
  - **T1.4**: 新建 `backend/tests/test_difficulty.py`，13 个 pytest 用例全绿（clue 分布、max_mistakes、watson proactive_rate）

### 2026-04-15
- ✅ **完成 US-019: 完善 Zustand 状态管理** - 为所有 Store 添加 DevTools 和 Persist 中间件，实现状态持久化和调试支持
- ✅ **创建 StoreManager**: 提供统一的状态管理功能（重置、快照保存/恢复、localStorage 集成）
- ✅ **重构 WatsonChatDialog**: 使用新的状态管理，将对话框位置存储到 UIStore，解决切换页面位置丢失问题
- ✅ **消除状态重复**: 将对话框开关/展开状态从 watsonChatStore 移至 uiStore，统一管理
- ✅ **创建状态管理文档**: 添加 `frontend/src/store/README.md` 完整使用指南
- ✅ **修复 deduction 页面 footer**: 添加独立的 `deduction-footer` 样式，位置固定在左下角，背景透明
- ✅ **修复圆桌对峙输入框宽度自适应问题**: 为 `.question-input--textarea` 添加 `width: 100%` 样式
- ✅ **实现@提及菜单键盘导航功能**: 支持上下键选择方向，回车键确认选中，添加高亮样式
- ✅ **修复 InterrogationPage 模式切换状态丢失问题**: 将 conversationHistory、groupMessages、lieDetection、contradictions、mentionedSuspects 等状态从 useState 迁移至 useInterrogationStore，使用 localStorage 持久化确保切换模式时对话历史不丢失

### 2026-04-14
- ✅ **完成 US-019: 完善前端 Zustand 状态管理** - 在 InvestigationPage 和 ConclusionPage 集成使用 stores，实现跨页面状态保持
- ✅ **完成 US-016: 实现系统判断与反馈** - 验证并完善后端结案逻辑（make_accusation、get_case_reveal）和前端 ConclusionPage 完整集成（错误反馈、案件真相揭露、再玩一局功能）
- ✅ **修复华生对话框输入区域不显示问题**: 补充完整的CSS样式（输入框、发送按钮、快捷问题、错误提示等）
- ✅ **修复华生对话框重复显示问题**: 从所有页面删除旧的内联对话框实现，只保留新的 WatsonChatDialog 组件
- ✅ **修复华生对话框位置定位问题**: 给 WatsonChatDialog 添加 `watson-dialog--draggable` 类，确保 transform 定位正常工作
- ✅ **清理代码重复**: 移除 watson_agent.py 中多处重复的 `import random` 语句，统一在文件顶部导入

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
1. **US-020**: 集成所有模块并端到端测试（最后验证）

### 待解决的问题
- 无（核心功能已完成，待端到端测试）

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
