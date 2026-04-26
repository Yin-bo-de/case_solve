# 福尔摩斯式探案游戏 - 项目概览

**更新日期**: 2026-04-26（完成 Agent 上下文大小管理）
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

### 总体进度: ~99% 完成（产品体验优化方案进行中：章节 8/10 完成）

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
| US-020 | 产品体验优化方案（测试与验证） | ✅ | 2026-04-19 |
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

### 待完成的用户故事 (0/21)

全部用户故事已完成！

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
│   │   │   ├── oracle_agent.py           # 裁决官（推理/指控验证）
│   │   │   ├── scene_agent.py            # 场景NPC（自然语言场景探索）
│   │   │   ├── _llm_helpers.py           # LLM调用通用封装
│   │   │   └── prompts/                 # Prompt模板集中管理
│   │   │       ├── __init__.py
│   │   │       ├── case_prompts.py       # 案件生成Prompt
│   │   │       ├── suspect_prompts.py    # 嫌疑人Prompt
│   │   │       ├── watson_prompts.py     # 华生Prompt
│   │   │       ├── oracle_prompts.py     # 裁决官Prompt
│   │   │       └── scene_prompts.py      # 场景NPC Prompt
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
│   │   │   ├── InvestigationPage.tsx     # 勘查页面（场景列表）
│   │   │   ├── ScenePage.tsx             # 场景详情页（三列布局+NPC对话）
│   │   │   ├── InterrogationPage.tsx     # 质询页面（可选中消息+华生Tips）
│   │   │   ├── DeductionBoard.tsx        # 推理板页面（Oracle验证+指认凶手）
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
│   │   │   ├── WatsonChatDialog.tsx      # 华生对话框组件
│   │   │   ├── CluePreviewModal.tsx       # 线索详情预览弹窗
│   │   │   ├── ScenePanel/               # 场景相关组件
│   │   │   │   ├── SceneChat.tsx         # 场景NPC对话聊天框
│   │   │   │   ├── SceneObjectCard.tsx   # 可交互对象卡片
│   │   │   │   └── AddClueModal.tsx      # 添加线索Modal
│   │   │   ├── SelectableMessage.tsx     # 可选中文本消息（审讯提取线索）
│   │   │   ├── ExtractClueModal.tsx      # 审讯提取线索Modal
│   │   │   ├── Toast.tsx                 # 全局轻量 Toast 提示组件
│   │   │   ├── WatsonTipsPanel.tsx       # 华生审讯实时提示面板
│   │   │   ├── ReasoningRecordCard.tsx   # 推理记录卡片（带verdict徽章）
│   │   │   ├── CombineReasoningModal.tsx # 组合推理Modal
│   │   │   └── AccusationModal.tsx       # 指认凶手Modal
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

### 2026-04-23（修复华生 Agent 线索与场景信息链路）
- ✅ **修复华生自由对话无法获取具体线索和场景信息的问题**：
  - **根因**: `WatsonChatContext` 模型只传递了统计数字（`clues_collected=3`）和 ID 列表，LLM system prompt 中完全没有注入具体的线索内容、场景列表和嫌疑人信息。导致用户问"总结线索"或"有哪些场景"时，LLM 只能凭模糊的案件概要瞎编。
  - **修复步骤1**: 扩展 `backend/app/models/game.py` 的 `WatsonChatContext`，新增 `current_clues`（已发现线索列表，含 id/label/description）、`available_scenes`（可勘查场景列表，含 id/name/description）、`suspects`（嫌疑人列表，含 id/name）三个字段。
  - **修复步骤2**: 修改 `backend/app/services/game_service.py` 的 `build_watson_chat_context()`，从 `game.case.clues` / `game.case.scenes` / `game.case.suspects` 提取具体数据填充到上述新字段。
  - **修复步骤3**: 修改 `backend/app/agents/prompts/watson_prompts.py` 的 `WATSON_CHAT_SYSTEM`，在 system prompt 中新增 `{current_clues_block}`、`{available_scenes_block}`、`{suspects_block}` 三个动态变量段，并明确要求 LLM"基于上面列出的具体信息回答，不要编造"。
  - **修复步骤4**: 修改 `backend/app/agents/watson_agent.py` 的 `_generate_response()`，将 context 中的线索、场景、嫌疑人数据格式化为 `"- 标签：描述"` 字符串块并注入 prompt 输入。
  - **验证**: 后端 `py_compile` 全绿；创建测试游戏 → 添加线索 → 调用 `/watson/chat`，华生准确总结了"酒杯指纹"和"威胁信"两条线索；询问场景时准确列出了"格雷珠宝行办公室"、"死者住所"、"印度宝石供应商办公室"三个场景。
  - **影响范围**: 仅影响 `/api/game/{game_id}/watson/chat` 自由对话体验，不影响审讯提示、矛盾检测、推理反馈等其他 API（这些接口已单独传入 `clues`/`case` 数据）。

### 2026-04-23（修复场景线索数量角标）
- ✅ **修复 cluesStore.ts mergeClues 函数** (`frontend/src/store/cluesStore.ts`):
  - 原 `mergeClues` 只追加新线索（按 id 判重），不更新已有线索
  - 当 `useGameSessionSync` revalidate 时，已有线索被跳过，无法修复内存中可能缺失的 `sourceType`/`sourceRef`
  - 改为"合并更新"模式：既添加新线索，也用后端数据更新已有线索，确保字段完整
- ✅ **验收**: `npm run typecheck` ✅ 全绿（0 错误）

### 2026-04-23（修复审讯切换嫌疑人消息错乱 + 打字动画隔离）
- ✅ **修复密室问话消息归属错乱** (`frontend/src/store/interrogationStore.ts` + `frontend/src/pages/InterrogationPage.tsx`):
  - **根因**: `addConversationMessage` 使用当前 `selectedSuspectId` 存储消息，API 异步期间用户切换嫌疑人后，响应消息被写入新嫌疑人历史
  - **修复**: `addConversationMessage`/`setConversationHistory`/`getCurrentConversationHistory`/`clearConversationHistory` 均支持传入可选 `suspectId` 参数
  - `sendPrivateQuestion` 发请求前缓存 `targetSuspectId`，后续所有消息添加、API 传参、`fetchTips` 调用均使用缓存值
  - `handleExtractConfirm` 同样缓存嫌疑人ID，避免模态框打开期间切换导致上下文错乱
- ✅ **修复打字动画未按嫌疑人隔离** (`frontend/src/pages/InterrogationPage.tsx`):
  - **根因**: `isProcessing` 是全局布尔状态，切换嫌疑人后 A 的生成动画会显示在 B 的窗口中
  - **修复**: 新增 `processingSuspectId` 状态，单独审讯时设为 `targetSuspectId`，全体质询时设为 `'group'`
  - 渲染打字动画条件改为：`isProcessing && processingSuspectId === selectedSuspect?.id`（单独）或 `=== 'group'`（全体）
- ✅ **验收**: `npm run typecheck` ✅ 全绿（0 错误）

### 2026-04-22（推理页面线索预览弹窗）
- ✅ **新增 CluePreviewModal 组件** (`frontend/src/components/CluePreviewModal.tsx`):
  - 弹窗展示线索完整详情：完整描述、线索类型（物证/证词/法医）、发现地点、来源、引用原文、发现记录
  - Meta badges：🧑 用户线索、⚠️ 可疑线索（isRedHerring 显示为"可疑线索"保持游戏悬念）
  - 复用已有 `modal-overlay`/`modal`/`modal-header`/`modal-close`/`modal-body` 样式体系
- ✅ **修改 DeductionBoard.tsx** (`frontend/src/pages/DeductionBoard.tsx`):
  - 新增 `previewedClueId` 本地 state 和 `previewedClue` 派生 memo
  - 点击线索文字区域 → 弹出 CluePreviewModal 预览详情
  - 点击复选框 ☑/☐ → 仅切换选中状态（`stopPropagation` 隔离，不影响预览）
  - 当前预览线索在列表中显示 `clue-checkbox-item--previewed` 高亮样式
- ✅ **修改 index.css** (`frontend/src/index.css`):
  - 新增 `.clue-checkbox-item--previewed` 高亮样式
  - 新增弹窗内容专属样式：`.clue-preview-modal`、字段布局、引用块、badges
- ✅ **验收**: `npm run typecheck` ✅ 全绿（0 错误）

### 2026-04-20（审讯页面聊天记录持久化修复）
- ✅ **修复 interrogationStore 聊天记录存储结构** (`frontend/src/store/interrogationStore.ts`):
  - 将 `conversationHistory: ConversationMessage[]` 改为 `conversationHistoryBySuspect: Record<string, ConversationMessage[]>`
  - 新增 `getCurrentConversationHistory: () => ConversationMessage[]` 方法
  - 修改 `addConversationMessage`/`setConversationHistory`/`clearConversationHistory` 方法，改为按嫌疑人存储
  - 修改 `clearPrivateInterrogation`/`resetAll` 方法，适配新结构
  - 修改 `persist` 配置，持久化 `conversationHistoryBySuspect`
- ✅ **修复 InterrogationPage 切换嫌疑人聊天记录丢失** (`frontend/src/pages/InterrogationPage.tsx`):
  - 从 store 中获取 `conversationHistoryBySuspect`、`selectedSuspectId`、`getCurrentConversationHistory`
  - 移除 `handleSuspectSelect` 中的 `clearConversationHistory()` 调用
  - 使用 `getCurrentConversationHistory()` 获取当前嫌疑人的对话历史
  - 修改 useEffect 依赖项，使用 `conversationHistoryBySuspect` 和 `selectedSuspectId`
- ✅ **验收**: `npm run typecheck` ✅ 全绿（0 错误）
- ✅ **效果**: 每个嫌疑人的对话记录独立存储，切换嫌疑人时保留之前的聊天记录

### 2026-04-19（场景搜查对话会话级持久化）
- ✅ **新增 sceneChatStore 状态管理** (`frontend/src/store/sceneChatStore.ts`):
  - 新增 `SceneChatMessage` 接口（`role`/`content`/`candidates`）
  - 新增 `messagesByScene` 状态（按 sceneId 存储聊天记录）
  - 新增 `addMessage`/`getMessages`/`clearScene`/`resetAll` 方法
  - 集成 `devtools` 和 `persist` 中间件
  - 使用 `createGameScopedStorage` 实现 gameId 维度的持久化
- ✅ **更新 SceneChat.tsx 使用 store**:
  - 替换 `useState<ChatMessage[]>` 为 `useSceneChatStore`
  - 使用 `getMessages(sceneId)` 获取当前场景消息
  - 使用 `addMessage(sceneId, message)` 添加消息
  - 移除本地 `ChatMessage` 接口定义
- ✅ **注册到状态管理系统**:
  - `frontend/src/store/index.ts` 导出 `useSceneChatStore` 和 `SceneChatMessage`
  - `frontend/src/store/storeManager.ts` 在 `resetAll()` 中调用 `useSceneChatStore.getState().resetAll()`
  - 在 `rehydrateGameScopedStores()` 中调用 `(useSceneChatStore as any).persist?.rehydrate?.()`
- ✅ **验收**: `npm run typecheck` ✅ 全绿（0 错误）

### 2026-04-19（添加线索成功提示）
- ✅ **新增 Toast 提示组件** (`frontend/src/components/Toast.tsx`):
  - 可复用轻量级 Toast，带淡入淡出动画，2.5 秒自动消失
  - 维多利亚哥特风格（深色背景 + 金色边框）
  - 修改 `SceneChat.tsx`：场景添加线索成功后显示"线索已成功添加！"
  - 修改 `InterrogationPage.tsx`：从审讯提取线索成功后显示"线索已成功提取！"

### 2026-04-19（状态机重构）

- ✅ **完成线索同步架构重构 Phase E（Task 15）**：
  - **Task 15**: `frontend/src/pages/StartPage.tsx` `handleStartGame` 完整替换为新游戏五步序列：`clearAllGameSessions()` 清历史 localStorage → `resetAll()` 清所有内存态 → `createNewGame(API)` 后端创建 → `setGameState()` 写入新 gameId + 分离 clues → `navigate()` 跳转；移除旧的 `setTimeout` 延迟跳转逻辑；新增 `StoreManager` 导入
  - **验收**: `npm run typecheck` ✅ 全绿（0 错误）
  - **效果**: 新游戏启动时彻底清除所有历史 `game:*` localStorage 条目，消除跨局数据污染问题

- ✅ **完成线索同步架构重构 Phase D（Task 11-14）**：
  - **Task 11**: `frontend/src/pages/InvestigationPage.tsx` 删除自定义 useEffect 加载逻辑，改用 `useGameSessionSync(gameId)`；移除 `gameApi`、`setGameState/setLoading/setError`、`useWatsonChatStore` 等仅在该 effect 内使用的导入
  - **Task 12**: `frontend/src/pages/DeductionBoard.tsx` 同模板改造；同时移除 `localGameState` 本地 state，改为直接读取 `gameStore.gameState`；`isLoading/error` 改为从 store 读取
  - **Task 13**: `frontend/src/pages/InterrogationPage.tsx` 删除"加载游戏状态"useEffect；本地 `gameState/isLoading/error` 替换为 `useGameStore()` 读取；新增 useEffect 监听 `gameState.case.suspects` 变化、首次就绪时初始化 `selectedSuspect`
  - **Task 14**: `frontend/src/pages/ScenePage.tsx` 同模板改造；`scene` 本地 state 改为 `useMemo` 派生于 `gameState.case.scenes`，消除了 `setScene` 和加载 useEffect
  - **验收**: `npm run typecheck` ✅ 全绿（0 错误）
  - **效果**: 四个页面数据加载逻辑统一收敛到 `useGameSessionSync` Hook，消除各页面独立 useEffect 拉取的不一致性

- ✅ **完成线索同步架构重构 Phase A（Task 1-3）**：
  - **Task 1**: 新建 `frontend/src/store/gameScopedStorage.ts`，实现 `createGameScopedStorage(storeName)` Zustand StateStorage 适配器，localStorage key 格式为 `game:${activeGameId}:${storeName}`；无 activeGameId 时读写 no-op，避免产生无主数据；导出 `GAME_SCOPED_STORAGE_PREFIX` 常量供 StoreManager 使用
  - **Task 2**: 扩展 `frontend/src/store/storeManager.ts`，新增三个静态方法：`clearAllGameSessions(exceptGameId?)` 批量删除 `game:*` 前缀 localStorage 条目、`clearInMemoryGameScopedStores()` 清空 game-scoped store 内存态、`rehydrateGameScopedStores()` 从新命名空间重新 hydrate；`resetAll` 补齐 `interrogationStore` 重置调用；`useStoreManager` hook 导出新方法
  - **Task 3**: 新建 `frontend/src/hooks/useGameSessionSync.ts`，页面级数据同步 Hook：gameId 变更时执行"清内存 → 后端拉取 → setGameState → rehydrate 新命名空间"全量同步；gameId 一致时后台 revalidate；同组件同 gameId 二次渲染不重复拉取（useRef 守卫）
  - **验收**: `npm run typecheck` ✅ 全绿

- ✅ **完成线索同步架构重构 Phase C（Task 7-10）**：
  - **Task 7**: `frontend/src/store/cluesStore.ts` persist storage 从 `createJSONStorage(() => localStorage)` 改为 `createJSONStorage(() => createGameScopedStorage('clues-store'))`；导入 `createGameScopedStorage`
  - **Task 8**: `frontend/src/store/deductionStore.ts` 同模板改造，storage 改为 `createGameScopedStorage('deduction-store')`
  - **Task 9**: `frontend/src/store/interrogationStore.ts` 同模板改造，storage 改为 `createGameScopedStorage('interrogation-store')`
  - **Task 10**: `frontend/src/store/watsonChatStore.ts` 同模板改造，storage 改为 `createGameScopedStorage('watson-chat-store')`
  - **验收**: `npm run typecheck` ✅ 全绿（0 错误）
  - **效果**: 4 个 store 的持久化数据改为按 `game:<gameId>:<storeName>` 命名空间隔离，新游戏时旧游戏数据不再污染；无 activeGameId 时读写 no-op

- ✅ **完成线索同步架构重构 Phase B（Task 4-6）**：
  - **Task 4**: `frontend/src/types/game.ts` 拆分类型：`Case` 移除 `clues` 字段，新增 `CaseDto`（继承 Case + `clues: Clue[]`）和 `GameStateDto`（`case?: CaseDto`）；`frontend/src/services/api.ts` `createNewGame`/`getGameState` 返回类型从 `GameState` 改为 `GameStateDto`
  - **Task 5**: `frontend/src/store/cluesStore.ts` 新增 `mergeClues(incoming: Clue[]): void` action（已有 id 保留本地，新 id 追加）；`frontend/src/store/gameStore.ts` `setGameState` 参数类型改为 `GameStateDto`，自动剥离 `case.clues` → `cluesStore.mergeClues`，存入 `gameState` 时 `case` 不含 `clues`
  - **Task 6**: grep 确认所有组件已使用 `useCluesStore()` 读取线索，无直接 `case.clues` 访问，TypeScript 零错误验收（`npm run typecheck` ✅）
  - **验收**: `npm run typecheck` 全绿（0 错误）

### 2026-04-19（产品体验优化）
- ✅ **完成产品体验优化方案 章节 8：测试与验证**:
  - **8.1**: `backend/tests/test_oracle_agent.py` 已存在（4 个测试用例全绿）
  - **8.2**: `backend/tests/test_scene_search.py` 已存在（4 个测试用例全绿）
  - **8.3**: 新建 `backend/tests/test_accuse_validation.py`（5 个测试用例全绿：空列表校验、超过 3 条记录校验、无效 ID 校验、wrong 记录校验）
  - **8.4**: `backend/tests/test_difficulty.py` 已扩展（章节 8.4 的 Scene 生成测试已集成，TestSceneGeneration 类 4 个用例全绿）
  - **8.5**: 前端 `npm run typecheck` ✅ 全绿（0 错误）
  - **验收**: 后端 pytest 29/30 通过（1 个预存 WatsonAgent.llm 缺陷与本次无关），前端 typecheck 通过
  - **端到端冒烟**: 需用户手工执行 13 步操作清单验证完整流程
- ✅ **完成产品体验优化方案 章节 7：前端改造（7.1→7.4 全部完成）**:
  - **7.1 类型与 API 客户端先行**:
    - `frontend/src/types/game.ts`：新增 `SceneObject`, `Scene`, `SceneSearchResponse`, `ReasoningRecord`, `WatsonTip` 5 个类型；扩展 `Clue`（+`userLabel/sourceType/sourceRef/userGenerated`）、`Case`（+`scenes`）、`Inference`（+`clueIds/verificationResult/oracleExplanation/userMarkedImportant`）
    - `frontend/src/services/api.ts`：新增 `sceneSearch`, `addClue`, `submitReasoning`, `extractClueFromInterrogation`, `getInterrogationTips` 5 个方法；改造 `makeAccusation` 接受 `reasoningRecordIds`
  - **7.2 勘查页面重构**:
    - `App.tsx` 新增路由 `/investigation/:gameId/scene/:sceneId`
    - 新建 `ScenePage.tsx`：三列布局（对象列表 / 氛围图 / NPC对话聊天）
    - 新建 `ScenePanel/SceneChat.tsx`：场景 NPC 对话，clue_candidates → AddClueModal → 调 `gameApi.addClue`
    - 新建 `ScenePanel/SceneObjectCard.tsx`、`ScenePanel/AddClueModal.tsx`
    - 改写 `InvestigationPage.tsx`：替换热区点图为 `scene-list` 卡片网格，已添加线索面板
    - `cluesStore.ts`：新增 `addClueFromBackend`（存在则更新，不存在则追加）
  - **7.3 推理板重构**:
    - `deductionStore.ts`：新增 `reasoningRecords/selectedClueIds/filter` 状态；新增 `submitReasoning/toggleClue/setFilter/markImportant/deleteRecord/accuse` actions；旧版 Inference/Hypothesis actions 完整保留（向后兼容）
    - `DeductionBoard.tsx` 完全重写：左栏线索勾选 + 右栏推理记录 + `filter-tabs` 筛选 + 指认凶手 FAB（仅在 ≥1 条 correct 记录时激活）
    - 新建 `ReasoningRecordCard.tsx`：verdict 徽章（✅/❌/⚠️）、关联线索 chip、裁决官解释、标记重要/删除
    - 新建 `CombineReasoningModal.tsx`：选中线索列表 + 结论输入框 + 提交中状态
    - 新建 `AccusationModal.tsx`：嫌疑人下拉 + 1-3 条 correct 推理记录多选
  - **7.4 审讯页面增强**:
    - 新建 `SelectableMessage.tsx`：`mouseup` 监听，选中 >5 字符时浮现"📎 生成线索" tooltip
    - 新建 `ExtractClueModal.tsx`：引用片段展示 + 命名输入
    - 新建 `WatsonTipsPanel.tsx`：展示 suggestion/contradiction/question_template 三类 tip
    - `interrogationStore.ts`：新增 `watsonTips/watsonTipsLoading/extractedClues` 状态；新增 `fetchTips/extractClue/clearWatsonTips` actions
    - `InterrogationPage.tsx`：嫌疑人消息渲染换为 `<SelectableMessage>`，每轮 `sendPrivateQuestion` 后异步调 `fetchTips`，右侧挂载 `<WatsonTipsPanel>`，页面末尾挂载 `<ExtractClueModal>`
  - **样式**：`index.css` 新增约 300 行（推理板暗色金边、场景三列布局、通用 Modal、SelectableMessage tooltip 等）
  - **验收**：`npm run typecheck` ✅ 全绿（0 错误）
- ✅ **完成产品体验优化方案 章节 6：WatsonAgent 强化**:
  - **6.1**: 扩展 `backend/app/agents/prompts/watson_prompts.py`，新增 4 个 Prompt 模板：
    - `watson_scene_hint_prompt`：场景勘查一句话建议（纯文本）
    - `watson_interrogation_tips_prompt`：审讯实时 Tips（JSON 模式，含 suggestion + contradiction 两种类型）
    - `watson_deduction_hint_prompt`：推理板关联提示（纯文本）
    - `watson_contradiction_prompt`：嫌疑人陈述矛盾检测（JSON 模式，替代关键词启发式）
  - **6.2**: 扩展 `backend/app/agents/watson_agent.py`，新增 4 个异步方法：
    - `offer_scene_hint(scene_name, recent_actions) -> str`：场景勘查建议，有 mock 降级
    - `offer_interrogation_tips(case, suspect, conversation_history, clues) -> List[Dict]`：返回 tips 数组，JSON 模式 + fallback
    - `offer_deduction_hint(clues, inferences) -> str`：推理板关联提示
    - `detect_contradictions(case, conversation_history, suspect_statements) -> List[Dict]`：基于 LLM 的矛盾检测，替代旧关键词启发式（已在章节 5.5 的 contradiction-check 端点中调用）
  - **适配说明**: 所有新方法遵循现有 `invoke_with_retry(chain, inputs, fallback_fn, parse_json)` 签名；JSON 方法使用 `parse_json=True + StrOutputParser()`
  - **验收**: `from app.agents.watson_agent import WatsonAgent` 4 个新方法全部注册，pytest 24/25 通过（1 个预存 WatsonAgent.llm 缺陷与本次改动无关）
- ✅ **完成产品体验优化方案 章节 5：后端 API 新增与改造**:
  - **5.1**: 在 `backend/app/routers/game.py` 新增 5 个 Request 模型：`SceneSearchRequest`、`AddClueRequest`、`SubmitReasoningRequest`、`ExtractClueFromInterrogationRequest`、`WatsonInterrogationTipsRequest`
  - **5.2**: 改造 `MakeAccusationRequest`，增加必填 `reasoning_record_ids: List[str]`，保留 `reasoning_steps` 兼容旧字段
  - **5.3**: 新增 5 个 API 端点：
    - `POST /{game_id}/scene/{scene_id}/search`（场景 NPC 自然语言搜查，调用 SceneAgent）
    - `POST /{game_id}/clues`（添加用户自定义命名线索）
    - `POST /{game_id}/deduction/reasoning`（核心：选取线索+结论 → OracleAgent 验证 → 持久化 Inference）
    - `POST /{game_id}/interrogation/extract-clue`（从审讯片段生成线索）
    - `POST /{game_id}/interrogation/watson-tips`（华生审讯实时提示）
  - **5.4**: 改造 `make_accusation` 端点：接入 OracleAgent，校验 1-3 条推理记录，拒绝使用被标记为 wrong 的记录
  - **5.5**: 改造 `contradiction-check` 端点：删除关键词启发式，改为调用 `WatsonAgent.detect_contradictions`（该方法在章节 6 实现）
  - **game_service.py** 新增 3 个方法：`add_user_clue`、`update_inference`、`record_accusation`
  - **验收**: 全部模块导入成功，24/25 测试通过（1 个预存 WatsonAgent.llm 缺陷与本次无关），5 个新端点正确注册
- ✅ **完成产品体验优化方案 章节 4：CaseGeneratorAgent 升级（scenes 生成）**:
  - **4.1**: 修改 `backend/app/agents/prompts/case_prompts.py`，在 JSON Schema 追加 `scenes` 字段（含 objects 结构约束：≥3 scenes，每个 3-6 objects，非红鲱鱼线索必须被至少 1 个 object 引用）
  - **4.2**: 修改 `backend/app/agents/case_generator_agent.py`：
    - 导入 `Scene`, `SceneObject`
    - `_generate_mock_case` 构造 3 个预设 scenes（书房/客厅/厨房），每个 3 个 objects，所有线索分配到对应 objects
    - `_build_case_from_llm_output` 新增 `_parse_scenes_from_data` 解析 LLM 返回 scenes，含 fallback 降级逻辑
    - `investigation_locations` 同步为 `[s.name for s in case.scenes]`
  - **4.3**: 扩展 `backend/tests/test_difficulty.py`，新增 `TestSceneGeneration` 类（4 个用例：≥3 scenes、每 scene 3-6 objects、非红鲱鱼线索覆盖验证、investigation_locations 镜像验证），全绿
  - **验收**: 模型导入成功，`_generate_mock_case` 返回 3 scenes，每个 3 objects，非红鲱鱼线索全部被覆盖，17 个测试中 16 绿（1 个预存 WatsonAgent.llm 缺陷与本次无关）
- ✅ **完成产品体验优化方案 章节 3：新增 SceneAgent**:
  - **3.1**: 新增 `backend/app/agents/prompts/scene_prompts.py`（`SCENE_SYSTEM` + `SCENE_SEARCH_USER` 两个 Prompt 模板）
  - **3.2**: 新增 `backend/app/agents/scene_agent.py`（`SceneAgent` 类，含 `search` 异步方法及 `get_scene_agent` 单例工厂；`_format_scene` / `_format_history` / `_format_clues_for_scene` 三个辅助函数）
  - **3.3**: 新增 `backend/tests/test_scene_search.py`（4 个单测全绿：schema 验证、clue_candidates 解析、fallback 降级、历史对话截取 6 轮）
  - **适配说明**: 同章节 2，使用 `ChatPromptTemplate | ChatOpenAI | StrOutputParser` 构建 LangChain 链，适配实际 `invoke_with_retry` 签名
  - **验收**: 模块导入输出非空，4 个单测全绿
- ✅ **完成产品体验优化方案 章节 2：新增 OracleAgent**:
  - **2.1**: 新增 `backend/app/agents/prompts/oracle_prompts.py`（`ORACLE_SYSTEM` / `VERIFY_INFERENCE_USER` / `VERIFY_ACCUSATION_USER` 三个 Prompt 模板）
  - **2.2**: 新增 `backend/app/agents/oracle_agent.py`（`OracleAgent` 类，含 `verify_inference` / `verify_accusation` 两个异步方法，`get_oracle_agent` 单例工厂）
  - **2.3**: 新增 `backend/tests/test_oracle_agent.py`（4 个单测全绿：schema 验证、fallback 降级正确/错误嫌疑人、含推理记录的 accusation）
  - **适配说明**: `invoke_with_retry` 实际签名为 `(chain, inputs, fallback_fn, parse_json)`，OracleAgent 使用 `ChatPromptTemplate | ChatOpenAI | StrOutputParser` 构建 LangChain 链并适配
  - **验收**: `python -c "from app.agents.oracle_agent import get_oracle_agent; print(get_oracle_agent())"` 输出非空，4 个单测全绿
- ✅ **完成产品体验优化方案 章节 1：数据模型扩展** (`backend/app/models/case.py`):
  - **1.1**: 新增 `SceneObject` 模型（可交互场景对象，含 hidden_clue_ids 和 search_hints）
  - **1.2**: 新增 `Scene` 模型（案件场景，含 objects 列表和 npc_persona）
  - **1.3**: 扩展 `Clue` 新增字段：`user_label`、`source_type`、`source_ref`、`quoted_text`、`user_generated`（向后兼容，全部有默认值）
  - **1.4**: 扩展 `Case` 新增 `scenes: List[Scene]` 字段
  - **1.5**: 扩展 `Inference` 新增字段：`clue_ids`、`verification_result`、`oracle_explanation`、`user_marked_important`
  - **1.6**: 新增 `ReasoningRecord(Inference)` 语义别名类
  - **验收**: 模型导入全部成功，pytest 12/13 绿（1 个预存 WatsonAgent.llm 缺陷与本次改动无关）

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

### 待解决的问题
- [P2] watson-tips-panel__header的提示内容，需要重新考虑是在华生npc中还是保持单独弄一个提示组件
- 华生当前没有获取到用户在当前游戏中审讯的聊天记录（自由对话 prompt 中未注入审讯历史，未来可按需扩展）
---

## MVP版本待办事项
1. 游戏初始页面新增三个输入框和三个按钮：兑换码输入框 + 兑换码验证按钮，openai baseurl输入框 + openai apikey输入框 + 验证按钮 + 提交按钮
  1.1. 兑换码验证按钮点击后，验证兑换码是否正确，正确则将兑换码在后端映射的baseurl和apikey保存到后端数据库中，并提示用户兑换成功（一个兑换码默认使用10次）
  1.2. openai baseurl和apikey输入框，点击提交按钮后，将输入的baseurl和apikey保存到后端数据库中，并提示用户提交成功
  1.3. 验证按钮点击后，验证openai baseurl和apikey是否正确，正确则提示用户验证成功，否则提示用户验证失败并要求重新输入
2. 数据库接入（PostgreSQL + SQLAlchemy / asyncpg）—— 解决数据丢失问题
  2.1. 数据库表结构设计
  2.2. 每一个用户进入游戏后需要记录用户的openai baseurl和apikey（包括兑换码的baseurl和apikey）
  2.3. 前端新增一个存档按钮，点击存档后，需要将每一个用户的游戏数据（游戏难度、游戏时间、游戏结果、游戏内对话记录等）存储到数据库
  2.4. 前端新增一个加载按钮，点击加载存档后，需要从数据库中读取用户上一次的游戏数据并恢复到当前游戏页面
3. 兑换码功能开发
 3.1 后端
  3.1.1 增加一个验证码生成能力接口：调用接口自动生成并返回一个兑换码，该兑换码用于前端进行验证，验证后后的兑换码的使用次数为10次。 每一个兑换码都默认关联我提前配置好的openai baseurl和apikey。
  3.1.2 兑换码以本地json配置文件存储的方式记录使用次数，每次验证兑换码后，需要更新该文件中的使用次数。
  3.1.3 增加一个兑换码验证接口：调用接口时需要传递兑换码，接口对兑换码进行有效性和次数校验，如果验证通过默认将当前兑换码绑定的openai baseurl和apikey作为当前游戏使用，并返回前端验证成功。
 3.2 前端
  3.2.1 增加一个游戏登录页，页面有：兑换码输入框 + 兑换码验证按钮。点击兑换码验证按钮后，需要将输入的兑换码传递给后端进行验证，验证通过后，跳转到游戏的开始页（即难度选择页）

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
- 详细需求请查看 `scripts/ralph/prd.json`
- Git 分支: `ralph/sherlock-holmes-detective-game`
- 产品体验优化文档：AI福尔摩斯案件推理游戏产品体验优化方案.md
- 产品体验优化技术实现文档：AI福尔摩斯案件推理游戏产品体验优化方案—技术实现.md