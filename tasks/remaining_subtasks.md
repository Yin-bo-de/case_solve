# 福尔摩斯探案游戏 - 剩余工作子任务拆解

> 生成日期：2026-04-17
> 基于：`project_overview.md`（2026-04-15 快照，项目进度约 90%）
> 对应 PRD：`tasks/prd-us-017-difficulty-system.json`、`tasks/prd-us-018-victorian-gothic-ui.json`、`tasks/prd-us-020-end-to-end-testing.json`

---

## 背景

项目当前约 90% 完成，17/21 个用户故事已交付。剩余 4 大块工作需要拆解为更容易实现的子任务：

1. **US-017 难度系统**（后端已有 30% 基础，剩余需扩展）
2. **LLM Mock 替换**（LangChain 脚手架全部就位，仅缺 prompt + 解析逻辑）
3. **US-018 维多利亚哥特风 UI**（基础样式 100% 完成，缺高级视觉效果）
4. **US-020 端到端集成测试**（后端 pytest 已装，前端无测试框架）

本文件是**任务清单**，不是实现方案。每个子任务均可独立交付、独立验收。

---

## 一、US-017 难度系统（Priority: 最高）

**现状**：`GameDifficulty` 枚举已定义（easy/classic/hardcore）；错误次数、时间限制已按难度生效；其他维度未实现。

### 子任务

#### T1.1 案件生成端 - 红鲱鱼与线索明显度随难度调整
- **文件**：`backend/app/agents/case_generator_agent.py`
- **内容**：
  - `_generate_mock_case(case_id, difficulty)` 中根据 difficulty 控制：
    - Easy：明显线索比例 70%、红鲱鱼 1 个；
    - Classic：明显线索 50%、红鲱鱼 2 个；
    - Hardcore：明显线索 30%、红鲱鱼 3 个。
  - 在 `Clue` 模型（`backend/app/models/case.py`）若无 `obviousness` 字段则新增（已有则复用）。
- **验收**：三种难度生成的案件 clue 列表中 `obviousness`/`is_red_herring` 分布符合预期。

#### T1.2 华生主动性与提示频率随难度调整
- **文件**：`backend/app/agents/watson_agent.py`、`backend/app/services/game_service.py`
- **内容**：
  - 在 WatsonAgent 增加 `proactive_rate` 配置：Easy=0.8、Classic=0.5、Hardcore=0.2（决定 `share_observation`/`question_reasoning` 的触发概率）。
  - 在 `game_service` 把当前 game 的 difficulty 注入 WatsonAgent 调用链。
- **验收**：Easy 模式勘查页面华生评论频繁出现，Hardcore 模式极少主动介入。

#### T1.3 前端 StartPage 难度描述文案完善
- **文件**：`frontend/src/pages/StartPage.tsx`
- **内容**：三个难度卡片补充对应的"线索明显度/华生活跃度/错误机会"量化描述（与后端一致）。
- **验收**：用户看到三个难度的差异清晰可预期。

#### T1.4 后端单元测试：难度参数生效
- **文件**：新建 `backend/tests/test_difficulty.py`
- **内容**：pytest 用例覆盖三种难度下 case 生成、错误次数配置、华生触发频率。
- **验收**：`pytest backend/tests/test_difficulty.py` 全绿。

---

## 二、LLM Mock 替换（Priority: 次高，是游戏真正可玩的关键）

**现状**：三个 Agent 都已导入 `ChatOpenAI`、`ChatPromptTemplate`，并在 `__init__` 创建 `self.llm` 实例；`config.py` 有 `openai_api_key/base_url/model`；所有方法都有 `# TODO: 实际调用LLM` 注释，当前直接调用 `_generate_mock_*`。

### 子任务

#### T2.1 准备 PromptTemplate 工程化管理
- **文件**：新建 `backend/app/agents/prompts/` 目录，每个 Agent 一个 `.py` 文件（如 `case_prompts.py`/`suspect_prompts.py`/`watson_prompts.py`）
- **内容**：将每个方法的 System/Human prompt 模板集中管理，变量化替换（难度、嫌疑人人设、对话历史等）。
- **验收**：prompts 可被各 Agent 导入并格式化生成 messages。

#### T2.2 case_generator_agent 接入真实 LLM
- **文件**：`backend/app/agents/case_generator_agent.py`
- **内容**：
  - `generate_case` 用 `ChatPromptTemplate` + `PydanticOutputParser(Case)` 生成完整案件；
  - 保留 `_generate_mock_case` 作为 LLM 失败的降级路径，但仅在 API key 缺失时使用（非 silent fallback）。
  - 关键日志：prompt 发送/响应/解析耗时。
- **验收**：在有效 API key 下生成一次真实案件，嫌疑人/线索/凶手逻辑自洽。

#### T2.3 suspect_agent 接入真实 LLM（3 个方法）
- **文件**：`backend/app/agents/suspect_agent.py`
- **内容**：
  - `generate_response`：嫌疑人人设 + 案件上下文 + 对话历史 → 对话回复；
  - `detect_lie`：基于案件真相 + 嫌疑人回复 → 结构化 JSON（`lie_detected`/`confidence`/`microexpression`）；
  - `generate_interjection`：全体质询下，其他嫌疑人是否插话以及插话内容。
- **验收**：三种调用在单独/圆桌审讯页面返回合理的 AI 回复。

#### T2.4 watson_agent 接入真实 LLM（4 个方法）
- **文件**：`backend/app/agents/watson_agent.py`
- **内容**：
  - `share_observation`、`question_reasoning`、`provide_knowledge`、`suggest_hypothesis` 替换为 LLM 调用；
  - `encourage` 可保留规则式（轻量场景）。
- **验收**：勘查、推理、质询、结案页面华生反馈不再重复、有案件针对性。

#### T2.5 LLM 调用通用封装（可选、收敛重复）
- **文件**：`backend/app/agents/_llm_helpers.py`
- **内容**：封装 `async def invoke_with_retry(chain, inputs, parser=None)`，统一重试/超时/日志/降级。
- **验收**：三个 Agent 的 LLM 调用走同一封装。

---

## 三、US-018 维多利亚哥特风 UI 精致化（Priority: 中）

**现状**：`index.css` 2109 行，暗色背景/金色点缀/Georgia 字体已完成；五个页面均有独立样式；缺煤气灯和木质纹理。

### 子任务

#### T3.1 全局煤气灯光晕效果
- **文件**：`frontend/src/index.css`、`frontend/public/` 可能新增 SVG
- **内容**：
  - 为主按钮、标题新增柔和黄色光晕（`box-shadow`/`text-shadow` + 微动画 `@keyframes flicker`）；
  - 在 StartPage 贝克街场景添加"壁灯"角落装饰。
- **验收**：浏览器观察到有规律的微闪烁，不刺眼、不卡顿。

#### T3.2 木质纹理 / 羊皮纸纹理背景
- **文件**：`frontend/public/textures/`（新增 2-3 张纹理图或 CSS 渐变模拟）、`frontend/src/index.css`
- **内容**：
  - 卡片/面板背景用深褐木纹；
  - 文档类面板（线索卡、推理笔记）用羊皮纸纹理。
- **验收**：页面关键容器呈现可辨识的纹理感，保持对比度。

#### T3.3 文本措辞 19 世纪化润色
- **文件**：前端页面中的固定文案（StartPage、InvestigationPage 引导语、系统提示等）
- **内容**：把现代白话替换为更贴合维多利亚叙事风格（如"请您着手勘查现场"→"有劳先生亲临现场细查"）。
- **验收**：关键文案有"时代气息"，无穿帮白话。

#### T3.4 字体引入（可选、提升质感）
- **文件**：`frontend/index.html` 或 `index.css`
- **内容**：引入 Cinzel/IM Fell English 等维多利亚风格衬线字体作为标题字体。
- **验收**：标题与正文形成风格反差。

---

## 四、US-020 集成与端到端测试（Priority: 中，作为最后闸门）

**现状**：后端已装 pytest + pytest-asyncio + httpx；前端无测试框架；无 `backend/tests/` 目录。

### 子任务

#### T4.1 后端 API 集成测试骨架
- **文件**：新建 `backend/tests/conftest.py`、`backend/tests/test_game_flow.py`
- **内容**：
  - conftest 构造 FastAPI TestClient；
  - `test_game_flow` 串联：new → difficulty → watson observation → interrogation → deduction → accuse → reveal，断言关键字段。
- **验收**：`pytest backend/tests/` 全绿，覆盖核心 11 个 API。

#### T4.2 前端引入 Vitest + React Testing Library
- **文件**：`frontend/package.json`、`frontend/vitest.config.ts`（新增）
- **内容**：安装 `vitest`/`@testing-library/react`/`jsdom`，配置 `npm run test`。
- **验收**：一个 smoke test（如渲染 `StartPage`）通过。

#### T4.3 前端关键 store 单元测试
- **文件**：`frontend/src/store/__tests__/gameStore.test.ts`、`deductionStore.test.ts` 等
- **内容**：覆盖 setDifficulty、错误次数累计、推理链增删、localStorage 持久化。
- **验收**：`npm run test` 全绿。

#### T4.4 浏览器端到端手动 QA（用 `/qa-only` 技能）
- **内容**：启动前后端，走完一遍"新案件 → 勘查 → 审讯 → 推理 → 结案"完整流程，记录任何回归。
- **验收**：产出一份 QA 报告（通过/失败 checklist），列出所有发现的问题。

#### T4.5 类型检查 + Lint 清单
- **内容**：`mypy backend/app/` + `cd frontend && npm run typecheck && npm run lint`，修复所有残留告警。
- **验收**：无 error，warning 最小化。

---

## 推荐执行顺序（依赖关系）

```
T1.1 → T1.2 → T1.3 → T1.4          （难度系统先落地，后续测试和 LLM 都可能依赖它）
       ↓
T2.1 → T2.2/T2.3/T2.4 (可并行) → T2.5
       ↓
T3.1 → T3.2 → T3.3 → T3.4          （UI 精致化与功能独立，可在任意时间穿插）
       ↓
T4.1 → T4.2 → T4.3 → T4.4 → T4.5   （作为最终闸门）
```

**并行机会**：T3 系列与 T2 系列可完全并行；T4.2（安装 vitest）可先做，再和 T4.3 并行。

---

## 关键文件清单（后续实施时会动到）

- `backend/app/agents/case_generator_agent.py` / `suspect_agent.py` / `watson_agent.py`
- `backend/app/agents/prompts/*.py`（新增）
- `backend/app/services/game_service.py`
- `backend/app/models/case.py`（可能新增 `obviousness` 字段）
- `backend/tests/*.py`（新增）
- `frontend/src/pages/StartPage.tsx`
- `frontend/src/index.css`
- `frontend/src/store/__tests__/*.ts`（新增）
- `frontend/package.json`、`frontend/vitest.config.ts`（新增）
- `scripts/ralph/prd.json`、`scripts/ralph/progress.txt`（每个子任务完成后更新）
- `project_overview.md`（阶段性更新）

---

## 验证方法

每个子任务结束后至少一种：
1. **后端**：`pytest backend/tests/`、`mypy backend/app/`、手动 curl 对应 API；
2. **前端**：`npm run typecheck`、`npm run lint`、`npm run test`、`npm run dev` + 浏览器 QA；
3. **整体**：`/qa-only` 技能跑一次完整流程。
