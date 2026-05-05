# 福尔摩斯式探案游戏 - 项目概览

**更新日期**: 2026-05-05（P5 案件生成强约束 完成）
**当前分支**: releaes/1.0.0_dev
**项目状态**: 开发中（探案游戏「线索被使用」核心闭环改造 P1-P5 全部完成）

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

### 总体进度: MVP 后端门控完成（兑换码功能后端 100% 完成，前端待实现）

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
│   │   │   ├── witness_agent.py          # 证人对话（新增）
│   │   │   ├── expert_agent.py           # 专家对话（新增）
│   │   │   ├── watson_agent.py           # 华生NPC
│   │   │   ├── oracle_agent.py           # 裁决官（推理/指控验证）
│   │   │   ├── scene_agent.py            # 场景NPC（自然语言场景探索）
│   │   │   ├── _llm_helpers.py           # LLM调用通用封装
│   │   │   └── prompts/                 # Prompt模板集中管理
│   │   │       ├── __init__.py
│   │   │       ├── case_prompts.py       # 案件生成Prompt
│   │   │       ├── suspect_prompts.py    # 嫌疑人Prompt
│   │   │       ├── witness_prompts.py    # 证人Prompt（新增）
│   │   │       ├── expert_prompts.py     # 专家Prompt（新增）
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
│   │   │   ├── MusicPlayer.tsx           # 全局背景音乐播放器（右下角浮窗）
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
│   ├── Dockerfile
│   ├── Caddyfile
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

### 2026-05-05（P5 — 案件生成强约束：Suspect.statements 二阶段产出 + 可解性校验 + 失败重试）

**背景**: 探案游戏「线索被使用」核心闭环改造的第五步，也是最后一步。为案件生成加入嫌疑人陈述（statements）的二阶段产出，并引入可解性强约束校验，确保每局游戏都可通过审讯中的线索对质推进。

**后端改动**
- ✅ **`backend/app/agents/prompts/case_prompts.py`**：
  - 新增 `SUSPECT_STATEMENTS_GENERATION_SYSTEM` + `SUSPECT_STATEMENTS_GENERATION_HUMAN` prompt 模板
  - 要求为每位嫌疑人设计 2-4 条陈述，输出严格 JSON（id/content/is_lie/refutable_by_clue_ids/revealed_when_broken）
  - 新增 `suspect_statements_generation_prompt` ChatPromptTemplate
- ✅ **`backend/app/agents/case_generator_agent.py`**：
  - 新增 `_generate_suspect_statements(case, difficulty)`：二阶段 LLM 调用，为每位嫌疑人生成 statements
    - 弱绑定约束校验：`refutable_by_clue_ids` 必须指向真实 clue 且 clue.related_suspect_ids 包含当前 suspect
    - 校验失败时自修复重试 1 次（prompt 追加约束提醒）
    - 重试仍失败回退 `_build_fallback_statements`
  - 新增 `_validate_solvability(case)`：4 项可解性校验
    - 至少 2 条 clue 被 statements 引用
    - 至少 1 名嫌疑人有 ≥2 条可反驳的谎言
    - 每条 statement 的 refutable_by_clue_ids 关联正确
    - 真凶至少持有 1 条可反驳的谎言
  - 新增辅助方法：`_build_clues_block`、`_build_suspects_block`、`_parse_statements_from_llm_output`、`_validate_statement_bindings`、`_build_fallback_statements`
  - 修改 `generate_case()`：三阶段流程（A 主体 → B statements → C 可解性校验）+ 整体重试最多 3 次 + 终极回退 mock case
  - 修改 `_generate_mock_case()`：调用 `_build_fallback_statements` 为 3 名嫌疑人生成符合可解性约束的 statements

**测试**
- ✅ **新建 `backend/tests/test_case_solvability.py`**：18 个 pytest 用例
  - `TestValidateSolvability`（7 个）：校验通过/失败场景（无谎言链、真凶无谎言、线索不足、弱绑定失败、开关关闭）
  - `TestStatementBindings`（4 个）：弱绑定约束校验（通过、clue 不存在、clue 未关联、空 refutable）
  - `TestFallbackStatements`（5 个）：fallback 结构正确、真凶有谎言、弱绑定有效、覆盖所有嫌疑人、满足可解性
  - `TestGenerateCaseStatements`（2 个）：mock 路径生成 case 包含 statements、满足可解性

**验收**
- `pytest tests/ -x -q` → **144 passed**（含新增 18 个可解性测试），无回归
- 前端 `npm run typecheck` → **零错误**（P5 无前端改动）
- `npm run build` → **构建成功**
- 连开 mock 案件 → 每局 `case.suspects[*].statements` 非空，真凶有 ≥2 条谎言且可被线索反驳

---

### 2026-05-05（P1 — 数据骨架：Clue/Suspect/Inference/GameState 字段扩展 + 前端类型同步）

**背景**: 探案游戏「线索被使用」核心闭环改造的第一步，为后续 P2-P5 阶段（出示线索质询、嫌疑人状态机、已验证信息门槛、案件生成强约束）打好数据层基础。

**改动**
- ✅ **扩展 `backend/app/models/case.py`**：
  - `Clue` 新增 `verification_status`（默认 "unverified"）、`verification_notes`、`verified_by`
  - 新增 `SuspectStatement` 模型（`id/content/is_lie/refutable_by_clue_ids/revealed_when_broken`，敏感字段 `exclude=True`）
  - `Suspect` 新增 `statements: List[SuspectStatement]`
  - `Inference` 新增 `node_type`（默认 "mixed"）
- ✅ **扩展 `backend/app/models/game.py`**：
  - `GameState` 新增 `suspect_states: Dict[str, str]`、`verified_clue_ids: List[str]`
- ✅ **扩展 `frontend/src/types/game.ts`**：
  - `Clue` 新增 `verificationStatus/verificationNotes/verifiedBy`
  - `Suspect` 新增 `statements?: SuspectStatement[]`
  - `ReasoningRecord` 新增 `nodeType`
  - `GameState` 新增 `suspectStates/verifiedClueIds`
- ✅ **扩展 `backend/app/config.py`**：新增 4 个 feature flag（`enable_clue_confrontation=True`、`enable_suspect_state_machine=False`、`enable_strict_oracle=False`、`enable_solvability_validation=False`）+ `strict_accusation_threshold`
- ✅ **新建 `backend/tests/test_models_backward_compat.py`**：6 个测试类，覆盖 Clue/Suspect/Inference/GameState/SuspectStatement/Case 旧 JSON 反序列化兼容

**验收**
- `pytest tests/ -x -q` → **91 passed**（含新增 11 个兼容测试），无回归
- `npm run typecheck` → **零错误**
- 所有新增字段均为 Optional + 默认值，历史 GameState 反序列化无破坏

---

### 2026-05-05（P2 — 出示线索质询 MVP：confront_with_clue 端到端闭环）

**背景**: 探案游戏「线索被使用」核心闭环改造的第二步，实现玩家可在审讯中向嫌疑人出示已发现线索，嫌疑人针对性回应，线索根据对质结果更新验证状态（unverified → verified / refuted）。

**后端改动**
- ✅ **`backend/app/agents/prompts/suspect_prompts.py`**：新增 `SUSPECT_CONFRONT_CLUE_SYSTEM` + `SUSPECT_CONFRONT_CLUE_HUMAN` prompt 模板，注入 clue/suspect/statements/在场人员信息，要求输出严格 JSON（response/relevance/statement_refuted_id/status_delta/suggested_verification）
- ✅ **`backend/app/agents/suspect_agent.py`**：新增 `confront_with_clue()` 异步方法 + `_normalize_confront_result()` 归一化函数 + `_generate_mock_confront_response()` mock 降级（related_suspect_ids 启发式：含 suspect.id→critical，空→irrelevant，其余随机 related/irrelevant）
- ✅ **`backend/app/services/game_service.py`**：新增 `update_clue_verification()` 单源更新 `Clue.verification_status` + 同步 `GameState.verified_clue_ids` 冗余索引；新增 `mark_clue_refuted()` 封装
- ✅ **`backend/app/routers/game.py`**：新增 `ConfrontWithClueRequest` 请求模型 + `POST /interrogation/confront-with-clue` 端点，handler 校验 game/case/suspect/clue → 调 SuspectAgent → 根据 suggested_verification 更新线索状态 → 返回 clue_after + conversation_message

**前端改动**
- ✅ **`frontend/src/services/api.ts`**：新增 `confrontWithClue()` API 方法
- ✅ **`frontend/src/store/interrogationStore.ts`**：新增 `confrontLoading` 状态 + `confrontSuspectWithClue()` action（先写入「出示线索」消息 → 调 API → 写入嫌疑人回应 → 同步 cluesStore.updateClue）
- ✅ **`frontend/src/pages/InterrogationPage.tsx`**：密室问话输入区新增「出示线索」按钮 → 弹出 `ClueSelectorModal` → 选中后调 `confrontSuspectWithClue`；用户消息以 `【出示线索】` 前缀渲染 `message-text--clue-confront` 金色高亮气泡
- ✅ **新建 `frontend/src/components/ClueSelectorModal.tsx`**：列出已发现线索，显示 verificationStatus 徽章（绿/灰/红），点击确认后回调
- ✅ **`frontend/src/components/CluePreviewModal.tsx`**：新增「验证状态」字段展示 + `verificationNotes` + `verifiedBy`

**样式**
- ✅ `InterrogationPage.tsx` 内联样式新增：`.confront-clue-btn`、`.message-text--clue-confront`、`.clue-selector-modal` 系列、`.clue-status-badge` 系列

**测试**
- ✅ **新建 `backend/tests/test_confront_with_clue.py`**：8 个 pytest 用例
  - `test_confront_critical`：相关线索 → critical + suggested_verification=True
  - `test_confront_irrelevant`：无关线索 → irrelevant + suggested_verification=False
  - `test_confront_result_normalization`：异常 relevance 兜底为 irrelevant
  - `test_update_clue_to_verified`：verification_status 持久化 + verified_clue_ids 同步
  - `test_update_clue_to_refuted`：refuted 后 verified_clue_ids 移除
  - `test_update_nonexistent_clue`：不存在线索返回 False
  - `test_update_clue_idempotent`：重复验证不重复追加
  - `test_confront_with_clue_endpoint`：端点集成流程

**验收**
- `pytest tests/ -x -q` → **99 passed**（含新增 8 个对质测试），无回归
- `npm run typecheck` → **零错误**
- `npm run build` → **构建成功**（130 modules）

---

### 2026-05-05（P3 — 嫌疑人状态机 + 谎言链：服务端状态迁移 + Prompt 压力指令 + 前端徽章/Toast）

**背景**: 探案游戏「线索被使用」核心闭环改造的第三步，实现嫌疑人在审讯中从 calm → pressured → broken 的三态动态变化，玩家可通过出示线索对质看到嫌疑人状态迁移和语气变化。

**后端改动**
- ✅ **`backend/app/services/game_service.py`**：
  - 新增 `_suspect_relevance_counter` 内存计数器（key 格式 `{game_id}:{suspect_id}`）
  - 新增 `transition_suspect_state(game_id, suspect_id, relevance)`：实现状态迁移规则引擎
    - `calm + critical` → `broken`
    - `calm + related`（累计≥1）→ `pressured`
    - `pressured + critical` → `broken`
    - `pressured + related` → `pressured`（保持）
    - `broken` → `broken`（终态不回退）
    - `irrelevant` 不触发任何迁移
- ✅ **`backend/app/agents/prompts/suspect_prompts.py`**：
  - `SUSPECT_RESPONSE_SYSTEM` 与 `SUSPECT_CONFRONT_CLUE_SYSTEM` 注入 `{state_directive}` 占位符
- ✅ **`backend/app/agents/suspect_agent.py`**：
  - 新增 `_STATE_DIRECTIVES` 映射表（calm/pressured/broken 三态指令文本）
  - `generate_response` 新增 `current_state` 参数，注入对应心理状态指令
  - `confront_with_clue` 新增 `current_state` 参数，注入对应心理状态指令
- ✅ **`backend/app/routers/game.py`**：
  - `POST /interrogation/confront-with-clue`：读取当前状态 → 调 SuspectAgent（带 state）→ 根据 relevance 调用 `transition_suspect_state` → 响应追加 `state_delta: {from, to}`
  - `POST /interrogation/question`：读取当前状态 → 调 `generate_response`（带 state，仅影响语气，不触发状态迁移）
  - 配置开关 `enable_suspect_state_machine` 控制：关闭时沿用 P2 LLM 返回的 `status_delta`

**前端改动**
- ✅ **`frontend/src/store/gameStore.ts`**：新增 `patchGameState(patch: Partial<GameState>)` 轻量局部更新方法
- ✅ **`frontend/src/store/interrogationStore.ts`**：
  - 新增 `suspectStates: Record<string, 'calm'|'pressured'|'broken'>` 状态
  - `confrontSuspectWithClue` 处理响应 `statusDelta`，更新本地 suspectStates 并通过 `patchGameState` 同步到 gameStore
  - `resetAll` 清空 suspectStates；`persist` 追加 suspectStates 持久化
- ✅ **`frontend/src/pages/InterrogationPage.tsx`**：
  - 嫌疑人列表项：头像旁新增状态徽章（冷静/承压/崩溃），`broken` 状态红色边框高亮（`.suspect-item--broken`）
  - 当前嫌疑人信息卡（`.suspect-header`）：姓名旁显示状态徽章
  - 状态升级时 Toast 提示「{suspect.name} 的语气变了…… ({from} → {to})」
  - `handleConfrontClue` 中检测 `statusDelta` 变化并触发 Toast
- ✅ **样式**：新增 `.suspect-state-badge--calm`（灰色）、`.suspect-state-badge--pressured`（橙色）、`.suspect-state-badge--broken`（红色）；`.suspect-item--broken` 红色边框

**测试**
- ✅ **新建 `backend/tests/test_suspect_state_machine.py`**：9 个 pytest 用例
  - `test_calm_to_broken_on_critical`：calm → broken
  - `test_calm_to_pressured_on_related`：calm → pressured
  - `test_pressured_stays_on_second_related`：pressured 保持
  - `test_pressured_to_broken_on_critical`：pressured → broken
  - `test_broken_remains_terminal_on_related/critical`：broken 终态
  - `test_irrelevant_does_not_trigger_any_transition`：irrelevant 无影响
  - `test_counter_increments_on_related`：计数器递增
  - `test_game_not_found_returns_calm`：游戏不存在兜底

**验收**
- `pytest tests/ -x -q` → **108 passed**（含新增 9 个状态机测试），无回归
- `npm run typecheck` → **零错误**
- `npm run build` → **构建成功**（130 modules）

---

### 2026-05-05（WatsonAgent 审讯提示词增强：案件概要、其他嫌疑人、证人信息）

**背景**: `WATSON_INTERROGATION_TIPS_HUMAN` 提示词中仅包含案件线索、当前嫌疑人和最近对话，缺少案件整体概要、其他嫌疑人背景及证人信息，导致华生在审讯环节给出的建议缺乏全局视角。

**改动**
- ✅ **`backend/app/agents/prompts/watson_prompts.py`**：
  - `WATSON_INTERROGATION_TIPS_HUMAN` 新增三段：`案件概要`、`其他嫌疑人信息`、`证人信息`
  - 对应新增 `{case_summary}`、`{other_suspects_block}`、`{witnesses_block}` 占位符
- ✅ **`backend/app/agents/watson_agent.py`**：
  - `offer_interrogation_tips` 新增构建 `case_summary`（直接取 `case.summary`）
  - 新增构建 `other_suspects_block`（排除当前嫌疑人，含姓名、年龄、背景、动机、时间线、性格）
  - 新增构建 `witnesses_block`（含姓名、年龄、职业、与案件关系、时间线、关键目击）
  - `invoke_with_retry` 的 `inputs` 中新增 `"case_summary"`、`"other_suspects_block"`、`"witnesses_block"` 字段

---

### 2026-05-05（SuspectAgent / WatsonAgent 注入在场人员背景信息）

**背景**: SuspectAgent、WatsonAgent 的 System Prompt 中均未注入"在场其他嫌疑人"和"证人"清单。当玩家问及人物关系时，LLM 可能编造不存在的人名，破坏游戏一致性。

**改动**
- ✅ **`backend/app/agents/prompts/suspect_prompts.py`**：
  - `SUSPECT_RESPONSE_SYSTEM` 新增两段：`在场其他嫌疑人（可供你提及或关联）`、`在场证人（可供你提及或关联）`
- ✅ **`backend/app/agents/suspect_agent.py`**：
  - `generate_response` 新增构建 `other_suspects_block`（排除当前嫌疑人，含姓名+背景）和 `witnesses_block`（含姓名+职业+关系）
  - `invoke_with_retry` 的 `inputs` 中新增 `"other_suspects_block"`、`"witnesses_block"` 字段
- ✅ **`backend/app/agents/prompts/watson_prompts.py`**：
  - `WATSON_CHAT_SYSTEM` 中 `案件中的嫌疑人` 升级为含背景摘要的格式
  - 新增 `在场证人` 段落及 `{witnesses_block}` 变量
- ✅ **`backend/app/agents/watson_agent.py`**：
  - `_generate_response` 中升级 `suspects_block` 构建逻辑（`name + background`）
  - 新增 `witnesses_block` 构建逻辑（`name + occupation + relationship_to_case`）
  - `invoke_with_retry` 的 `inputs` 中新增 `"witnesses_block"` 字段
- ✅ **`backend/app/services/game_service.py`**：
  - `build_watson_chat_context` 中 suspects 列表新增 `"background"` 字段
  - witnesses 列表新增 `"relationship_to_case"` 字段

**验证**
- `python3 -m py_compile` 语法检查 ✅ 全绿
- `pytest tests/ -x -q` 全量回归测试 ✅ 80/80 通过

---

### 2026-05-05（SceneAgent 增加已发现线索输入，避免重复提示）

**背景**: `scene_agent.py` 调用 LLM 时未传入玩家已发现的线索列表，导致 LLM 在玩家已发现某线索后仍重复给出"发现提示"，影响游戏体验。

**改动**
- ✅ **`backend/app/agents/scene_agent.py`**：
  - 新增 `_format_discovered_clues_for_scene(case, scene)` 函数，提取当前场景对象相关且 `discovered=True` 的线索
  - `invoke_with_retry` 的 `inputs` 中新增 `"discovered_clues_block"` 字段
- ✅ **`backend/app/agents/prompts/scene_prompts.py`**：
  - `SCENE_SYSTEM` 新增规则 3a：已发现线索不再给出"发现提示"，但玩家追问时可补充新细节
  - `SCENE_SEARCH_USER` 新增 `## 玩家已在本场景发现的线索` 段落，变量 `{discovered_clues_block}`

**验证**
- `python3 -m py_compile` 语法检查 ✅ 全绿
- 无需修改路由层（`game.py`），`case.clues` 已包含 `discovered` 状态

---

### 2026-05-01（修复 SceneAgent LLM 返回 JSON key 缩写问题）

**背景**: SceneAgent 调用 LLM 后，返回的 JSON 中 `narrative` 被模型缩写为 `narr`，导致前端无法正确读取叙述文本字段。即使 prompt 中明确要求"不要随意修改key"，LLM 仍倾向缩写长 key，这是 LLM 输出格式的固有问题。

**改动**
- ✅ **`backend/app/agents/scene_agent.py`**：新增 `_KEY_ALIASES` 映射表（`narr→narrative`、`narration→narrative`、`text→narrative`、`matched_objects→matched_object_ids`、`clues→clue_candidates`）和 `_normalize_keys()` 归一化函数，在 `search()` 方法返回前对 LLM 结果做 key 校正

### 2026-05-01（修复勘查页面已发现线索面板宽度不稳定）

**背景**: `.discovered-clues-panel` 组件宽度随线索内容变化而变化，每次渲染宽度不一致。根因是该面板位于 `flex-direction: row` 的父容器 `.investigation-main` 中，且未设置任何宽度约束，宽度完全由内容撑开。

**改动**
- ✅ **`frontend/src/index.css`**：`.discovered-clues-panel` 新增 `width: 100%; max-width: 100%`，面板宽度固定为父容器满宽，不再随内容变化

### 2026-05-01（修复案件生成 JSON 截断报错）

**背景**: 生成案件时报错 `Unterminated string starting at: line 161 column 28 (char 5108)`，LLM 输出的案件 JSON 在约 5100 字符处被截断，导致 `json.loads` 失败。

**根因**: `CaseGeneratorAgent` 的 `ChatOpenAI` 未设置 `max_tokens`，模型默认输出上限（通常 4096 tokens）不足以装下完整案件 JSON（3 嫌疑人 + 5 线索 + 3 场景 + 证人 + 专家），输出在中途被截断。

**改动**
- ✅ **`backend/app/config.py`**：新增 `case_generator_max_output_tokens: int = 8000` 配置项
- ✅ **`backend/app/agents/case_generator_agent.py`**：`ChatOpenAI` 构造时传入 `max_tokens=settings.case_generator_max_output_tokens`
- ✅ **`backend/app/agents/_llm_helpers.py`**：`invoke_with_retry` 的 JSON 解析逻辑优化——截断导致的 `JSONDecodeError` 不再无意义重试，直接 `break` 跳出循环进入 fallback，避免浪费时间等待同样的截断结果

**验收**
- 41/41 后端测试全绿，无回归
- 三处修改均通过导入验证

### 2026-05-01（新增证人 Witness / 专家 Expert 角色与后端审讯互动）

**背景**: 当前案件中仅有 3 名嫌疑人可对话，缺乏真实推理小说中的目击证人和法医专家角色。为增强维多利亚时代探案的真实感，新增两类角色并扩展后端审讯 API。

**角色设计**
- **证人（Witness）**: 1-3 名/案，提供目击证词。可能因恐惧或被收买而隐瞒事实，保留「可信度提示」（区别于嫌疑人的战术性谎言）。不参与圆桌对峙。
- **专家（Expert）**: 固定 1 名/案（皇家法医），首次进入即给出「初步法医报告」，完全可信，可被追问技术细节。不检测谎言。

**后端改动**
- ✅ **数据模型扩展** (`backend/app/models/case.py`):
  - 新增 `Witness` 模型（含 `key_observations`、`is_lying_for_someone`、`bribed_by_suspect_id`、`credibility` 等字段，敏感字段 `exclude=True`）
  - 新增 `ExpertKeyFinding`、`Expert` 模型（含 `preliminary_report`、`methodology_notes`、`related_clue_ids`）
  - 扩展 `Case` 新增 `witnesses: List[Witness]`、`experts: List[Expert]`
  - `Clue.source_type` 语义扩展为 `"initial" | "scene" | "interrogation" | "witness" | "expert"`
- ✅ **Prompt 模板新建/扩展**:
  - 新建 `backend/app/agents/prompts/witness_prompts.py`：`witness_response_prompt`（基于 `key_observations` 发言、维多利亚口吻、动态注入撒谎上下文）、`witness_credibility_prompt`（JSON 模式返回可信度评估）
  - 新建 `backend/app/agents/prompts/expert_prompts.py`：`expert_response_prompt`（反幻觉策略——显式列出 `related_clue_descriptions` 作为唯一可引用物证池，拒绝动机/心理类问题）、`watson_witness_tips_prompt`（提示侦探追问 observation 而非测谎）
  - 扩展 `backend/app/agents/prompts/case_prompts.py`：JSON Schema 追加 `witnesses`/`experts` 数组定义及数量/难度约束（easy 0 撒谎 credibility≥0.8；classic ≤1 撒谎；hardcore ≤2 撒谎 0.3-0.6）
- ✅ **新建 Agent**:
  - 新建 `backend/app/agents/witness_agent.py`：`WitnessAgent`（`generate_response`、`detect_credibility`、`_build_lying_context`、mock 降级）
  - 新建 `backend/app/agents/expert_agent.py`：`ExpertAgent`（`get_preliminary_report`、`answer_question`、`_build_related_clue_descriptions` 反幻觉、mock 降级，temperature=0.4）
- ✅ **案件生成扩展** (`backend/app/agents/case_generator_agent.py`):
  - `_generate_mock_case` 按难度动态配置证人可信度与撒谎状态，新增 2 名证人 + 1 名法医专家
  - 新增 `_parse_witnesses_from_data`、`_parse_experts_from_data`、`_build_fallback_witnesses`、`_build_fallback_expert` 解析/兜底方法
- ✅ **API 路由扩展** (`backend/app/routers/game.py`):
  - 新增 4 个请求模型：`WitnessQuestionRequest`、`ExpertQuestionRequest`、`ExtractClueFromActorRequest`、`WitnessWatsonTipsRequest`
  - 新增 5 个端点：`POST /interrogation/witness/question`、`POST /interrogation/expert/question`、`GET /interrogation/expert/{id}/preliminary-report`、`POST /interrogation/extract-clue-from-actor`、`POST /interrogation/witness/watson-tips`
  - 旧端点 `/interrogation/extract-clue` 与 `/interrogation/watson-tips` 完全不变，保持兼容
- ✅ **Service 层扩展** (`backend/app/services/game_service.py`):
  - `build_watson_chat_context` 新增填充 `witnesses`（id/name/occupation）与 `experts`（id/name/title）摘要
- ✅ **华生 Agent 扩展** (`backend/app/agents/watson_agent.py`):
  - 新增 `offer_witness_interrogation_tips(case, witness, conversation_history, clues)` 方法，提示追问关键目击事实
- ✅ **配置扩展** (`backend/app/config.py`):
  - 新增 `witness_agent_max_history_messages: int = 8`、`expert_agent_max_history_messages: int = 6`
- ✅ **测试覆盖**:
  - 新建 `backend/tests/test_witness_expert.py`：20 个 pytest 用例（mock 案件结构、交叉引用一致性、Agent mock 回退、Service 层 source_type 兼容、WatsonChatContext 包含证人专家），全绿
  - 扩展 `backend/tests/test_difficulty.py`：新增 `TestWitnessDifficultyDistribution`（6 个用例：三难度下证人撒谎数与可信度范围验证），全绿

**前端改动（Commit 5+6 已完成）**
- ✅ **类型扩展** (`frontend/src/types/game.ts`)：新增 `Witness`、`Expert`、`ExpertKeyFinding`、`ActorType`、`CredibilityCheckResult`，`Case` 新增 `witnesses/experts`，`Clue.sourceType` 扩展 `witness/expert`
- ✅ **API 客户端** (`frontend/src/services/api.ts`)：新增 `askWitnessQuestion`、`askExpertQuestion`、`getExpertPreliminaryReport`、`extractClueFromActor`、`getWitnessInterrogationTips` 5 个方法
- ✅ **Store 改造** (`frontend/src/store/interrogationStore.ts`)：
  - 新增 `SelectedTab` / `ActorMessage` 类型（并存，不重构旧字段）
  - 新增 10 个状态字段：`selectedTab`、证人相关 5 个、专家相关 3 个、`extractedActorClues`
  - 新增 9 个 actions：`setSelectedTab`、`setSelectedWitnessId`、`addWitnessConversationMessage`、`setWitnessCredibilityCheck`、`fetchWitnessTips`、`setSelectedExpertId`、`addExpertConversationMessage`、`markExpertReportLoaded`、`extractClueFromActor`
  - persist `version: 1` + `migrate` 兼容旧存档（旧版本 v0 自动补齐新字段默认值）
  - `partialize` 追加新字段，旧字段完全不变

**前端改动（Commit 7 已完成）**
- ✅ **页面改造** (`frontend/src/pages/InterrogationPage.tsx`)：
  - 左栏重构为 `actors-panel`，顶部 3 个 Tab（嫌疑人 N / 证人 N / 专家 N），切换后自动选中第一个角色
  - 切换到证人/专家 Tab 时强制锁定 `private` 模式，圆桌对峙按钮在非嫌疑人 Tab 下 disabled
  - 标题动态：suspects→单独审讯/全体质询，witnesses→证人问询，experts→法医咨询
  - 证人对话区：`SelectableMessage` 提取 + 可信度检测卡（`证人迟疑/有所保留/记忆偏差` 文案）+ 华生提示面板
  - 专家对话区：自动加载 `.expert-report-card`（初步报告 + 关键发现 + 依据 clue ids）+ 对话区（无谎言检测/无华生提示）
  - 统一 `handleSendQuestion` dispatcher，按 `selectedTab` 分发到 `sendWitnessQuestion` / `sendExpertQuestion` / `sendPrivateQuestion` / `sendGroupQuestion`
  - `handleExtractConfirm` 按 Tab 分支：嫌疑人→旧 `extractClue`，证人/专家→`extractClueFromActor`
  - 新增内联样式：`.actor-tabs`、`.actor-tab`、`.actor-tab__count`、`.witness-badge`（蓝色系）、`.expert-badge`（绿色系）、`.expert-report-card`、`.credibility-check` 系列

**端到端联调（Commit 8 已完成）**
- ✅ 全量回归测试：`pytest tests/ -v` → 77/77 全绿（无回归）
- ✅ 冒烟测试 1：`POST /api/game/new` → case 含 `witnesses: 2, experts: 1`
- ✅ 冒烟测试 2：`POST /interrogation/witness/question` → 返回 `response` + `credibility_check`（含 `credibility_concern`, `confidence`）
- ✅ 冒烟测试 3：`POST /interrogation/expert/question` → 返回 `response`（无 `credibility_check` 字段）
- ✅ 冒烟测试 4：`GET /interrogation/expert/{id}/preliminary-report` → `preliminary_report` 159 字非空
- ✅ 冒烟测试 5：`POST /interrogation/extract-clue-from-actor` → `source_type: "witness"` 正确
- ✅ 冒烟测试 6：`POST /interrogation/witness/watson-tips` → 返回 3 条 `suggestion` 类型提示
- ✅ 前端 TypeScript 检查：`npm run typecheck` → 零错误
- ✅ 前端构建：`npm run build` → 128 modules，构建成功

**验收**
- 后端 `pytest tests/test_witness_expert.py tests/test_difficulty.py -v` ✅ 41/41 全绿
- 后端全量 `pytest tests/ -v` ✅ 77/77 全绿
- 前端 `npm run typecheck && npm run build` ✅ 零错误，构建成功

---

### 2026-04-29（新增全局背景音乐播放器）

**背景**: 游戏缺乏沉浸式氛围，需要在进入勘查阶段后全程播放维多利亚时代背景音乐，且音乐需跨页面持续（不因路由切换中断），并提供右下角浮窗开关控制。

**改动**
- ✅ **新建 `frontend/src/components/MusicPlayer.tsx`**：
  - 从 `frontend/assert/案件推理背景音乐_watermark.mp3` 导入音频文件（Vite 静态资源处理）
  - 读取 `uiStore.musicStarted` / `musicPlaying` 状态：`musicStarted=false` 时返回 null，不渲染按钮
  - 首次 `musicStarted` 变为 true 时创建 Audio 对象（loop=true, volume=0.5），尝试自动播放；浏览器拦截时降级为手动点击启动
  - 响应 `musicPlaying` 状态变化执行 `play()` / `pause()`
  - 右下角圆形浮窗按钮（`position: fixed; bottom: 5rem; right: 2rem; z-index: 150`），播放中金色高亮，暂停时灰色
- ✅ **修改 `frontend/src/store/uiStore.ts`**：新增 `musicStarted: boolean`、`musicPlaying: boolean`、`startMusic()`、`setMusicPlaying()` 四个状态和 action，不持久化（页面刷新重置）
- ✅ **修改 `frontend/src/App.tsx`**：在 `<Routes>` 外挂载 `<MusicPlayer />`，使其不随路由切换卸载，全生命周期保持 Audio 引用
- ✅ **修改 `frontend/src/pages/InvestigationPage.tsx`**：在 `useEffect([], [startMusic])` 中调用 `startMusic()`，首次进入勘查页面触发音乐启动；移除原先页面内的 `<MusicPlayer />` 标签
- ✅ **修改 `frontend/src/index.css`**：新增 `.music-player-btn` 和 `.music-player-btn--playing` 样式

**Z-index 层级（无冲突）**
```
9999  Toast
2000  ExtractClue Tooltip
1000  Modal overlay / Watson dragging
 150  MusicPlayer（bottom: 5rem, right: 2rem）← 新增
 100  WatsonChatDialog（bottom: 2rem, right: 2rem）
```

**验收**
- `npm run typecheck` ✅ 全绿（0 错误）
- 进入 investigation 页面 → 音乐自动播放；切换到 interrogation/deduction/conclusion 任意页面 → 音乐持续；刷新/返回登录页 → 音乐停止，按钮隐藏
- 点击右下角音符图标可切换开/关

---

### 2026-04-29（扩展 /watson/hint 路由，接入 offer_scene_hint）

**背景**: `WatsonAgent.offer_scene_hint` 方法已在章节 6 实现，但 `/watson/hint` 路由仅做字符串拼接，从未调用该方法，场景勘查提示无法享受 LLM 驱动的个性化建议。

**改动**
- ✅ **扩展 `backend/app/routers/game.py` 的 `WatsonHintRequest`**：新增 3 个可选字段：`scene_name`（当前场景名称）、`recent_actions`（玩家最近搜查动作列表）、`unchecked_object_names`（未检查对象列表）
- ✅ **`get_watson_hint` handler 新增 `hint_type == "scene"` 分支**：调用 `WatsonAgent.from_difficulty(...).offer_scene_hint()`；`collected_clues`、`total_clues`、`difficulty` 服务端从 `game` 对象派生，无需前端传入；`scene_name` 缺失时返回 400
- ✅ **旧 `idle`/`area` 分支保持不变**，无破坏性变更；全局单例 `get_watson_agent()` 统一替换为 `WatsonAgent.from_difficulty()` 与其他华生路由保持一致

**前端对接**
```json
POST /{game_id}/watson/hint
{ "hint_type": "scene", "scene_name": "书房", "recent_actions": ["检查书桌"], "unchecked_object_names": ["壁炉"] }
```

---

### 2026-04-26（修复 red herring 答案在运行时 API 中泄密）

**背景**: 玩家在勘查/推理阶段，UI 上以橙色高亮 + ⚠️ 可疑线索徽标直接展示了 red herring（干扰线索）。根因是 `Clue.is_red_herring` 字段在 `GameState` / `Clue` 等运行时接口中被默认序列化下发到前端，前端再据此为线索染色。这等于游戏开局就把答案告诉玩家，使红鲱鱼丧失误导功能。

**改动**
- ✅ **修改 `backend/app/models/case.py`**：`Clue.is_red_herring` 改为 `Field(default=False, exclude=True)`，所有 `response_model=GameState/Clue` 的接口序列化时自动剥离该字段；后端内存对象保留字段，oracle/watson/case_generator 等内部逻辑不受影响
- ✅ **保留 `conclusion/reveal` 真相通道**：`game_service.get_case_reveal()` 走手工构造 dict 路径（直接 `c.is_red_herring` 属性访问），不受 `exclude=True` 影响
- ✅ **修改 `frontend/src/types/game.ts`**：`Clue.isRedHerring` 改为可选（`?: boolean`），运行时 API 不再下发；conclusion reveal 类型保持必填
- ✅ **修改 `frontend/src/index.css`**：删除 `.clue-item--red-herring` 与 `.clue-preview-badge--herring` 两条样式规则
- ✅ **修改 `frontend/src/pages/InvestigationPage.tsx` 与 `frontend/src/pages/DeductionBoard.tsx`**：移除 className 中 `${clue.isRedHerring ? 'clue-item--red-herring' : ''}` 的条件分支
- ✅ **修改 `frontend/src/components/CluePreviewModal.tsx`**：移除「⚠️ 可疑线索」徽标渲染分支，保留「🧑 用户线索」徽标

**验证**
- Pydantic 模拟：`GameState.model_dump()` 输出中已无 `is_red_herring` 字段
- 前端 `npm run typecheck` 通过，无类型错误
- 全量 grep：除 `models/case.py` 字段定义、`game_service.get_case_reveal()` 内部逻辑、几个 Agent 内部 prompt 拼接外，前后端再无泄密路径

**遗留 / 后续建议**
- `Suspect.is_guilty` 同样存在「在运行时 API 被下发」的潜在泄密风险（GameState 序列化会带出），本次未纳入修复范围，需要时可一并处理
- 旧游戏存档为内存存储，重启即清，无持久化兼容性问题

### 2026-04-26（Docker 后端日志本地持久化与按天轮转）

**背景**: Docker 生产环境部署后，后端日志仅输出到容器 stdout，容器重建或崩溃时日志丢失，不利于问题排查。

**改动**
- ✅ **新建 `backend/app/logging_config.py`**：
  - 配置 loguru `logger.add("logs/app.log", rotation="00:00", retention="30 days")`，每天午夜自动切分新日志文件，保留最近 30 天
  - 添加 `InterceptHandler` 拦截标准库 logging，使 uvicorn 访问日志与 FastAPI 业务日志统一落入 loguru 文件
  - 同时保留 stderr sink，确保 `docker logs` 命令仍可查看实时日志
- ✅ **修改 `backend/app/main.py`**：在 `create_app()` 开头调用 `setup_logging()` 完成日志初始化
- ✅ **修改 `backend/Dockerfile`**：增加 `RUN mkdir -p logs`，确保容器内 `/app/logs` 目录存在且可写
- ✅ **修改 `docker-compose.prod.yml`**：backend 服务新增 `volumes: - ./log:/app/logs`，将容器内日志文件实时同步到宿主机项目根目录的 `log/` 文件夹

**兼容性与风险**
- 代码中使用相对路径 `logs/app.log`，容器内解析为 `/app/logs/app.log`，本地开发解析为 `backend/logs/app.log`，两端兼容
- 当前 Dockerfile 未切换非 root 用户，默认拥有写权限，无额外权限风险
- `.gitignore` 已包含 `*.log` 与 `logs/`，日志文件不会被误提交

### 2026-04-26（修复前端生产环境 API 地址配置错误）

**背景**: 部署到服务器后，浏览器中前端代码向 `http://localhost:8000` 发请求，导致网络失败。根因是 `.env` 中 `VITE_API_BASE_URL=http://localhost:8000` 被构建进生产包，浏览器中的 localhost 指向用户本地电脑而非服务器。

**改动**
- ✅ **修改 `frontend/.env`**：`VITE_API_BASE_URL` 由 `http://localhost:8000` 改为 `/api`，使前端通过 Caddy 反向代理访问后端
- ✅ **修改 `frontend/.env.example`**：同步更新示例值，增加注释说明本地开发可用 `.env.local` 覆盖
- ✅ **修改 `frontend/Caddyfile`**：
  - `handle_path /api/*` → `handle /api/*`，保留 `/api` 前缀代理到后端
  - `try_files` 和 `file_server` 移入独立的 `handle` 块，避免 `/api/*` 请求被重写为 `index.html`

**本地开发适配**
- 本地开发时在前端目录创建 `.env.local` 并设置 `VITE_API_BASE_URL=http://localhost:8000`，Vite 优先读取且该文件已被 `.gitignore` 排除

**后续发现**
- ⚠️ **根因补充**: `frontend/.dockerignore` 中 `.env` 被排除，导致 Docker 构建时未复制 `.env` 文件，Vite 构建仍使用代码默认值 `http://localhost:8000`
- ✅ **修复 `frontend/.dockerignore`**：注释掉 `.env` 排除规则，确保生产构建能读取 API 路径配置

### 2026-04-26（Docker 部署：Caddy 替换 Nginx 实现自动 HTTPS）

**背景**: 项目使用 Docker 部署后无法通过 HTTPS 访问，原因为 Nginx 配置未启用 SSL。用户要求使用最省心的方案，且当前无域名。

**改动**
- ✅ **新增 `frontend/Caddyfile`**：
  - 全局配置 `auto_https off`（无域名时必需，防止 Caddy 启动失败）
  - `:80` 占位符块提供 HTTP 服务，支持 React Router（`try_files`）
  - `/api/*` 反向代理到后端 `backend:8000`
  - 预留注释好的域名配置模板，注册域名后替换即可自动启用 HTTPS
- ✅ **重写 `frontend/Dockerfile`**：
  - Stage 2 基础镜像由 `nginx:alpine` 替换为 `caddy:2-alpine`
  - 暴露 80 和 443 端口
  - 启动命令指向 Caddyfile
- ✅ **修改 `docker-compose.prod.yml`**：
  - 前端端口增加 `443:443`
  - 新增 `volumes` 持久化 `caddy-data:/data` 和 `caddy-config:/config`，证书和配置在容器重建后不丢失
  - 文件底部定义两个 named volume

**域名注册后的启用步骤**
1. 域名解析到服务器公网 IP
2. 编辑 `frontend/Caddyfile`，删除 `auto_https off`，将 `:80` 替换为域名（如 `your-domain.com`）
3. 执行 `docker compose -f docker-compose.prod.yml up -d --build`
4. Caddy 自动申请并续期 Let's Encrypt 证书，无需其他操作

**风险与依赖**
- Let's Encrypt 不支持纯 IP 地址，必须使用域名才能启用受信任的 HTTPS
- 当前无域名时仅提供 HTTP 服务

### 2026-04-26（兑换码扣减逻辑重构 - verify 与 /new 分离）

**背景**: 原实现中 verify 按钮同时完成验证+扣减+创建游戏，用户希望验证仅做验证，实际扣减移到 `/new` 接口。

**后端改动**
- ✅ **拆分 `backend/app/services/redemption_service.py`**：`validate_and_consume` 拆分为 `validate_only`（仅验证）、`consume`（仅扣减）、`validate_and_consume`（保留原子操作供测试复用）
- ✅ **改造 `backend/app/routers/redemption.py` `verify` 接口**：仅验证可用性，不扣减次数，不创建游戏，返回 `game_id=None`
- ✅ **改造 `backend/app/routers/game.py` `/new` 接口**：
  - 新增 `redemption_code` 可选参数
  - 若提供了兑换码，先调用 `validate_only` 获取其绑定的 OpenAI 配置
  - 创建游戏时绑定 `openai_api_key/openai_base_url/redemption_code`
  - 生成案件后调用 `consume` 扣减一次使用次数
- ✅ **扩展 `backend/app/models/game.py`**：`CreateGameRequest` 新增 `redemption_code` 字段
- ✅ **移除 `backend/app/models/redemption.py`**：`RedemptionVerifyResponse` 移除 `game_id` 字段

**前端改动**
- ✅ **更新 `frontend/src/services/api.ts`**：`createNewGame` 新增 `redemptionCode` 参数，透传给后端
- ✅ **更新 `frontend/src/pages/LoginPage.tsx`**：移除 `!result.gameId` 检查（verify 现返回 `gameId: undefined`），直接跳转 `/start`
- ✅ **更新 `frontend/src/pages/StartPage.tsx`**：调用 `createNewGame(selectedDifficulty, session.code)`；移除 `setRedemptionSession` 调用（不再存储 gameId）
- ✅ **更新 `frontend/src/App.tsx`**：`RequireRedeem` 守卫检查 `session?.code` 而非 `session?.gameId`
- ✅ **更新 `frontend/src/types/redemption.ts`**：`RedemptionVerifyResponse` 移除 `gameId`；`RedemptionSession` 移除 `gameId`（改为可选后完全移除）

**新完整流程**
1. 登录页验证 → `POST /api/redemption/verify` → 仅验证，`session.code` 存入 localStorage
2. 选择难度 → `POST /api/game/new`（传入 `redemption_code`）→ 验证兑换码 + 创建游戏 + 生成案件 + **扣减次数**
3. 跳转勘查页

**验收**
- `npm run typecheck` ✅ 全绿（0 错误）
- 后端 pytest `test_redemption_service.py` 9/9 全绿

### 2026-04-26（兑换码后端实现 - 3-3-1-typed-widget.md）
- ✅ **`.gitignore` 更新**：追加 `backend/data/redemption_codes.json`，防止含 apikey 的文件入库
- ✅ **新建 `backend/app/models/redemption.py`**：`RedemptionCode`（内部）、`RedemptionGenerateResponse`（不含 apikey）、`RedemptionVerifyRequest/Response`
- ✅ **新建 `backend/app/services/redemption_service.py`**：单例 + `threading.Lock` + 原子写；`generate_code()`、`validate_and_consume()`、`get_remaining_uses()`
- ✅ **新建 `backend/app/routers/redemption.py`**：`POST /api/redemption/generate`、`POST /api/redemption/verify`（验证成功后直接创建 game 会话，返回 `game_id`）
- ✅ **扩展 `backend/app/models/game.py`**：`GameState` 新增 `openai_api_key`（`Field(exclude=True)`）、`openai_base_url`、`redemption_code`，apikey 不出现在 API 响应中
- ✅ **扩展 `backend/app/services/game_service.py`**：`create_game()` 接受可选 openai 配置参数并写入 GameState
- ✅ **更新 `backend/app/main.py`**：注册 redemption router 到 `/api/redemption`
- ✅ **新建 `backend/tests/test_redemption_service.py`**：9/9 测试全绿（生成、验证、耗尽、并发无超扣）

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
- [P1] 前端页面适配移动端
- [P2] 为scene_agent之外的其他agent的invoke_with_retry 返回后，添加一个 _normalize_keys 辅助函数，映射已知别名，避免llm返回缩写导致的字段命名不一致问题
---

## MVP版本待办事项
1. 数据库接入（PostgreSQL + SQLAlchemy / asyncpg）—— 解决数据丢失问题
  2.1. 数据库表结构设计
  2.2. 每一个用户进入游戏后需要记录用户的openai baseurl和apikey（包括兑换码的baseurl和apikey）
  2.3. 前端新增一个存档按钮，点击存档后，需要将每一个用户的游戏数据（游戏难度、游戏时间、游戏结果、游戏内对话记录等）存储到数据库
  2.4. 前端新增一个加载按钮，点击加载存档后，需要从数据库中读取用户上一次的游戏数据并恢复到当前游戏页面


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