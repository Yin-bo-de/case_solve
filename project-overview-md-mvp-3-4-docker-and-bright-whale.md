# MVP 任务 3 & 4 执行计划

## 背景与目标

本计划对应 `project_overview.md` 中 MVP 版本待办事项的第 3 项和第 4 项：

- **任务 3：Docker + docker-compose** — 统一本地与生产环境，实现一键启动
- **任务 4：Agent 上下文大小管理** — 避免游戏进行中对话历史、推理数据线性增长导致超出模型最大上下文长度

---

## 任务 3：Docker + docker-compose

### 3.1 根因分析

当前项目无任何容器化配置：
- 后端依赖 Python 3.11 + pip3，开发启动用 `uvicorn --reload`
- 前端依赖 Node.js + Vite，开发服务器端口 3000，通过 proxy 访问后端 localhost:8000
- 环境变量分散在前后端各自的 `.env` 文件中
- 生产部署方式不明确

### 3.2 执行步骤

#### 步骤 1：创建后端 Dockerfile

**文件**：`backend/Dockerfile`

- 基于 `python:3.11-slim`
- 分阶段构建（非必须，但推荐保持 slim）
- 安装 `requirements.txt` 中的依赖
- 暴露端口 8000
- 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port 8000`（生产不加 `--reload`）
- 注意：`.env` 文件不打包进镜像，通过环境变量或 docker-compose 注入

#### 步骤 2：创建前端 Dockerfile

**文件**：`frontend/Dockerfile`

- 基于 `node:20-alpine` 多阶段构建
- Stage 1（build）：安装依赖 → `npm run build` 生成静态文件
- Stage 2（serve）：基于 `nginx:alpine`，复制构建产物到 `/usr/share/nginx/html`
- 复制自定义 `nginx.conf`，配置前端路由 fallback（React Router 需要 `try_files $uri /index.html`）
- 暴露端口 80

#### 步骤 3：创建 nginx 配置

**文件**：`frontend/nginx.conf`

- 监听 80 端口
- 根目录指向 `/usr/share/nginx/html`
- 配置 `location /` 的 `try_files` 支持前端路由
- 配置 `location /api` 反向代理到后端服务（容器内网通信，通过服务名 `backend`）

#### 步骤 4：创建 docker-compose.yml（开发环境）

**文件**：项目根目录 `docker-compose.yml`

- 定义两个服务：`backend`、`frontend`
- `backend`：
  - 构建上下文 `./backend`
  - 端口映射 `8000:8000`
  - 环境变量从根目录 `.env` 文件注入（`OPENAI_API_KEY`、`OPENAI_BASE_URL` 等）
  - 开发模式可挂载代码卷实现热重载（可选）
- `frontend`：
  - 构建上下文 `./frontend`
  - 端口映射 `80:80`
  - 依赖 `backend` 服务
- 使用 Docker 内网通信，前端通过 `http://backend:8000` 访问后端 API

#### 步骤 5：创建 docker-compose.prod.yml（生产环境）

**文件**：项目根目录 `docker-compose.prod.yml`

- 不挂载代码卷
- 后端移除 `--reload`
- 可加入健康检查（`healthcheck`）
- 可限制容器资源（`deploy.resources`）

#### 步骤 6：创建 .dockerignore

**文件**：`backend/.dockerignore`、`frontend/.dockerignore`

- 排除 `node_modules/`、`venv/`、`.git/`、`__pycache__/`、`.env` 等

#### 步骤 7：修改 vite.config.ts（适配 Docker 内网）

**文件**：`frontend/vite.config.ts`

- 当前 proxy 写死 `target: 'http://localhost:8000'`
- 改为读取环境变量 `VITE_API_BASE_URL`，默认值仍为 `http://localhost:8000`
- 确保 Docker 环境下可通过环境变量指向 `http://backend:8000`

#### 步骤 8：更新 .env.example 和文档

- 根目录新增 `.env.example`，汇总前后端所需环境变量
- 在 `project_overview.md` 中更新开发命令参考，增加 Docker 启动方式

#### 步骤 9：验证

```bash
docker-compose up --build
```

- 前端页面 `http://localhost` 正常访问
- 后端 API `http://localhost:8000/health` 返回 healthy
- 前端能正常调用后端 API 创建游戏、进行完整流程

---

## 任务 4：Agent 上下文大小管理

### 4.1 根因分析

游戏中以下数据会随游玩时间线性增长：

| 数据源 | 增长方式 | 当前限制 | 风险等级 |
|--------|----------|----------|----------|
| **SuspectAgent 审讯对话历史** | 每轮问答 +2 条消息 | ❌ **无限制** | 🔴 **高** |
| WatsonAgent 自由对话历史 | 每条消息追加 | ❌ 无限制（但 prompt 未注入历史） | 🟡 中 |
| 推理链条（observations / inferences / hypotheses） | 用户操作递增 | ❌ 无限制 | 🟡 中 |
| 场景 NPC 对话历史 | 每轮 +2 条 | ✅ 已限制 6 轮 | 🟢 低 |
| 审讯实时 Tips 输入 | 每轮传入 | ✅ 已限制 8 轮 | 🟢 低 |
| 矛盾检测陈述输入 | 累积 | ✅ 已限制每人 3 条 | 🟢 低 |

**核心问题**：`SuspectAgent.generate_response()` 接收 `conversation_history` 列表，完整转为 LangChain messages 传入 LLM。长时间审讯（如 50 轮）会产生约 100 条消息，轻松超出 GPT-4 的 128K 上下文上限中的有效工作窗口，导致：
1. Token 费用暴涨
2. 响应延迟增加
3. 早期关键信息被挤占
4. 可能触发模型截断或报错

### 4.2 执行步骤

#### 步骤 1：在 _llm_helpers.py 中引入 tiktoken 进行 Token 估算

**文件**：`backend/app/agents/_llm_helpers.py`

- 新增依赖：`tiktoken`（加入 `requirements.txt`）
- 新增函数 `estimate_token_count(text: str, model: str = "gpt-4") -> int`
- 新增函数 `truncate_messages_by_token(messages: List[Dict], max_tokens: int, model: str) -> List[Dict]`
  - 策略：保留最近 N 条完整消息，从旧到新截断，直到总 token < max_tokens
  - 始终保留 system prompt（如果有）和最近的用户消息

#### 步骤 2：统一上下文管理配置

**文件**：`backend/app/config.py`

- 在 Settings 中新增上下文管理相关配置（带合理默认值）：
  - `SUSPECT_AGENT_MAX_HISTORY_MESSAGES = 20`（保留最近 20 轮 = 40 条消息）
  - `SUSPECT_AGENT_MAX_HISTORY_TOKENS = 8000`
  - `WATSON_CHAT_MAX_HISTORY_MESSAGES = 50`
  - `WATSON_CHAT_MAX_HISTORY_TOKENS = 12000`
  - `SCENE_AGENT_MAX_HISTORY_MESSAGES = 6`（与现有逻辑一致）
  - `SCENE_AGENT_MAX_HISTORY_TOKENS = 4000`
  - `ORACLE_AGENT_MAX_CONTEXT_TOKENS = 10000`

#### 步骤 3：SuspectAgent 添加上下文截断

**文件**：`backend/app/agents/suspect_agent.py`

- 在 `generate_response()` 方法中，构建 `history` 列表之前，先对 `conversation_history` 进行截断
- 截断策略（组合使用）：
  1. 先按消息数量截断：保留最近 `SUSPECT_AGENT_MAX_HISTORY_MESSAGES` 轮（即 `conversation_history[-MAX_HISTORY_MESSAGES:]`）
  2. 再按 token 数量截断：调用 `_llm_helpers.truncate_messages_by_token()` 确保总 token 不超过预算
- 日志记录：截断前/后的消息数量和估算 token 数，便于调试

#### 步骤 4：WatsonAgent 聊天添加上下文管理

**文件**：`backend/app/agents/watson_agent.py`

- 当前 `chat()` 和 `_generate_response()` 未在 prompt 中注入对话历史
- **策略选择**：基于项目现状，华生自由对话以"当前状态快照 + 用户最新问题"为主，不依赖长对话历史（与 ChatGPT 式连续对话不同）
- 但为防未来扩展，需在 `game_service.py` 的 `add_watson_chat_message` / `get_watson_chat_history` 中增加上限保护：
  - 当某游戏的聊天记录超过 `WATSON_CHAT_MAX_HISTORY_MESSAGES` 时，丢弃最旧的消息
- 若未来需要在 prompt 中注入历史，再启用 token 截断

#### 步骤 5：推理链条数据增长防护

**文件**：`backend/app/services/game_service.py`

- `DeductionChain` 的 `observations`、`inferences`、`hypotheses` 列表随游戏进行会增长
- 虽然这些数据**不直接传入 LLM prompt**（OracleAgent 只接收选取的线索和结论，不接收完整链条），但内存占用会持续增长
- 添加防护性上限（软限制）：
  - `MAX_INFERENCES_PER_GAME = 50`
  - `MAX_HYPOTHESES_PER_GAME = 20`
  - `MAX_USER_CLUES_PER_GAME = 30`
- 当用户尝试创建超出上限的数据时，返回友好提示（如"推理记录已达上限，请先删除不必要的记录"）

#### 步骤 6：GameService 对话历史存储上限

**文件**：`backend/app/services/game_service.py`

- `self._watson_chat_history[game_id]` 和审讯相关的对话历史（如 future DB 中的记录）需有上限
- 在 `add_watson_chat_message()` 中：
  - 如果该游戏的聊天记录超过 `WATSON_CHAT_MAX_HISTORY_MESSAGES`，移除最旧的消息
- 审讯对话历史（由前端传入后端的 `conversation_history`）虽然存储在前端，但后端应通过 API 文档/校验提示前端也做限制

#### 步骤 7：Token 使用监控与日志

**文件**：`backend/app/agents/_llm_helpers.py`

- 在 `invoke_with_retry()` 中：
  - 调用前记录估算的输入 token 数（基于 `inputs` 字典的 JSON 序列化长度估算）
  - 调用成功后记录实际耗时、重试次数
  - 如果估算 token 数超过某个阈值（如 10000），记录 `logger.warning` 提示"上下文接近上限"

#### 步骤 8：新增上下文管理单元测试

**文件**：`backend/tests/test_context_management.py`

- 测试 `truncate_messages_by_token`：
  - 短列表不截断
  - 长列表正确截断到最近 N 条
  - 单条超长消息的处理
- 测试 SuspectAgent 截断逻辑：
  - 传入 100 条历史，确认只保留最近 20 轮
- 测试 Watson 聊天历史上限：
  - 连续添加 60 条消息，确认只保留 50 条

#### 步骤 9：验证

- 运行后端测试：`pytest backend/tests/test_context_management.py -v`
- 端到端测试：创建游戏 → 进行 30 轮以上审讯 → 确认响应时间稳定、无上下文溢出报错
- 检查日志：确认截断事件被正确记录

---

## 关键文件清单

### 任务 3 新增/修改文件

| 文件路径 | 操作 | 说明 |
|----------|------|------|
| `backend/Dockerfile` | 新增 | Python 3.11 slim 镜像 |
| `frontend/Dockerfile` | 新增 | Node 20 多阶段构建 + Nginx |
| `frontend/nginx.conf` | 新增 | Nginx 路由 fallback + API 反向代理 |
| `docker-compose.yml` | 新增 | 开发环境编排 |
| `docker-compose.prod.yml` | 新增 | 生产环境编排 |
| `backend/.dockerignore` | 新增 | 排除不需要的文件 |
| `frontend/.dockerignore` | 新增 | 排除不需要的文件 |
| `frontend/vite.config.ts` | 修改 | 代理目标支持环境变量 |
| `.env.example` | 新增（根目录） | 汇总环境变量模板 |
| `project_overview.md` | 修改 | 补充 Docker 启动命令 |

### 任务 4 新增/修改文件

| 文件路径 | 操作 | 说明 |
|----------|------|------|
| `backend/requirements.txt` | 修改 | 新增 `tiktoken` |
| `backend/app/config.py` | 修改 | 新增上下文管理配置项 |
| `backend/app/agents/_llm_helpers.py` | 修改 | 新增 token 估算、消息截断函数 |
| `backend/app/agents/suspect_agent.py` | 修改 | generate_response 增加历史截断 |
| `backend/app/agents/watson_agent.py` | 修改 | 预留/调整上下文处理逻辑 |
| `backend/app/services/game_service.py` | 修改 | 聊天记录上限、推理数据软上限 |
| `backend/tests/test_context_management.py` | 新增 | 上下文管理单元测试 |

---

## 依赖关系

1. 任务 3 和任务 4 **相互独立**，可并行开发
2. 任务 4 中的 `tiktoken` 依赖需要提前安装（修改 requirements.txt 后执行 `pip3 install -r requirements.txt`）
3. 两个任务都完成后，统一运行前后端类型检查/测试验证

---

## 验证方式

### 任务 3 验证

```bash
# 1. 构建并启动
docker-compose up --build

# 2. 健康检查
curl http://localhost:8000/health

# 3. 前端访问
open http://localhost

# 4. 完整流程：创建游戏 → 勘查 → 审讯 → 推理 → 结案
```

### 任务 4 验证

```bash
# 1. 单元测试
cd backend
pytest tests/test_context_management.py -v

# 2. 长会话压力测试（模拟 50 轮审讯）
# 可通过脚本连续调用 /interrogation/question 接口，观察响应时间和日志

# 3. 日志检查
grep "上下文" backend/logs/*.log  # 确认截断事件被记录
grep "token" backend/logs/*.log   # 确认 token 估算被记录
```

---

## 风险点与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| Docker 内网通信问题（前端→后端） | 服务启动但 API 调用失败 | 使用服务名通信，`nginx.conf` 反向代理 `/api` 到 `http://backend:8000` |
| tiktoken 依赖增加镜像体积 | 后端镜像变大 | tiktoken 纯 Python + Rust 扩展，体积增加约 5MB，可接受 |
| 截断策略不当导致关键信息丢失 | 游戏体验下降 | 保留最近 N 轮（而非中间截断），N 取值留配置余地；默认 20 轮足够覆盖大多数审讯 |
| 环境变量注入遗漏 | 服务启动失败 | 根目录 `.env.example` 明确列出所有必需变量；docker-compose 显式声明 `env_file` |

---

*计划完成，等待确认后执行。*
