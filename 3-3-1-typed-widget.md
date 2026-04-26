# 兑换码功能开发执行计划

## Context（背景与目标）

当前游戏入口直接进入难度选择页（`/`），任何人访问后端都可消耗 OpenAI 额度。MVP 需要一个最小化的访问门控：

- **生成接口** 提供 10 次使用配额的兑换码（绑定预配置的 OpenAI baseurl/apikey）
- **验证接口** 校验兑换码、扣减次数、为当前游戏会话绑定 OpenAI 配置
- **本地 JSON 文件** 持久化兑换码状态（无数据库依赖，符合 MVP 阶段）
- **登录页** 作为新的应用入口（`/`），验证通过后跳转到原难度选择页（`/start`）

预期收益：（1）控制 OpenAI 用量（每个兑换码 10 次硬上限）；（2）为后续接入数据库与多用户做铺垫；（3）记录"哪局游戏用了哪个兑换码"以便日后审计。

---

## 关键决策（用户已确认）

| 决策点 | 选择 | 含义 |
|--------|------|------|
| 配置生效粒度 | 每个游戏会话独立绑定 | `GameState` 携带 `openai_api_key`/`openai_base_url` 快照字段 |
| 生成接口权限 | 无权限校验 | MVP 直接暴露，靠部署网络隔离 |
| 绑定来源 | 始终绑定到 `settings.openai_api_key/base_url` | 兑换码生成时快照当前 settings 值 |
| 路由布局 | `/` = 登录页，`/start` = 难度选择页 | 在 `App.tsx` 新增 `RequireRedeem` 守卫 |

**实现取舍说明**：由于"始终绑定到 settings"，游戏会话内的 OpenAI 配置 = 全局 settings，**Agent 层无需改造**。`GameState.openai_api_key` 字段仅用于"逻辑绑定"快照（审计/未来扩展），现阶段 Agent 仍读取 `settings`。这是把"per-session 隔离"做轻的实用解。

---

## 后端实现

### 1. 数据存储：本地 JSON 文件
- 路径：`backend/data/redemption_codes.json`（新建 `data/` 目录）
- 结构：
  ```json
  {
    "codes": [
      {
        "code": "AB12-CD34-EF56",
        "max_uses": 10,
        "used_count": 0,
        "openai_api_key": "sk-...",
        "openai_base_url": "https://api.openai.com/v1",
        "created_at": "2026-04-26T10:00:00Z",
        "last_used_at": null
      }
    ]
  }
  ```
- `.gitignore` 追加 `backend/data/redemption_codes.json`（防止 apikey 入库）

### 2. 新建服务 `backend/app/services/redemption_service.py`
- 单例模式（参考 `game_service.py` 结构）
- 内部使用 `threading.Lock` 保证并发安全（避免使用次数竞态）
- 提供方法：
  - `generate_code() -> RedemptionCode`：生成 12 位字母数字兑换码（格式 `XXXX-XXXX-XXXX`），快照当前 `settings.openai_api_key/base_url`，写入 JSON
  - `validate_and_consume(code: str) -> RedemptionResult`：校验有效性 + 次数 → 扣减 `used_count` → 持久化 → 返回绑定的 baseurl/apikey
  - `get_remaining_uses(code: str) -> int`：查询剩余次数（不扣减）
  - 私有 `_load() / _save()`：JSON 文件读写，含原子写（写临时文件 + rename）

### 3. 新建数据模型 `backend/app/models/redemption.py`
- `RedemptionCode`：完整结构（含 apikey，仅服务内部使用）
- `RedemptionGenerateResponse`：生成接口返回（含 code、max_uses、created_at；**不返回 apikey**）
- `RedemptionVerifyRequest`：`{ code: str }`
- `RedemptionVerifyResponse`：`{ success: bool, remaining_uses: int, message: str, game_id?: str }`（**不返回 apikey**，避免暴露给前端）

### 4. 新建路由 `backend/app/routers/redemption.py`
- `POST /api/redemption/generate` → `RedemptionGenerateResponse`
- `POST /api/redemption/verify` → `RedemptionVerifyResponse`
  - 验证通过后**直接创建一个游戏会话**并把 baseurl/apikey 快照写入 `GameState`，返回 `game_id` 给前端
  - 这样前端凭 `game_id` 就能进入后续流程，避免在前端持有 apikey
- 在 `app/main.py` 注册：`app.include_router(redemption.router, prefix="/api/redemption", tags=["redemption"])`

### 5. 扩展 `GameState` 模型（`backend/app/models/game.py`）
- 新增字段（带默认值，向后兼容）：
  ```python
  openai_api_key: Optional[str] = None  # 兑换码绑定快照（不返回前端）
  openai_base_url: Optional[str] = None
  redemption_code: Optional[str] = None  # 审计用
  ```
- 在 API 响应序列化处通过 `model_dump(exclude={"openai_api_key"})` 过滤敏感字段，或在 router 层 `response_model_exclude` 排除

### 6. 扩展 `GameService.create_game()`（`backend/app/services/game_service.py`）
- 接受可选 `openai_api_key` / `openai_base_url` / `redemption_code` 参数
- 写入 `GameState` 对应字段
- `redemption_service.validate_and_consume()` 成功后调用 `game_service.create_game(...)` 并把绑定信息写入

---

## 前端实现

### 1. 新建页面 `frontend/src/pages/LoginPage.tsx`
- UI：兑换码输入框（自动 `XXXX-XXXX-XXXX` 格式化）+ 验证按钮
- 维多利亚哥特风格（复用现有 `start-page` 样式骨架，新增 `login-page` CSS 类）
- 验证失败显示错误提示；成功后：
  1. 写入 `localStorage`：`{ gameId, code, remainingUses, validatedAt }` (key: `redemption-session`)
  2. `navigate('/start')`
- 日志规范：`console.info('[LoginPage] 验证兑换码', { code: 'AB12-***' })`（脱敏）

### 2. 新建 API 方法（`frontend/src/services/api.ts`）
- `redemptionApi.verify(code: string): Promise<RedemptionVerifyResponse>`
- 类型放在 `frontend/src/types/redemption.ts`

### 3. 路由调整（`frontend/src/App.tsx`）
- `/` → `LoginPage`
- `/start` → `StartPage`（移动现有路由）
- 新增 `RequireRedeem` 包裹组件：检查 `localStorage.redemption-session` 存在 → 渲染子路由；否则 `<Navigate to="/" replace />`
- 保护范围：`/start`、`/investigation/*`、`/interrogation/*`、`/deduction/*`、`/conclusion/*`

### 4. StartPage 调整（`frontend/src/pages/StartPage.tsx`）
- 关键改动：`handleStartGame` 不再调用 `gameApi.createNewGame(difficulty)` 创建新游戏，而是**复用兑换码验证时已创建的 `gameId`**：
  - 读取 `localStorage.redemption-session.gameId`
  - 调用 `gameApi.setDifficulty(gameId, difficulty)` 后跳转
  - 若读不到 → 跳回 `/`
- 配套后端：检查 `set_difficulty` 端点是否支持已创建的 START 阶段游戏（路由层应已支持，需确认 `routers/game.py:POST /{gameId}/difficulty`）

### 5. 兑换码状态管理（轻量）
- 不引入新 store，直接使用 `localStorage` + 工具函数 `frontend/src/utils/redemptionSession.ts`：
  - `getRedemptionSession()` / `clearRedemptionSession()`
- StoreManager.clearAllGameSessions 时**保留** `redemption-session`（其前缀 `redemption-` 与 `game:` 不冲突）

---

## 关键文件清单

### 新建
- `backend/data/redemption_codes.json`（运行时生成，已 gitignore）
- `backend/app/services/redemption_service.py`
- `backend/app/models/redemption.py`
- `backend/app/routers/redemption.py`
- `backend/tests/test_redemption_service.py`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/types/redemption.ts`
- `frontend/src/utils/redemptionSession.ts`

### 修改
- `backend/app/main.py`（注册路由）
- `backend/app/models/game.py`（GameState 新增字段）
- `backend/app/services/game_service.py`（create_game 接受 openai 配置参数）
- `backend/app/routers/game.py`（响应排除 apikey 字段）
- `.gitignore`（追加 redemption_codes.json）
- `frontend/src/App.tsx`（路由 + RequireRedeem）
- `frontend/src/pages/StartPage.tsx`（复用 gameId）
- `frontend/src/services/api.ts`（新增 redemptionApi）
- `frontend/src/index.css`（login-page 样式）

---

## 复用的现有能力
- `app.config.get_settings()`：读取预配置 `openai_api_key/base_url`（兑换码快照来源）
- `loguru.logger`：所有关键节点日志（生成/验证/扣减）
- `pydantic.BaseModel`：Request/Response 模型
- `app.services.game_service.GameService.create_game()`：扩展形参后复用
- 前端 `axios apiClient` 拦截器（自动 snake_case ↔ camelCase 转换）
- 前端 `console.debug/info/warn/error` 日志规范

---

## 验证方式

### 后端单元测试（新建 `backend/tests/test_redemption_service.py`）
- 生成兑换码 → JSON 文件存在并含 `used_count: 0`
- 重复验证 10 次成功，第 11 次返回失败
- 不存在的兑换码返回失败
- 并发验证（多线程模拟）次数扣减正确（无超扣）

### 后端 API 冒烟（curl）
```bash
# 生成
curl -X POST http://localhost:8000/api/redemption/generate
# {"code":"AB12-CD34-EF56","max_uses":10,"used_count":0,"created_at":"..."}

# 验证
curl -X POST http://localhost:8000/api/redemption/verify -H "Content-Type: application/json" -d '{"code":"AB12-CD34-EF56"}'
# {"success":true,"remaining_uses":9,"message":"验证成功","game_id":"..."}

# 验证不存在
curl -X POST http://localhost:8000/api/redemption/verify -d '{"code":"INVALID"}'
# {"success":false,"remaining_uses":0,"message":"兑换码无效"}
```

### 前端端到端
1. `cd frontend && npm run dev` → 浏览器访问 `http://localhost:5173/`
2. 应自动展示登录页（不是难度选择页）
3. 输入后端生成的兑换码 → 点击验证 → 跳转 `/start`
4. 选择难度 → 进入勘查页 → 流程正常
5. 检查 `localStorage`：`redemption-session` 存在
6. 直接访问 `/start` 不带 session → 自动跳回 `/`
7. 同一兑换码连续验证 11 次：第 11 次失败提示

### 检查项
- `npm run typecheck` 全绿
- `cd backend && pytest backend/tests/test_redemption_service.py -v` 全绿
- `redemption_codes.json` 不会被 commit（验证 `.gitignore`）
- API 响应不包含 `openai_api_key` 字段（避免泄露）

---

## 风险与注意事项

| 风险 | 应对 |
|------|------|
| `redemption_codes.json` 含 apikey 被误提交 | `.gitignore` 必须先于功能上线 |
| 并发扣减导致超扣 | `RedemptionService` 内部 `threading.Lock` |
| 进程重启后兑换码状态丢失 | 每次写入 fsync，重启后从 JSON 加载 |
| API 响应泄露 apikey | 模型层 `model_dump(exclude=...)` + router 层 response_model 双保险 |
| 用户篡改 localStorage 绕过登录 | 后端真正鉴权在每个 game API 上验证 game_id 存在；前端守卫只是 UX |
