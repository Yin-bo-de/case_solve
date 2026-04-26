# 福尔摩斯探案游戏 — MVP 四项执行计划

> 本文件为 `project_overview.md` "MVP 版本待办事项" 4 项任务各自的可执行计划。每章节自成一份独立计划，另一个 agent 拿到对应章节即可直接落地。

## Context（背景与共识）

- 项目当前状态：所有数据存内存（`GameService._games: Dict[str, GameState]`），无数据库、无登录、无 Docker。LLM 配置全局走 `app.config.Settings`（pydantic-settings 单实例）。
- LLM 实例化方式：每个 Agent 的 `__init__` 中固定创建 `ChatOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)`；mock 降级路径基于 `if not settings.openai_api_key`。
- 约束（用户 2026-04-25 已确认）：
  1. **用户身份**：简单**用户名密码登录**（JWT 鉴权），不引入 OAuth。
  2. **任务 1 兑换码**：完全本地化生成 + 存储 + 兑换次数记录（落盘 JSON / SQLite 二选一，后文统一选 SQLite 单文件最轻量）。
  3. **任务 1 OpenAI 凭证**：作为**一次性服务**，不持久化到磁盘；仅在用户当前 session 内存中保留，重启 / 登出即丢。
  4. **任务 2 数据库**：仅产出**设计文档**，**不做实现**。
  5. **任务 3、4** 完全独立。
  6. **上下文压缩策略**：tiktoken 计数 + 旧历史 LLM 摘要 + 近窗保留。
- 用户偏好（来自 CLAUDE.md）：FastAPI、loguru、pip3、pydantic-settings、Zustand、TypeScript、维多利亚哥特风。沟通中文，代码注释中英混合。

---

# 任务 1：起始页登录 + 兑换码 + OpenAI 凭证一次性接入

## 1.1 设计目标

- 起始页改造为"登录页 → 配置页 → 难度选择 → 进游戏"四段式
- 用户名/密码登录系统（注册免费），后端 JWT 鉴权
- 兑换码：本地生成 N 个码（脚本），用户兑换后**记录次数**（一码默认 10 次，0 次后失效）
- 兑换成功后，后端将该兑换码绑定的 `base_url + api_key` 注入到该用户的"会话凭证缓存"（**仅内存**）
- 用户也可手动填 base_url + api_key：
  - "验证"按钮 → 后端代理 GET `{base_url}/v1/models` → 返回 valid/invalid（不写任何存储）
  - "提交"按钮 → 凭证传入后端，写入会话凭证缓存（仅内存，重启即失）
- 后续所有 LLM 调用使用该用户当前会话凭证；缺凭证时走 mock 降级（保留现状）

## 1.2 关键架构决策

| 决策 | 理由 |
|---|---|
| 用户密码用 SQLite 文件 (`backend/data/auth.db`) + bcrypt 哈希 | 不依赖任务 2 的 PostgreSQL；MVP 单机够用；与"数据库设计文档不实施"约束相符 |
| 兑换码池同样存 SQLite (`auth.db` 内 `redemption_codes` 表) | 持久化次数+绑定关系；脚本可批量生成 |
| OpenAI 凭证只放后端进程内存 `dict[user_id] -> {base_url, api_key, expires_at}`，TTL=24h | 满足"一次性服务，不存储记忆"；TTL 防 OOM |
| 鉴权用 JWT (HS256)，前端存 `localStorage["sherlock_token"]` | 简单可靠；与 Zustand 配合自然 |
| `LLMFactory.build_for_user(user_id)` 工厂从内存凭证缓存读 → 返回 ChatOpenAI 实例（无凭证返回 None 走 mock） | Agent 去单例化 LLM 必经之路 |
| Agent `__init__` 移除 `self.llm`，方法签名加 `llm: BaseChatModel \| None` 由 router 注入 | 关注点分离；不让 Agent 知道 DB |
| 验证 `/v1/models` 失败时回退试 `/chat/completions` mini ping | 第三方代理可能不暴露 `/models` |
| 兑换码格式 `SHERLOCK-XXXX-XXXX`（脚本生成时去歧义字符 0/O/1/l/I） | 用户友好 |

## 1.3 数据存储（SQLite, `backend/data/auth.db`）

```sql
CREATE TABLE users (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  username        TEXT UNIQUE NOT NULL,
  password_hash   TEXT NOT NULL,            -- bcrypt
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);

CREATE TABLE redemption_codes (
  code             TEXT PRIMARY KEY,        -- e.g. SHERLOCK-A3B7-K9P2
  base_url         TEXT NOT NULL,
  api_key          TEXT NOT NULL,
  total_quota      INTEGER NOT NULL DEFAULT 10,
  remaining_quota  INTEGER NOT NULL DEFAULT 10,
  created_at       TEXT NOT NULL
);

CREATE TABLE redemption_records (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      INTEGER NOT NULL REFERENCES users(id),
  code         TEXT NOT NULL REFERENCES redemption_codes(code),
  redeemed_at  TEXT NOT NULL
);
CREATE INDEX ix_redemption_records_user ON redemption_records(user_id);
```

注：兑换码"次数"语义 = 码池本身 `remaining_quota`，每次兑换 -1（不是按用户次数）。如果改为"用户兑换该码后获得 10 次 LLM 调用配额"，须在 `users` 加 `llm_quota` 字段并在每次 LLM 调用时扣减。本 MVP 采用**码池次数**简化语义：一码可被 10 个不同用户兑换，每兑换 -1。

## 1.4 后端改造点

### 1.4.1 新增依赖（`backend/requirements.txt` 追加）

```
sqlalchemy>=2.0
aiosqlite>=0.19
bcrypt>=4.1
python-jose[cryptography]>=3.3
httpx>=0.27
```

### 1.4.2 新增文件

- `backend/data/.gitkeep`（数据库放此目录，加入 `.gitignore` 忽略 `*.db`）
- `backend/app/db/__init__.py`
- `backend/app/db/session.py`：`engine = create_async_engine("sqlite+aiosqlite:///data/auth.db", echo=False)`、`AsyncSessionLocal`、`async def get_db()`
- `backend/app/db/base.py`：`class Base(DeclarativeBase): pass`
- `backend/app/models/db.py`：ORM 类 `User`, `RedemptionCode`, `RedemptionRecord`
- `backend/app/services/auth_service.py`
  - `async def register(session, username, password) -> User`（用户名唯一冲突 → `HTTPException(409)`）
  - `async def login(session, username, password) -> tuple[User, str]`（返回 user 和 jwt）
  - `def create_jwt(user_id) -> str`、`def decode_jwt(token) -> int`
  - `async def get_user_by_id(session, user_id) -> User`
- `backend/app/services/redemption_service.py`
  - `async def redeem(session, user_id, code) -> tuple[str, str, int]`（事务：行锁 → 校验 remaining > 0 → -1 → 写 record → 返回 base_url, api_key, remaining_after）
- `backend/app/services/llm_credentials_cache.py`
  - 模块级单例 dict + asyncio.Lock
  - `set_credentials(user_id: int, base_url: str, api_key: str, ttl_seconds: int = 86400)`
  - `get_credentials(user_id: int) -> dict | None`
  - `clear_credentials(user_id: int)`
  - 内部带过期清理（懒清理：get 时检查 expires_at）
- `backend/app/services/llm_validator.py`
  - `async def validate_credentials(base_url: str, api_key: str) -> dict[str, Any]`
  - 实现：`httpx.AsyncClient(timeout=8.0)` GET `{base_url}/models` (Bearer api_key) → 200 OK 即 valid；非 200 时回退 POST `{base_url}/chat/completions` body `{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"ping"}],"max_tokens":1}` → 任一 200 即 valid；返回 `{"valid": bool, "message": str}`
- `backend/app/agents/llm_factory.py`
  - `class LLMFactory`
    - `@staticmethod def build_for_user(user_id: int, *, model: str | None = None, temperature: float = 0.7) -> BaseChatModel | None`
      - 从 `llm_credentials_cache.get_credentials(user_id)` 读
      - 无 → 返回 None（router 层据此决定走 mock）
      - 有 → `ChatOpenAI(api_key=..., base_url=..., model=settings.openai_model, temperature=temperature)`
- `backend/app/dependencies.py`
  - `def get_current_user_id(authorization: str = Header(...)) -> int`：解析 `Bearer <jwt>` → `decode_jwt`
  - `async def get_current_user(uid: int = Depends(get_current_user_id), session = Depends(get_db)) -> User`
  - `def get_user_llm(temperature: float = 0.7) -> Callable`：返回 dependency 闭包，闭包接受 `user_id = Depends(get_current_user_id)` 调 `LLMFactory.build_for_user(user_id, temperature=temperature)`
- `backend/app/routers/auth.py`
  - `POST /api/auth/register` body `{username, password}` → 201
  - `POST /api/auth/login` body `{username, password}` → `{access_token, token_type:"bearer", user:{id, username}}`
  - `GET /api/auth/me` → `{id, username, has_session_credentials, credentials_expires_at, redemption_history:[{code, redeemed_at}]}`
  - `POST /api/auth/redeem` body `{code}` → 调 `redeem` + 调 `set_credentials`，返回 `{success, remaining_quota, message}`
  - `POST /api/auth/llm/validate` body `{base_url, api_key}` → 调 `validate_credentials`（不写任何存储）
  - `POST /api/auth/llm/config` body `{base_url, api_key}` → 先 validate，通过后调 `set_credentials`（仅内存）
  - `POST /api/auth/logout` → 调 `clear_credentials(user_id)`（前端清 localStorage）
- `backend/scripts/generate_redemption_codes.py`
  - CLI: `python -m scripts.generate_redemption_codes --count 50 --base-url https://api.openai.com/v1 --api-key sk-... --quota 10`
  - 用 `secrets.choice` 从 `BCDFGHJKMPQRTVWXY2346789` 字符集生成 `SHERLOCK-XXXX-XXXX`，去重写入 SQLite

### 1.4.3 修改文件

- **`backend/app/main.py`**：
  - lifespan 中执行 `await create_tables()`（首次自动建表，避免引入 alembic）
  - 注册 `auth.router`
  - CORS 暴露 `Authorization` 头
- **`backend/app/config.py`**：
  - 新增 `jwt_secret: str = "CHANGE_ME_IN_PROD"`（从 env 读）
  - 新增 `jwt_algorithm: str = "HS256"`
  - 新增 `jwt_expires_minutes: int = 60 * 24 * 7`（一周）
  - 新增 `auth_db_path: str = "data/auth.db"`
- **5 个 Agent 文件**（`watson_agent.py / suspect_agent.py / scene_agent.py / oracle_agent.py / case_generator_agent.py`）：
  - 移除 `__init__` 中 `self.llm = ChatOpenAI(...)` 与 `from app.config import get_settings` 中 settings 的 LLM 部分
  - 所有公开异步方法增加 `llm: BaseChatModel | None = None` 参数（位置参数加在末尾，保持向后兼容）
  - 内部判断：`if llm is None: <现有 mock 降级路径>`
  - 调用链：`chain = prompt | llm | parser`（用入参 llm，不再 self.llm）
- **`backend/app/routers/game.py`** 所有路由：
  - 增加 `current_user_id: int = Depends(get_current_user_id)`
  - 调用各 Agent 方法时构造 LLM：`llm = LLMFactory.build_for_user(current_user_id, temperature=0.7)`（CaseGenerator 用 0.8, Watson chat 用 0.7, Suspect 用 0.6 等，按现有温度配置查表）
  - 把 `llm` 透传给 Agent 方法
  - **注意**：现有路由如 `POST /api/game/new` 此前不需要鉴权；本任务起所有路由需要 JWT。前端 axios 拦截器自动注入。
- **`backend/app/services/game_service.py`**：
  - `create_game(difficulty, user_id: int | None = None)` 增加 `user_id` 参数
  - `GameState` 增加可选字段 `owner_user_id: int | None`（在 `backend/app/models/game.py` 加）
  - 后续如不实施任务 2 的存档功能，此字段仅做日志归属

### 1.4.4 全局降级路径保护

- 任何 Agent 在 `llm is None` 时必须返回原本 mock 路径的产物，**不可抛 500**
- `llm_credentials_cache.get_credentials` 返回 None 时 `LLMFactory.build_for_user` 返回 None
- 前端在用户未登录时拦截到 401 → 跳回 `/login`

## 1.5 前端改造点

### 1.5.1 路由调整（`frontend/src/App.tsx`）

```
新增路由：
  /login          → LoginPage
  /register       → RegisterPage
  /config         → ConfigPage（兑换码 + OpenAI 凭证）
受保护路由（包裹 <RequireAuth>）：
  /                    → StartPage（仅难度选择 + 进游戏）
  /investigation/...   → 现有
  /interrogation/...   → 现有
  /deduction/...       → 现有
  /conclusion/...      → 现有
```

### 1.5.2 新增文件

- `frontend/src/services/auth.ts`
  - `authApi.register(username, password)`
  - `authApi.login(username, password) -> {accessToken, user}`
  - `authApi.me() -> UserMe`
  - `authApi.redeem(code) -> {remainingQuota, message}`
  - `authApi.validateLLM(baseUrl, apiKey) -> {valid, message}`
  - `authApi.saveLLM(baseUrl, apiKey) -> {ok}`
  - `authApi.logout()`
- `frontend/src/store/authStore.ts`（Zustand + persist 仅 token & user）
  - state: `token`, `user`, `hasSessionCredentials`, `credentialsExpiresAt`, `validationStatus: 'idle'|'validating'|'valid'|'invalid'`, `validationMessage`, `redemptionMessage`
  - actions: `login`, `register`, `logout`, `refreshMe`, `redeem`, `validateLLM`, `saveLLM`
- `frontend/src/components/auth/RequireAuth.tsx`：检查 `authStore.token`，无则 `<Navigate to="/login" replace />`
- `frontend/src/pages/LoginPage.tsx`：用户名 + 密码 + 登录按钮 + 跳注册链接
- `frontend/src/pages/RegisterPage.tsx`：用户名 + 密码 + 确认密码 + 注册按钮
- `frontend/src/pages/ConfigPage.tsx`：
  - **兑换码区**：输入框 `code` + "兑换"按钮 → `authStore.redeem` → toast 显示剩余次数
  - **OpenAI 凭证区**：`baseUrl` 输入框 + `apiKey` 输入框 + "验证"按钮 + "提交"按钮
    - "验证"：调 `validateLLM`，按结果切换 validationStatus（按钮文案/颜色随状态变）
    - "提交"按钮：仅 `validationStatus==='valid'` 时启用 → 调 `saveLLM` → toast "已生效（本次会话有效）"
  - 顶部显示 "已配置：是/否，过期时间：xxx"
  - 底部"开始探案"按钮 → `navigate('/')`

### 1.5.3 修改文件

- **`frontend/src/services/api.ts`**：
  - 请求拦截器追加：`config.headers['Authorization'] = "Bearer " + useAuthStore.getState().token`（token 存在时）
  - 响应拦截器：401 → `useAuthStore.getState().logout()` + `window.location.href='/login'`
- **`frontend/src/pages/StartPage.tsx`**：
  - 顶部增加 "用户：xxx ｜ 凭证：✅/⚠️未配置 ｜ [配置] [登出]" 三个链接/按钮
  - "着手探案" 按钮：若 `!hasSessionCredentials` 则禁用并提示 "请先到 [配置页] 兑换或填写 OpenAI 凭证"
  - 现有 `handleStartGame` 流程不动
- **`frontend/src/index.css`**：
  - 新增 `.auth-page`, `.auth-form`, `.auth-input`, `.auth-button`（复用 `#d4af37` 金边、`Cinzel` 字体、`rgba(50,35,20,0.85)` 背景）
  - 新增 `.config-section`, `.config-input-group`, `.config-status-badge--valid/invalid/idle`
- **`frontend/src/store/storeManager.ts`**：
  - `resetAll()` 不清 `authStore`（登录态跨游戏保持）；增加 `logoutAndReset()` 同时清 auth + 所有游戏 store

## 1.6 数据流时序

```
[注册/登录]
  POST /api/auth/register {username, password} → bcrypt → INSERT users
  POST /api/auth/login → 校验 → JWT → 返回 {access_token, user}
  前端 authStore.login → 写 localStorage[sherlock_token]
  axios 拦截器自动注入 Authorization

[兑换码]
  ConfigPage 用户点"兑换" → POST /api/auth/redeem {code}
  → 后端事务：BEGIN → SELECT ... FOR UPDATE redemption_codes WHERE code=? AND remaining_quota>0
                  → UPDATE remaining_quota = remaining_quota - 1
                  → INSERT redemption_records (user_id, code)
                  → set_credentials(user_id, base_url, api_key, ttl=86400)
                  → COMMIT
  → 返回 {success: true, remaining_quota: 9}

[手动凭证]
  用户输入 baseUrl/apiKey → 点"验证"
  → POST /api/auth/llm/validate → httpx GET {baseUrl}/models（fallback /chat/completions）
  → 返回 {valid:true, message:"已识别 12 个模型"}
  → 前端按钮变金色"通过验证 ✓" → "提交"按钮启用
  用户点"提交" → POST /api/auth/llm/config → 再次 validate → set_credentials
  → 返回 {ok:true}

[业务调用]
  POST /api/game/new (Authorization: Bearer ...)
  → get_current_user_id Depends → uid
  → llm = LLMFactory.build_for_user(uid, temperature=0.8)
  → 缓存命中 → ChatOpenAI 实例
  → CaseGeneratorAgent.generate_case(difficulty="classic", llm=llm)
  → invoke_with_retry(chain, ...)

[过期/无凭证]
  llm is None → Agent 走原 mock 降级 → 返回 mock 案件 → 不报错
  前端可在 StartPage 顶部展示"凭证已过期，请重新配置"
```

## 1.7 风险与边界

- **JWT 密钥泄露**：`jwt_secret` 必须从环境变量读，部署文档明确告知
- **bcrypt 性能**：cost=12 单次约 100ms，登录可接受；注册同
- **凭证内存丢失**：进程重启即丢，前端检测 401 → 跳配置页重填
- **兑换码并发**：SQLite 写锁串行化天然防双扣；事务 BEGIN IMMEDIATE
- **api_key 泄露**：响应中只在 `me` 接口返回 `has_session_credentials` 与 `expires_at`，**绝不回传 api_key 明文**
- **mock 模式**：用户跳过验证、直接进游戏 → 所有 LLM 走 mock 降级（保留现状），UI 须在游戏页面提示"当前为示例模式（无凭证）"

## 1.8 验证步骤（端到端）

1. `pip3 install -r requirements.txt`，启动后端 → 自动建 SQLite 表
2. `python -m scripts.generate_redemption_codes --count 5` → 控制台打印 5 个码
3. 启动前端 → 访问 `/` → 重定向到 `/login`
4. 注册 `alice/alice123` → 登录 → 跳到 `/` 起始页
5. StartPage 顶部"凭证：⚠️未配置" → 点"配置" → 跳 `/config`
6. 兑换某码 → toast "已兑换，剩余 9 次" → "凭证：✅" 出现
7. 输 baseurl 错的 + apikey 错的 → 验证 → 显示"无效：401 Unauthorized"
8. 输正确凭证 → 验证 → 通过 → "提交" → toast "已生效"
9. 回首页 → "着手探案" → 后端日志看到 `[LLMFactory] build_for_user uid=1 base_url=... 命中`
10. 退出登录 → 重新登录 → 凭证应为"未配置"（内存丢失，符合一次性约束）
11. 删除用户 sqlite 文件 → 重启 → 自动重建表 → 老 token 401

---

# 任务 2：数据库接入 — 仅设计文档（不实施）

> ⚠️ 本任务**不动任何代码**，仅在 `docs/database-design.md` 输出设计文档供后续工单实施。

## 2.1 设计目标

- 解决数据丢失：用户、兑换码、游戏存档需持久化到 PostgreSQL
- "存档/读档"按钮闭环：前端任意时刻打快照 → 后端落 jsonb；前端从存档列表加载 → 后端反序列化 → 内存恢复
- 与任务 1 SQLite 平滑迁移：将 `users`、`redemption_codes`、`redemption_records` 三表迁到 PG，模式相同

## 2.2 文档结构（落地于 `docs/database-design.md`）

文档需包含以下章节：

### 2.2.1 总览与边界
- 选型：PostgreSQL 16 + SQLAlchemy 2.0 (asyncio) + asyncpg + alembic
- 不重构 `GameService._games` 内存字典，DB 仅承载"按需快照"
- 单库多表，无多租户隔离

### 2.2.2 表结构 DDL
完整 SQL，涵盖：
- `users`（接续任务 1：username/password_hash + 可选 email、last_login_at）
- `redemption_codes`（同任务 1 字段；可加 `created_by_admin_id`）
- `redemption_records`
- `game_saves`：
  ```sql
  CREATE TABLE game_saves (
    id              uuid PK DEFAULT gen_random_uuid(),
    user_id         uuid REFERENCES users(id) ON DELETE CASCADE,
    game_id         varchar(64) NOT NULL,    -- 业务 game_id
    name            varchar(128),            -- 用户起的存档名
    difficulty      varchar(16),
    phase           varchar(32),
    snapshot_version int NOT NULL DEFAULT 1,
    snapshot_json   jsonb NOT NULL,          -- 全量快照（backend + frontend）
    created_at      timestamptz DEFAULT now(),
    updated_at      timestamptz DEFAULT now()
  );
  CREATE INDEX ix_game_saves_user ON game_saves(user_id);
  CREATE INDEX ix_game_saves_phase ON game_saves(phase);
  ```
- `llm_credentials`（**可选**：若未来想从"一次性"改为"持久"，预留此表）：
  ```sql
  CREATE TABLE llm_credentials (
    user_id         uuid PK REFERENCES users(id) ON DELETE CASCADE,
    base_url        text NOT NULL,
    api_key_enc     bytea NOT NULL,        -- 用 pgcrypto 加密
    updated_at      timestamptz DEFAULT now()
  );
  ```

### 2.2.3 ORM 模型示例代码（不入仓）
- 给出 `class User(Base)`、`class GameSave(Base)` 的 SQLAlchemy 2.0 Mapped 风格示意
- `relationship` 反向引用示例

### 2.2.4 alembic 迁移方案
- `alembic init alembic`
- `env.py` 适配 async engine：用 `engine.sync_engine` connect 给 alembic
- 初始 migration `0001_initial.py` 一次建齐 4 张表
- 后续模型升级：每张表迁移独立 revision，`snapshot_json` 用 `op.execute` 跑数据迁移

### 2.2.5 snapshot_json 结构
```jsonc
{
  "version": 1,
  "backend": {
    "game": { /* GameState dump */ },
    "deduction_chain": { /* DeductionChain dump */ },
    "watson_chat_history": [ /* WatsonChatMessage dump */ ]
  },
  "frontend": {
    "clues": { /* useCluesStore.getState() */ },
    "deduction": { /* useDeductionStore.getState() */ },
    "interrogation": { /* useInterrogationStore.getState() */ },
    "watsonChat": { /* useWatsonChatStore.getState() */ },
    "sceneChat": { /* useSceneChatStore.getState() */ },
    "ui": { "watsonDialogPosition": {...} }
  }
}
```
- 字段命名：backend 全 snake_case，frontend 全 camelCase（与各 store 内部一致）

### 2.2.6 API 设计
| 方法 | 路径 | body | 返回 |
|---|---|---|---|
| POST | `/api/saves` | `{game_id, name?, frontend_snapshot}` | `{save_id, created_at}` |
| GET  | `/api/saves` | – | `[{id, game_id, name, phase, difficulty, updated_at}]` |
| GET  | `/api/saves/{save_id}` | – | 完整 snapshot |
| POST | `/api/saves/{save_id}/load` | – | `{game_id_new, frontend_snapshot}` |
| DELETE | `/api/saves/{save_id}` | – | 204 |
- 全部需 JWT 鉴权（来自任务 1）

### 2.2.7 GameService 适配
设计两个新方法（设计文档级，不实现）：
- `to_snapshot(game_id) -> dict`：聚合 `_games[game_id]` + `_deduction_chains[game_id]` + `_watson_chat_history[game_id]`
- `from_snapshot(snapshot) -> str`：写入内存 dict，返回新 game_id（避免与已有冲突）

### 2.2.8 前端适配设计
- `frontend/src/services/saves.ts`：`savesApi.save/list/load/delete`
- `frontend/src/components/SaveLoadDialog.tsx`：模态框含 Tab 切换
- `frontend/src/store/storeManager.ts` 新增 `createFullSnapshot()` / `restoreFromSnapshot(gameId, frontendSnapshot)`
- StartPage / InvestigationPage 新增"存档"、"读档"按钮入口

### 2.2.9 风险点与回滚策略
- **snapshot 模型漂移**：版本号 + 迁移函数链
- **大 jsonb**：> 1MB 触发警告日志；超大可在任务 4 摘要后再存
- **多 worker 共享内存丢失**：本设计不解决，列入未来工单
- **从 SQLite 迁 PG**：提供 `scripts/migrate_sqlite_to_pg.py` 设计骨架（pandas / pure SQL 二选一）

### 2.2.10 部署变更
- `requirements.txt` 增加：`sqlalchemy>=2.0`、`asyncpg>=0.29`、`alembic>=1.13`、`psycopg2-binary`
- `.env.example` 增加 `DATABASE_URL=postgresql+asyncpg://sherlock:sherlock@localhost:5432/sherlock`
- `config.py` 增加 `database_url` 字段

## 2.3 交付物

- 唯一交付：`docs/database-design.md` 一份完整设计文档（中文）
- 文档篇幅约 2000-3000 字
- 包含至少 1 张 ER 图（mermaid 语法）
- **不修改任何源码**，不安装新依赖

## 2.4 验证（仅文档评审）

- 自评 checklist：
  - [ ] 4 张表 DDL 完整
  - [ ] alembic env.py async 适配示例完整
  - [ ] snapshot_json 结构示例完整
  - [ ] 5 个 API 端点完整签名
  - [ ] 与任务 1 SQLite 表的字段映射一致
  - [ ] 风险点 ≥ 4 条
- 后续工单创建时直接引用本文档章节

---

# 任务 3：Docker + docker-compose（独立实现）

## 3.1 设计目标

- 一条 `docker compose up` 启动 backend + frontend
- 每端独立 Dockerfile，可单独 build & 部署
- **不含 postgres**（任务 2 不实施）；任务 1 SQLite 文件通过 volume 挂载持久化
- Makefile 简化常用命令
- 仅保证本地 dev 一键启动；不做 prod 级反代/TLS

## 3.2 关键架构决策

| 决策 | 理由 |
|---|---|
| 后端 `python:3.11-slim` | 与本地 venv 一致，体积小 |
| 前端多阶段：`node:20-alpine` build → `nginx:1.27-alpine` serve | 最终镜像 < 30MB |
| SQLite 文件用 named volume `auth_data` 挂到 `/app/data` | 保留任务 1 用户/兑换码数据 |
| backend 用非 root 用户 | 安全 |
| 前端 `VITE_API_BASE_URL` build-arg 注入 | Vite 编译期写入 |
| backend healthcheck `/health`，frontend healthcheck `wget /` | 启动顺序保障 |
| 不内置 alembic 启动（任务 2 不实施） | 启动只跑 uvicorn |

## 3.3 新增文件

### 3.3.1 `backend/Dockerfile`
```
FROM python:3.11-slim AS base
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY app ./app
COPY scripts ./scripts
RUN mkdir -p /app/data \
 && useradd -m sherlock \
 && chown -R sherlock /app
USER sherlock
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.3.2 `frontend/Dockerfile`
```
# Stage 1: build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Stage 2: serve
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD wget -q -O - http://localhost/ >/dev/null 2>&1 || exit 1
```

### 3.3.3 `frontend/nginx.conf`
```
server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;

  gzip on;
  gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

  location / {
    try_files $uri $uri/ /index.html;
  }
}
```

### 3.3.4 `docker-compose.yml`（项目根）
```yaml
version: "3.9"
services:
  backend:
    build:
      context: ./backend
    image: sherlock-backend:dev
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      OPENAI_BASE_URL: ${OPENAI_BASE_URL:-https://api.openai.com/v1}
      OPENAI_MODEL: ${OPENAI_MODEL:-gpt-4-turbo-preview}
      JWT_SECRET: ${JWT_SECRET:-change-me-in-prod}
      JWT_EXPIRES_MINUTES: ${JWT_EXPIRES_MINUTES:-10080}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      AUTH_DB_PATH: /app/data/auth.db
    ports:
      - "8000:8000"
    volumes:
      - auth_data:/app/data
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_BASE_URL: ${VITE_API_BASE_URL:-http://localhost:8000}
    image: sherlock-frontend:dev
    ports:
      - "5173:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped

volumes:
  auth_data:
```

### 3.3.5 `.env.example`（项目根）
```
# Backend
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo-preview
JWT_SECRET=please-change-me-32-chars-or-more
JWT_EXPIRES_MINUTES=10080
LOG_LEVEL=INFO

# Frontend (build-time)
VITE_API_BASE_URL=http://localhost:8000
```

### 3.3.6 `Makefile`（项目根）
```
.PHONY: up down logs build rebuild seed shell-backend shell-frontend clean

up:        ; docker compose up -d
down:      ; docker compose down
logs:      ; docker compose logs -f --tail=200
build:     ; docker compose build
rebuild:   ; docker compose build --no-cache
seed:      ; docker compose exec backend python -m scripts.generate_redemption_codes --count 20
shell-backend:  ; docker compose exec backend bash
shell-frontend: ; docker compose exec frontend sh
clean:     ; docker compose down -v
```

### 3.3.7 `.dockerignore`
- `backend/.dockerignore`：
  ```
  venv/
  __pycache__/
  *.pyc
  .pytest_cache/
  tests/
  data/
  .env
  ```
- `frontend/.dockerignore`：
  ```
  node_modules/
  dist/
  .vite/
  .env
  ```

## 3.4 修改文件

- 项目根 `.gitignore`：追加 `.env`（避免误提交真实密钥）
- `backend/.gitignore`：追加 `data/*.db`、`data/*.db-journal`
- `README.md`：新增「Docker 一键启动」章节，包含：
  - `cp .env.example .env` 编辑密钥
  - `make build && make up`
  - 访问 `http://localhost:5173`
  - `make seed` 灌兑换码
  - `make logs` 看日志
  - `make clean` 清理（含 SQLite 数据卷）

## 3.5 数据流时序

```
make build
  → docker 拉镜像 + 多阶段构建
make up
  → backend 启动 → 自动建 SQLite 表 → uvicorn → /health 200
  → frontend nginx 启动 → 静态文件可访问
浏览器 → http://localhost:5173
  → SPA 加载 → axios → http://localhost:8000/api/...
  → backend → SQLite (named volume)
make seed
  → 进 backend 容器跑生成脚本 → 控制台打印兑换码
make clean
  → 停容器 + 删 named volume → 数据清零
```

## 3.6 风险与边界

- **arm64 兼容**：所有镜像（python:3.11-slim、node:20-alpine、nginx:1.27-alpine）都有 multi-arch，Apple Silicon 直接可用
- **端口冲突**：8000、5173 与本地服务冲突时改 `ports` 映射
- **VITE_API_BASE_URL**：build-time 写死，更换地址需 `make rebuild`
- **JWT_SECRET 默认值**：必须在 README 强调"prod 必改"
- **SQLite 多 worker**：当前 uvicorn 默认单 worker，安全；若加 `--workers N` 须改任务 2 的 PG 方案
- **frontend → backend 走浏览器**：浏览器 fetch 直接打 `localhost:8000`，无需容器内代理；故未配置 nginx /api proxy（保持极简）
- **CORS**：backend 必须允许 `http://localhost:5173`

## 3.7 验证步骤

1. `cp .env.example .env`，编辑 JWT_SECRET
2. `make build` → 看到 backend & frontend 镜像构建完成
3. `make up` → `docker compose ps` 看到两个 healthy
4. `curl http://localhost:8000/health` → `{"status":"healthy"}`
5. 浏览器访问 `http://localhost:5173` → 起始页
6. `make seed` → 生成兑换码
7. 注册/登录/兑换/进游戏 → 全流程正常
8. `make down` → 再 `make up` → SQLite 数据持久（用户仍在）
9. `make clean` → 数据清零

---

# 任务 4：Agent 上下文大小管理（独立实现）

## 4.1 设计目标

- 防止任意 Agent 调用因累积历史/线索过大而超过 LLM context window
- 策略：**tiktoken 计数 + 旧历史 LLM 摘要 + 近窗保留**
- 集中提供 `context_manager` 工具模块；5 个 Agent 调用前先消费它
- 失败降级：摘要 LLM 调用失败 → 回退硬截断
- 与任务 1 共生：当 LLM 实例由 `LLMFactory.build_for_user` 注入时，摘要也复用同一 LLM；mock 模式跳摘要走截断

## 4.2 关键架构决策

| 决策 | 理由 |
|---|---|
| `tiktoken` `cl100k_base` 估算 | 主流 OpenAI 模型通用；第三方代理近似可接受 |
| `model_max_tokens × 0.8 - completion_reserve(=1500)` 作为软上限 | 留 20% 给 system prompt + 输出 |
| 默认保留最近 8 条 message（约 4 轮 QA） | 维持上下文连贯 |
| 摘要 LLM 调用 `temperature=0.3` | 稳定 |
| 摘要按 `(game_id, scope)` 内存缓存 + 增量更新（记录 `covered_until_index`） | 避免反复摘要 |
| `MODEL_CONTEXT_TABLE` 字典维护各 model 上下文长度，未知兜底 8000 | 安全保守 |
| 对**线索/嫌疑人/场景** 拼接 block 也截断 | prompt 中的 list 也会爆 |
| 不动 OracleAgent / CaseGeneratorAgent | 输入有限 |
| 提供单元测试 mock 摘要器 | 可重复验证 |

## 4.3 新增文件

### 4.3.1 `backend/app/agents/_context_manager.py`

```python
"""
Agent 上下文压缩工具：tiktoken 计数 + 摘要折叠 + 近窗保留
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from loguru import logger
import tiktoken
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.agents._llm_helpers import invoke_with_retry


class ContextScope(str, Enum):
    WATSON_CHAT = "watson_chat"
    SUSPECT_INTERROGATION = "suspect_interrogation"
    SCENE_SEARCH = "scene_search"
    CONTRADICTION_DETECTION = "contradiction_detection"


MODEL_CONTEXT_TABLE: dict[str, int] = {
    "gpt-4-turbo-preview": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
}
DEFAULT_MODEL_TOKENS = 8000


@dataclass
class ContextLimits:
    model_max_tokens: int = DEFAULT_MODEL_TOKENS
    completion_reserve: int = 1500
    safety_ratio: float = 0.8
    keep_recent_messages: int = 8

    @property
    def soft_input_limit(self) -> int:
        return int(self.model_max_tokens * self.safety_ratio) - self.completion_reserve


# (game_id) -> { scope -> { covered_until: int, summary: str } }
_summary_cache: dict[str, dict[str, dict[str, Any]]] = {}


def get_limits_for_model(model: str | None) -> ContextLimits:
    if not model:
        return ContextLimits()
    return ContextLimits(
        model_max_tokens=MODEL_CONTEXT_TABLE.get(model, DEFAULT_MODEL_TOKENS)
    )


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    try:
        enc = tiktoken.get_encoding(encoding_name)
        return len(enc.encode(text))
    except Exception as e:
        logger.warning(f"[ContextManager] tiktoken 失败回退到字符估算: {e}")
        return len(text) // 3  # 粗略 3 字符 = 1 token


def count_messages_tokens(messages: list[dict]) -> int:
    return sum(
        count_tokens(m.get("content", "")) + 4   # 每条 message overhead
        for m in messages
    )


def truncate_messages(
    messages: list[dict],
    max_tokens: int,
    keep_recent: int = 8,
) -> tuple[list[dict], int]:
    """从头部开始丢弃，直到总 tokens ≤ max_tokens"""
    msgs = list(messages)
    removed = 0
    while count_messages_tokens(msgs) > max_tokens and len(msgs) > keep_recent:
        msgs.pop(0)
        removed += 1
    return msgs, removed


SUMMARIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是一个对话摘要助手。把下面的对话总结成 200 字以内的中文摘要，保留：\n"
     "1) 玩家做过的关键决策或问题\n"
     "2) NPC/角色透露的关键信息或矛盾\n"
     "3) 已发现线索的标签 ID 列表\n"
     "请用列表形式输出，不要写'摘要：'前缀。"),
    ("user", "{conversation_block}")
])


async def summarize_old_messages(
    messages: list[dict],
    llm: BaseChatModel,
    timeout: float = 15.0,
) -> str:
    if not messages:
        return ""
    block = "\n".join(f"[{m.get('role','user')}] {m.get('content','')}" for m in messages)
    chain = SUMMARIZE_PROMPT | llm | StrOutputParser()
    return await invoke_with_retry(
        chain=chain,
        inputs={"conversation_block": block},
        fallback_fn=lambda: "（早期对话历史已截断，未生成摘要）",
        max_retries=1,
        timeout=timeout,
    )


async def compress_chat_history(
    game_id: str,
    scope: ContextScope,
    messages: list[dict],
    llm: BaseChatModel | None,
    limits: ContextLimits | None = None,
) -> tuple[list[dict], Optional[str]]:
    """
    返回 (compressed_messages, summary_or_none)。
    压缩策略：
      1. 若总 tokens ≤ soft_input_limit → 原样返回
      2. 否则：把 messages[:-keep_recent] 走摘要器（增量缓存）
      3. llm 为 None 或摘要失败 → 直接硬截断
    """
    limits = limits or ContextLimits()
    total = count_messages_tokens(messages)
    if total <= limits.soft_input_limit:
        return messages, None

    keep = limits.keep_recent_messages
    if len(messages) <= keep:
        return messages, None

    old = messages[:-keep]
    recent = messages[-keep:]

    # 缓存命中
    cache_entry = _summary_cache.setdefault(game_id, {}).get(scope.value)
    if cache_entry and cache_entry.get("covered_until", 0) >= len(old):
        return recent, cache_entry["summary"]

    # 走摘要
    if llm is None:
        truncated, removed = truncate_messages(messages, limits.soft_input_limit, keep)
        logger.info(f"[ContextManager] mock 模式硬截断 {removed} 条 game={game_id} scope={scope}")
        return truncated, None

    try:
        summary = await summarize_old_messages(old, llm)
        _summary_cache.setdefault(game_id, {})[scope.value] = {
            "covered_until": len(old),
            "summary": summary,
        }
        logger.info(f"[ContextManager] 摘要完成 game={game_id} scope={scope} 旧={len(old)} → 新近={len(recent)}")
        return recent, summary
    except Exception as e:
        logger.warning(f"[ContextManager] 摘要失败回退截断: {e}")
        truncated, _ = truncate_messages(messages, limits.soft_input_limit, keep)
        return truncated, None


def truncate_block(text: str, max_tokens: int, marker: str = "…(已省略)…") -> str:
    if count_tokens(text) <= max_tokens:
        return text
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    head = enc.decode(tokens[: max_tokens - 10])
    return head + "\n" + marker


def filter_relevant_clues(clues: list, query: str, max_items: int = 12) -> list:
    """按 query 关键词命中分数排序后取 top N，永远保留 user_generated 与最近发现的"""
    query_words = set(query.lower().split())
    def score(c) -> int:
        text = (getattr(c, "description", "") or "") + " " + (getattr(c, "user_label", "") or "")
        return sum(1 for w in query_words if w in text.lower())
    must_keep = [c for c in clues if getattr(c, "user_generated", False)]
    rest = [c for c in clues if not getattr(c, "user_generated", False)]
    rest_sorted = sorted(rest, key=score, reverse=True)
    return (must_keep + rest_sorted)[:max_items]


def clear_cache_for_game(game_id: str) -> None:
    _summary_cache.pop(game_id, None)
```

### 4.3.2 `backend/tests/test_context_manager.py`

测试用例（pytest async）：
- `test_count_tokens_basic`：英文 / 中文字符数 vs token 数比值
- `test_truncate_messages_keeps_recent`：50 条 → max=200 → 头部被丢，最近 8 条保留
- `test_compress_under_limit_returns_original`：少量消息原样返回
- `test_compress_with_mock_llm`：用 `MockChatModel` 验证摘要被调用一次
- `test_compress_cache_hit_no_second_call`：第二次 compress 同 game_id+scope 不再调 LLM
- `test_compress_llm_none_fallback_truncate`：llm=None 时落硬截断分支
- `test_filter_relevant_clues`：query 命中关键词的优先

### 4.3.3 配置项 `backend/app/config.py` 追加

```python
# 上下文管理
context_safety_ratio: float = 0.8
context_keep_recent: int = 8
context_completion_reserve: int = 1500
context_summary_temperature: float = 0.3
```

### 4.3.4 依赖 `backend/requirements.txt` 追加

```
tiktoken>=0.7
```

## 4.4 受影响的 Agent 改造点

### 4.4.1 `WatsonAgent.chat`（自由对话）
- 文件：`backend/app/agents/watson_agent.py`
- 方法：`async def chat(self, user_message, context, game_id, llm)` 增加 `game_id`
- 在构造 inputs 前：
  ```python
  history = game_service.get_watson_chat_history(game_id)
  history_dicts = [{"role": m.role, "content": m.content} for m in history]
  compressed, summary = await compress_chat_history(
      game_id, ContextScope.WATSON_CHAT, history_dicts, llm,
      limits=get_limits_for_model(settings.openai_model)
  )
  ```
- 把 `summary`（若有）拼到 system prompt 顶部："## 早期对话摘要\n{summary}"
- `current_clues_block` / `available_scenes_block` / `suspects_block` 各用 `truncate_block(block, max_tokens=600/400/300)`

### 4.4.2 `WatsonAgent.detect_contradictions`
- 入参 `clues` 与 `suspect_statements` 转字符串后用 `truncate_block`
- `statements_block` 每个嫌疑人均分 token 配额

### 4.4.3 `WatsonAgent.offer_interrogation_tips`
- `conversation_history` 走 `compress_chat_history(SUSPECT_INTERROGATION)`
- `clues_block` 用 `filter_relevant_clues(clues, last_user_question, max=12)` 后再拼接

### 4.4.4 `SuspectAgent.generate_response`
- 文件：`backend/app/agents/suspect_agent.py`
- 方法签名增加 `game_id`
- `conversation_history` 走 `compress_chat_history(SUSPECT_INTERROGATION)`
- 若 summary 不空 → prepend `SystemMessage(content=f"早期对话摘要: {summary}")`

### 4.4.5 `SceneAgent.search`
- 文件：`backend/app/agents/scene_agent.py`
- 方法签名增加 `game_id`
- `_format_history` 内部用 `compress_chat_history(SCENE_SEARCH)` 替代当前 `history[-6:]` 硬切

### 4.4.6 GameService 集成
- 在 `create_game` 与 `from_snapshot`（如未来实现）开头调 `clear_cache_for_game(game_id)`，避免新游戏复用旧缓存

### 4.4.7 router 修改
- `backend/app/routers/game.py` 中以下端点 handler 调用 Agent 时透传 `game_id`：
  - `chat_with_watson` → `watson.chat(..., game_id=game_id)`
  - `ask_suspect_question` → `suspect.generate_response(..., game_id=game_id)`
  - `scene_search` → `scene.search(..., game_id=game_id)`
  - `get_interrogation_tips` → `watson.offer_interrogation_tips(..., game_id=game_id)`
  - `check_contradictions` → `watson.detect_contradictions(..., game_id=game_id)`

## 4.5 数据流时序（以 WatsonAgent.chat 为例）

```
POST /api/game/{game_id}/watson/chat
  → router 取 game_id, 注入 llm
  → game_service.add_watson_chat_message(role=user)
  → watson.chat(user_msg, context, game_id, llm)
    → history = game_service.get_watson_chat_history(game_id)  # 全量
    → compressed, summary = await compress_chat_history(
         game_id, WATSON_CHAT, history_dicts, llm)
       ├── count_messages_tokens > limit?
       │     ├── 否 → 直接返回 (history, None)
       │     └── 是 →
       │         ├── 缓存命中? 复用 summary
       │         └── 否 → summarize_old_messages(old, llm) → 写缓存
    → 拼 prompt：system_prompt + (summary 段) + compressed messages + 当前 user
    → invoke_with_retry → 返回响应
  → game_service.add_watson_chat_message(role=watson)
  → 返回 JSON
```

## 4.6 风险与边界

- **tiktoken 与第三方 API 模型不匹配**：估算偏差 ±20%，安全比 0.8 已留余量；监控 LLM 实际 token 使用率（可在 `invoke_with_retry` 加 `result.usage` 日志）
- **摘要质量退化**：长程摘要丢细节。对策：摘要 prompt 强制保留"线索 ID 列表 / 嫌疑人陈述要点 / 用户决策"
- **摘要 LLM 调用失败**：fallback 文本 "（早期对话历史已截断，未生成摘要）" + 硬截断
- **缓存内存膨胀**：`_summary_cache` 按 game_id key；建议加 LRU 上限 1000 game_id（python `functools.lru_cache` 不直接适用，可用 `cachetools.LRUCache`）；MVP 暂不加，列入未来工单
- **并发竞态**：同 game_id 同 scope 并发调用可能双重摘要。MVP 接受短暂双调用；如需严格可加 `asyncio.Lock` 字典 per (game_id, scope)
- **mock 模式（llm=None）**：直接硬截断，不调摘要；已覆盖 fallback
- **测试可重复性**：`tiktoken` 计数确定；摘要 LLM mock 化

## 4.7 验证步骤

1. `pip3 install tiktoken`
2. `pytest backend/tests/test_context_manager.py -v` → 7 个用例全绿
3. 启动 backend，进入游戏，反复与华生对话 30 轮（脚本：`for i in {1..30}; do curl -X POST .../watson/chat -d ...; done`）
4. 后端日志看到 `[ContextManager] 摘要完成 game=xxx scope=watson_chat 旧=22 → 新近=8`
5. 在 `invoke_with_retry` 加临时打印 `chain.get_prompts()` 的 token 数 → 始终 ≤ `model_max × 0.8`
6. 把 `context_safety_ratio` 调到 0.3 → 应触发更激进压缩；调到 0.99 → 接近原行为
7. 把 `OPENAI_API_KEY=""` 后重跑 → 走 mock 分支不崩溃，日志看到 "mock 模式硬截断"
8. （配合任务 1）登录用户 A 与用户 B 跑同 game_id 不可能（game_id 由 user 创建），缓存隔离自然

---

# 关键文件索引（供执行 agent 快速跳转）

## 任务 1
- 后端新增：`backend/app/db/{session.py,base.py}`、`backend/app/models/db.py`、`backend/app/services/{auth_service.py,redemption_service.py,llm_credentials_cache.py,llm_validator.py}`、`backend/app/agents/llm_factory.py`、`backend/app/dependencies.py`、`backend/app/routers/auth.py`、`backend/scripts/generate_redemption_codes.py`
- 后端修改：`backend/app/main.py`、`backend/app/config.py`、`backend/app/routers/game.py`、`backend/app/services/game_service.py`、`backend/app/models/game.py`、`backend/app/agents/{watson,suspect,scene,oracle,case_generator}_agent.py`、`backend/requirements.txt`
- 前端新增：`frontend/src/services/auth.ts`、`frontend/src/store/authStore.ts`、`frontend/src/components/auth/RequireAuth.tsx`、`frontend/src/pages/{LoginPage,RegisterPage,ConfigPage}.tsx`
- 前端修改：`frontend/src/services/api.ts`、`frontend/src/pages/StartPage.tsx`、`frontend/src/store/storeManager.ts`、`frontend/src/App.tsx`、`frontend/src/index.css`

## 任务 2
- 仅新增：`docs/database-design.md`

## 任务 3
- 新增：`backend/Dockerfile`、`frontend/Dockerfile`、`frontend/nginx.conf`、`docker-compose.yml`、`.env.example`、`Makefile`、`backend/.dockerignore`、`frontend/.dockerignore`
- 修改：`.gitignore`、`backend/.gitignore`、`README.md`

## 任务 4
- 新增：`backend/app/agents/_context_manager.py`、`backend/tests/test_context_manager.py`
- 修改：`backend/app/config.py`、`backend/requirements.txt`、`backend/app/agents/{watson,suspect,scene}_agent.py`、`backend/app/routers/game.py`

---

# 执行总结

| 任务 | 工作量预估 | 依赖 | 可独立执行 |
|---|---|---|---|
| 任务 1 | 3-4 天（后端 2 + 前端 1.5） | 无 | ✅ |
| 任务 2 | 0.5 天（仅文档） | 无 | ✅ |
| 任务 3 | 0.5 天 | 无（不依赖任务 2） | ✅ |
| 任务 4 | 1.5 天（实现 + 测试） | 弱依赖任务 1 的 LLMFactory | 可独立或在任务 1 之后做 |

四份计划均已详细到"另一个 agent 拿到即可执行"的颗粒度。
