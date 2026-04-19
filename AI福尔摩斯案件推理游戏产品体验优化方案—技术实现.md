# AI 福尔摩斯案件推理游戏产品体验优化方案 — 技术实现

> **执行说明**：本文档面向后续执行 Agent。每一章为一个可独立验收的 Task，按章节顺序执行（章节 1 → 10）。每个 Task 的"验收标准"必须全部满足才能进入下一章。

---

## 章节 0 · 前置说明

### 0.1 上下文
- 项目根目录：`/Users/yinbo/AI_Project/ai_muder_mystery_3`
- 后端：FastAPI + LangChain（`backend/`）
- 前端：React + Vite + TypeScript + Zustand（`frontend/`）
- 现有 LLM 封装：`backend/app/agents/_llm_helpers.py` 的 `invoke_with_retry`
- 现有 Prompt 集中目录：`backend/app/agents/prompts/`

### 0.2 NPC 体系决定
本次新增/明确 3 类 NPC：
| NPC | Agent | 数据视角 | Temperature | 复用现有 Agent? |
|---|---|---|---|---|
| 华生（陪伴+提示） | `WatsonAgent`（已有，扩展方法） | 用户已发现的线索 | 0.5–0.7 | 是 |
| 场景 NPC（每场景一个） | `SceneAgent`（新增） | 当前场景 + 案件 | 0.4–0.6 | 否 |
| 全局视角裁决官 | `OracleAgent`（新增） | 完整 case（含 true_murderer_id） | 0.1–0.3 | 否 |

**职责单一原则**：`CaseGeneratorAgent` 只负责"生成案件"，不参与判定。

### 0.3 执行顺序
1. 章节 1：数据模型扩展（最底层，所有后续工作依赖）
2. 章节 2：OracleAgent
3. 章节 3：SceneAgent
4. 章节 4：CaseGeneratorAgent 升级（让案件包含 scenes）
5. 章节 5：后端 API
6. 章节 6：WatsonAgent 强化
7. 章节 7：前端改造（7.1 勘查 → 7.2 推理板 → 7.3 审讯）
8. 章节 8：测试
9. 章节 9：风险预案核对
10. 章节 10：交付清单核对

### 0.4 编码与日志规范（必须遵守）
- 后端：loguru，统一格式 `logger.info("[模块] 动作 字段=值")`
- 前端：`console.info('[组件名] 动作', { 数据 })`
- 后端类型注解 + Pydantic；前端严格 TS（开启 strict）
- 中文注释解释"为什么"

### 0.5 命名约定
- 后端字段：snake_case
- 前端字段：camelCase
- API JSON：snake_case（前端 axios 拦截器自动转换，已存在）

---

## 章节 1 · 数据模型扩展

**目标文件**：`backend/app/models/case.py`

### 1.1 新增 `SceneObject` 模型
在 `Suspect` 类后追加：

```python
class SceneObject(BaseModel):
    """场景中的可交互对象（如：办公桌、信件、保险柜）"""
    id: str
    name: str
    description: str
    hidden_clue_ids: List[str] = Field(default_factory=list)  # 该对象内藏的线索 id（可为空）
    search_hints: List[str] = Field(default_factory=list)     # 用户搜查时的引导提示
```

### 1.2 新增 `Scene` 模型
紧接 `SceneObject` 后：

```python
class Scene(BaseModel):
    """案件场景（如：被害人书房、贝克街客厅）"""
    id: str
    name: str
    description: str                                  # 场景文字描述
    atmosphere_image: Optional[str] = None            # 氛围图 URL 或占位符
    objects: List[SceneObject] = Field(default_factory=list)
    npc_persona: str = ""                             # 该场景 NPC 的人设（如"沉默的管家"）
```

### 1.3 扩展 `Clue`
在 `Clue` 类增加字段（保留默认值，向后兼容）：

```python
class Clue(BaseModel):
    # ... 已有字段 ...
    user_label: Optional[str] = None                  # 用户自定义命名
    source_type: str = "initial"                      # initial | scene | interrogation
    source_ref: Optional[str] = None                  # scene_id 或 suspect_id
    quoted_text: Optional[str] = None                 # 来源原文（审讯片段）
    user_generated: bool = False                      # 是否用户主动创建
```

### 1.4 扩展 `Case`
```python
class Case(BaseModel):
    # ... 已有字段 ...
    scenes: List[Scene] = Field(default_factory=list)
    # investigation_locations 保留，作为 [s.name for s in scenes] 的镜像
```

### 1.5 扩展 `Inference`
```python
class Inference(BaseModel):
    # ... 已有字段 ...
    clue_ids: List[str] = Field(default_factory=list)
    verification_result: Optional[str] = None         # correct | wrong | partial
    oracle_explanation: Optional[str] = None
    user_marked_important: bool = False
```

### 1.6 新增 `ReasoningRecord`（推理记录）
推理板的"推理记录"是 `Inference` 的视图层封装。后端不必新模型，前端用 `Inference` 直接渲染即可。但为了让 API 更清晰，新增一个语义别名：

```python
class ReasoningRecord(Inference):
    """推理记录 = 已经过 Oracle 验证的 Inference"""
    pass
```

### 1.7 验收标准
- `python -c "from app.models.case import Scene, SceneObject, Case, Clue, Inference, ReasoningRecord"` 成功
- 旧测试 `pytest backend/tests/test_difficulty.py` 全绿（兼容性验证）

---

## 章节 2 · 新增 OracleAgent

### 2.1 新增 `backend/app/agents/prompts/oracle_prompts.py`

```python
"""OracleAgent 的 Prompt 模板"""

ORACLE_SYSTEM = """你是案件世界的『裁决官』，掌握全部真相。
你的唯一职责：判断侦探的推理是否与既定事实吻合。
严格规则：
1. 仅基于给定的 case_truth 判断，不得编造
2. 输出 JSON，不输出散文
3. 不剧透未提及的真相片段，仅指出推理的"对/错/部分对"
4. 即使用户结论部分正确，也要明确标出"缺失的链条"
"""

VERIFY_INFERENCE_USER = """## 案件真相（保密，仅你可见）
{case_truth}

## 用户提交的推理
- 选用的线索:
{clues_block}
- 用户的推理结论:
{conclusion}

## 任务
判断该推理是否正确，输出 JSON:
{{
  "verdict": "correct" | "wrong" | "partial",
  "score": 0.0-1.0,
  "explanation": "面向侦探的反馈（不剧透未提及真相）",
  "missing_links": ["缺失的关键推理步骤"],
  "misused_clues": ["误用或误解的线索 id"]
}}
"""

VERIFY_ACCUSATION_USER = """## 案件真相（保密）
{case_truth}

## 侦探最终指认
- 被指认嫌疑人: {suspect_name} (id={suspect_id})
- 真凶 id: {true_murderer_id}
- 用户提供的推理记录依据:
{records_block}

## 任务
输出 JSON:
{{
  "is_correct": true|false,
  "score": 0.0-1.0,
  "verdict_explanation": "宣判文本（侦探读到的反馈）",
  "key_evidence_used": ["核心证据"],
  "missing_critical_evidence": ["未触及的关键证据"]
}}
"""
```

### 2.2 新增 `backend/app/agents/oracle_agent.py`

```python
"""全局视角裁决官 - 判定推理是否成立"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from loguru import logger

from app.models.case import Case, Clue, Inference
from app.agents._llm_helpers import invoke_with_retry
from app.agents.prompts.oracle_prompts import (
    ORACLE_SYSTEM,
    VERIFY_INFERENCE_USER,
    VERIFY_ACCUSATION_USER,
)


def _format_case_truth(case: Case) -> str:
    """把 case 序列化为裁决官可读的真相 block"""
    lines = [
        f"victim: {case.victim_name}",
        f"cause_of_death: {case.cause_of_death}",
        f"murder_method: {case.murder_method}",
        f"true_murderer_id: {case.true_murderer_id}",
        "suspects:",
    ]
    for s in case.suspects:
        lines.append(f"  - id={s.id} name={s.name} guilty={s.is_guilty} motive={s.motive}")
    lines.append("clues:")
    for c in case.clues:
        lines.append(
            f"  - id={c.id} type={c.clue_type} red_herring={c.is_red_herring} desc={c.description}"
        )
    return "\n".join(lines)


def _format_clues_block(clues: List[Clue]) -> str:
    return "\n".join(
        [f"  - id={c.id} label={c.user_label or c.description[:30]}" for c in clues]
    )


class OracleAgent:
    """裁决官：低温度、严格事实对齐"""

    def __init__(self, temperature: float = 0.2) -> None:
        self.temperature = temperature

    async def verify_inference(
        self,
        case: Case,
        clues: List[Clue],
        conclusion: str,
    ) -> Dict[str, Any]:
        logger.info(
            f"[OracleAgent] verify_inference 启动 clue_count={len(clues)} conclusion_len={len(conclusion)}"
        )
        user_prompt = VERIFY_INFERENCE_USER.format(
            case_truth=_format_case_truth(case),
            clues_block=_format_clues_block(clues),
            conclusion=conclusion,
        )
        result = await invoke_with_retry(
            system=ORACLE_SYSTEM,
            user=user_prompt,
            temperature=self.temperature,
            json_mode=True,
            fallback={
                "verdict": "partial",
                "score": 0.5,
                "explanation": "裁决官暂时不在，请稍后再试。",
                "missing_links": [],
                "misused_clues": [],
            },
        )
        logger.info(f"[OracleAgent] verify_inference 完成 verdict={result.get('verdict')}")
        return result

    async def verify_accusation(
        self,
        case: Case,
        suspect_id: str,
        reasoning_records: List[Inference],
    ) -> Dict[str, Any]:
        logger.info(
            f"[OracleAgent] verify_accusation 启动 suspect_id={suspect_id} record_count={len(reasoning_records)}"
        )
        suspect = next((s for s in case.suspects if s.id == suspect_id), None)
        records_block = "\n".join(
            [
                f"  - id={r.id} verdict={r.verification_result} content={r.content[:80]}"
                for r in reasoning_records
            ]
        )
        user_prompt = VERIFY_ACCUSATION_USER.format(
            case_truth=_format_case_truth(case),
            suspect_name=suspect.name if suspect else "未知",
            suspect_id=suspect_id,
            true_murderer_id=case.true_murderer_id or "",
            records_block=records_block or "  （无）",
        )
        result = await invoke_with_retry(
            system=ORACLE_SYSTEM,
            user=user_prompt,
            temperature=self.temperature,
            json_mode=True,
            fallback={
                "is_correct": (suspect_id == case.true_murderer_id),
                "score": 0.5,
                "verdict_explanation": "裁决官暂时不在，仅按真凶 id 给出降级判定。",
                "key_evidence_used": [],
                "missing_critical_evidence": [],
            },
        )
        logger.info(f"[OracleAgent] verify_accusation 完成 is_correct={result.get('is_correct')}")
        return result


_oracle_singleton: Optional[OracleAgent] = None


def get_oracle_agent() -> OracleAgent:
    global _oracle_singleton
    if _oracle_singleton is None:
        _oracle_singleton = OracleAgent()
    return _oracle_singleton
```

> **注意**：`invoke_with_retry` 当前签名以 `_llm_helpers.py` 实际定义为准；如签名为位置参数 `(prompt, system_prompt, ...)` 需作适配。执行 Agent 应先 `cat backend/app/agents/_llm_helpers.py` 校对参数名。

### 2.3 验收标准
- `python -c "import asyncio; from app.agents.oracle_agent import get_oracle_agent; print(get_oracle_agent())"` 输出非空
- 章节 8.1 单测全绿

---

## 章节 3 · 新增 SceneAgent

### 3.1 新增 `backend/app/agents/prompts/scene_prompts.py`

```python
SCENE_SYSTEM = """你是维多利亚时代某场景的 NPC（管家/目击者/沉默看守等）。
玩家是侦探，会用自然语言探索此处。
规则：
1. 只回答与本场景及其物体有关的问题
2. 当玩家明确"搜查/查看"某个对象时，返回该对象的描述
3. 如该对象藏有线索（hidden_clue_ids 非空），不要直接揭示线索内容，但要给出强烈暗示，并在 JSON 中标记 clue_candidate
4. 不要剧透其他场景或案件真相
5. 输出 JSON
"""

SCENE_SEARCH_USER = """## 当前场景
{scene_block}

## 本案可参考的线索（仅作参考，不可剧透）
{clue_block}

## 历史对话（最近 6 轮）
{history_block}

## 玩家最新提问
{query}

## 任务
返回 JSON:
{{
  "narrative": "你的回应（沉浸式，符合维多利亚风格）",
  "matched_object_ids": ["命中的 SceneObject id 列表"],
  "clue_candidates": [
    {{ "object_id": "...", "suggested_clue_id": "...", "hint": "用一句话提示该线索的存在" }}
  ]
}}
"""
```

### 3.2 新增 `backend/app/agents/scene_agent.py`

```python
"""场景 NPC - 引导玩家自然语言探索"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from loguru import logger

from app.models.case import Case, Scene
from app.agents._llm_helpers import invoke_with_retry
from app.agents.prompts.scene_prompts import SCENE_SYSTEM, SCENE_SEARCH_USER


def _format_scene(scene: Scene) -> str:
    lines = [f"name: {scene.name}", f"desc: {scene.description}", "objects:"]
    for o in scene.objects:
        hidden = "yes" if o.hidden_clue_ids else "no"
        lines.append(f"  - id={o.id} name={o.name} hidden_clue={hidden} desc={o.description}")
    return "\n".join(lines)


def _format_history(history: List[Dict[str, str]], limit: int = 6) -> str:
    recent = history[-limit:]
    return "\n".join([f"{m['role']}: {m['content']}" for m in recent]) or "（无）"


def _format_clues_for_scene(case: Case, scene: Scene) -> str:
    """仅暴露与该场景对象相关的线索元数据"""
    related_ids = {cid for o in scene.objects for cid in o.hidden_clue_ids}
    related = [c for c in case.clues if c.id in related_ids]
    return "\n".join([f"  - id={c.id} type={c.clue_type} desc={c.description}" for c in related]) or "（无）"


class SceneAgent:
    def __init__(self, temperature: float = 0.5) -> None:
        self.temperature = temperature

    async def search(
        self,
        scene: Scene,
        case: Case,
        query: str,
        history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        logger.info(f"[SceneAgent] search scene_id={scene.id} query_len={len(query)}")
        user_prompt = SCENE_SEARCH_USER.format(
            scene_block=_format_scene(scene),
            clue_block=_format_clues_for_scene(case, scene),
            history_block=_format_history(history),
            query=query,
        )
        result = await invoke_with_retry(
            system=SCENE_SYSTEM,
            user=user_prompt,
            temperature=self.temperature,
            json_mode=True,
            fallback={
                "narrative": "（场景陷入寂静，似乎暂时听不到任何回应）",
                "matched_object_ids": [],
                "clue_candidates": [],
            },
        )
        logger.info(f"[SceneAgent] search 完成 candidates={len(result.get('clue_candidates', []))}")
        return result


_scene_singleton: Optional[SceneAgent] = None


def get_scene_agent() -> SceneAgent:
    global _scene_singleton
    if _scene_singleton is None:
        _scene_singleton = SceneAgent()
    return _scene_singleton
```

### 3.3 验收标准
- 模块可导入
- 章节 8.2 单测全绿

---

## 章节 4 · CaseGeneratorAgent 升级

**目标文件**：
- `backend/app/agents/case_generator_agent.py`
- `backend/app/agents/prompts/case_prompts.py`

### 4.1 Prompt 修改要点
在 `case_prompts.py` 的 case 生成 system/user prompt 中追加：

```python
# 在 CASE_GENERATION_USER 中已有的 JSON Schema 上追加 scenes 字段
"""
...
"scenes": [
  {
    "id": "scene_xxx",
    "name": "书房",
    "description": "高高的红木书架...",
    "atmosphere_image": null,
    "npc_persona": "沉默的管家，对死者忠诚",
    "objects": [
      {
        "id": "obj_xxx",
        "name": "办公桌",
        "description": "胡桃木办公桌，抽屉半开",
        "hidden_clue_ids": ["clue_xxx"],
        "search_hints": ["仔细查看抽屉", "翻动桌上的纸张"]
      }
    ]
  }
]
"""
```

约束（写入 prompt）：
- 至少 3 个 scenes，每个 scene 含 3-6 个 objects
- 全部 case.clues 中的非 red_herring 线索必须有至少 1 个 object 引用
- red_herring 线索可以挂在 object 上或留空

### 4.2 `case_generator_agent.py` 修改
- LLM 解析 JSON 后填充 `case.scenes`
- 同步 `case.investigation_locations = [s.name for s in case.scenes]`
- Mock 降级路径：构造 2 个 scenes（"书房"、"客厅"），每个 2 个 objects，把 case.clues 平均挂上

### 4.3 验收标准
- 用 mock 降级（不设 OPENAI_API_KEY）创建 game：`POST /api/game/new` → 返回的 `case.scenes` 非空
- 每个非 red_herring clue 至少出现在某个 object.hidden_clue_ids 中
- 章节 8.4 测试通过

---

## 章节 5 · 后端 API 新增与改造

**目标文件**：
- `backend/app/routers/game.py`
- `backend/app/services/game_service.py`

### 5.1 新增 Request/Response 模型（`game.py` 顶部）

```python
class SceneSearchRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []


class AddClueRequest(BaseModel):
    user_label: str
    description: str
    source_type: str  # scene | interrogation
    source_ref: Optional[str] = None
    base_clue_id: Optional[str] = None  # 若是已有 case.clues 的"被发现"
    quoted_text: Optional[str] = None


class SubmitReasoningRequest(BaseModel):
    clue_ids: List[str]
    conclusion: str


class ExtractClueFromInterrogationRequest(BaseModel):
    suspect_id: str
    quoted_text: str
    context_messages: List[Dict[str, str]] = []
    user_label: str


class WatsonInterrogationTipsRequest(BaseModel):
    suspect_id: str
    conversation_history: List[Dict[str, str]] = []
```

### 5.2 改造 `MakeAccusationRequest`

```python
class MakeAccusationRequest(BaseModel):
    suspect_id: str
    reasoning_record_ids: List[str]   # 必填，1-3 条
    reasoning_steps: List[str] = []   # 兼容旧字段
```

### 5.3 新增端点

#### 5.3.1 场景搜索
```python
@router.post("/{game_id}/scene/{scene_id}/search")
async def scene_search(game_id: str, scene_id: str, request: SceneSearchRequest):
    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(404, "game/case 不存在")

    scene = next((s for s in game.case.scenes if s.id == scene_id), None)
    if not scene:
        raise HTTPException(404, f"scene 不存在: {scene_id}")

    from app.agents.scene_agent import get_scene_agent
    result = await get_scene_agent().search(
        scene=scene, case=game.case, query=request.query, history=request.history
    )
    return result
```

#### 5.3.2 添加自定义命名线索
```python
@router.post("/{game_id}/clues")
async def add_clue(game_id: str, request: AddClueRequest):
    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(404, "game/case 不存在")

    clue = game_service.add_user_clue(
        game_id=game_id,
        user_label=request.user_label,
        description=request.description,
        source_type=request.source_type,
        source_ref=request.source_ref,
        base_clue_id=request.base_clue_id,
        quoted_text=request.quoted_text,
    )
    return clue
```

`game_service.add_user_clue` 实现要点：
- 若 `base_clue_id` 命中已存在 clue：标记 `discovered=True`、写入 `user_label`、不重复创建
- 否则：新增 `Clue`，`id = "user_" + uuid4().hex[:8]`，`user_generated=True`
- 写回 `game.case.clues`

#### 5.3.3 组合推理（核心）
```python
@router.post("/{game_id}/deduction/reasoning")
async def submit_reasoning(game_id: str, request: SubmitReasoningRequest):
    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(404, "game/case 不存在")

    if not request.clue_ids:
        raise HTTPException(400, "至少选择 1 条线索")

    selected = [c for c in game.case.clues if c.id in request.clue_ids]
    if len(selected) != len(request.clue_ids):
        raise HTTPException(400, "存在无效的线索 id")

    # 调用 Oracle 验证
    from app.agents.oracle_agent import get_oracle_agent
    oracle_result = await get_oracle_agent().verify_inference(
        case=game.case, clues=selected, conclusion=request.conclusion
    )

    # 持久化为 Inference
    inference = game_service.create_inference(
        game_id=game_id,
        content=request.conclusion,
        observation_ids=[],
        parent_inference_ids=[],
    )
    inference.clue_ids = request.clue_ids
    inference.verification_result = oracle_result["verdict"]
    inference.oracle_explanation = oracle_result["explanation"]
    inference.confidence = float(oracle_result.get("score", 0.5))
    game_service.update_inference(game_id, inference)

    return {
        "inference": inference,
        "verification_result": oracle_result["verdict"],
        "score": oracle_result.get("score", 0.5),
        "explanation": oracle_result["explanation"],
        "missing_links": oracle_result.get("missing_links", []),
        "misused_clues": oracle_result.get("misused_clues", []),
    }
```

需要在 `game_service.py` 增加：
- `update_inference(game_id, inference)` 方法

#### 5.3.4 审讯片段生成线索
```python
@router.post("/{game_id}/interrogation/extract-clue")
async def extract_clue_from_interrogation(
    game_id: str, request: ExtractClueFromInterrogationRequest
):
    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(404, "game/case 不存在")

    clue = game_service.add_user_clue(
        game_id=game_id,
        user_label=request.user_label,
        description=request.quoted_text,
        source_type="interrogation",
        source_ref=request.suspect_id,
        quoted_text=request.quoted_text,
    )
    return clue
```

#### 5.3.5 华生审讯实时提示
```python
@router.post("/{game_id}/interrogation/watson-tips")
async def watson_interrogation_tips(
    game_id: str, request: WatsonInterrogationTipsRequest
):
    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(404, "game/case 不存在")

    suspect = next((s for s in game.case.suspects if s.id == request.suspect_id), None)
    if not suspect:
        raise HTTPException(404, "嫌疑人不存在")

    watson = WatsonAgent.from_difficulty(game.difficulty.value)
    tips = await watson.offer_interrogation_tips(
        case=game.case,
        suspect=suspect,
        conversation_history=request.conversation_history,
        clues=[c for c in game.case.clues if c.discovered or c.user_generated],
    )
    return {"tips": tips}
```

### 5.4 改造 `make_accusation`
```python
@router.post("/{game_id}/conclusion/accuse")
async def make_accusation(game_id: str, request: MakeAccusationRequest):
    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(404, "game/case 不存在")

    if not request.reasoning_record_ids or len(request.reasoning_record_ids) > 3:
        raise HTTPException(400, "需提供 1-3 条推理记录作为指控依据")

    chain = game_service.get_or_create_deduction_chain(game_id)
    records = [i for i in chain.inferences if i.id in request.reasoning_record_ids]
    if len(records) != len(request.reasoning_record_ids):
        raise HTTPException(400, "存在无效的推理记录 id")
    if any(r.verification_result == "wrong" for r in records):
        raise HTTPException(400, "不可使用已被裁决官标记为错误的推理记录")

    from app.agents.oracle_agent import get_oracle_agent
    oracle_result = await get_oracle_agent().verify_accusation(
        case=game.case, suspect_id=request.suspect_id, reasoning_records=records
    )

    game_service.record_accusation(
        game_id=game_id,
        suspect_id=request.suspect_id,
        is_correct=oracle_result["is_correct"],
        explanation=oracle_result["verdict_explanation"],
        reasoning_record_ids=request.reasoning_record_ids,
    )
    game.phase = GamePhase.CONCLUSION
    game.updated_at = datetime.utcnow()
    return oracle_result
```

`game_service.record_accusation` 需要在 `game_service.py` 实现（已有 `make_accusation`，扩展之）。

### 5.5 改造 `contradiction-check`
- 删除关键词启发式
- 改为：`watson.detect_contradictions(case, conversation_history, suspect_statements)`，返回 `{contradictions, count}`
- 新方法见章节 6

### 5.6 验收标准
- `uvicorn app.main:app --reload` 启动无报错
- 通过 `POST /api/game/new` → `POST /api/game/{id}/deduction/reasoning`（带 1-2 个 clue + 一句话结论）→ 返回 `{verification_result, ...}`
- `POST /accuse` 不带 `reasoning_record_ids` → 400

---

## 章节 6 · WatsonAgent 强化

**目标文件**：
- `backend/app/agents/watson_agent.py`
- `backend/app/agents/prompts/watson_prompts.py`

### 6.1 新增 Prompt（`watson_prompts.py`）

```python
WATSON_SCENE_HINT = """华生（智商合格但不优秀，允许偶尔出错）正在协助勘查。
场景：{scene_name}
玩家最近的搜查动作：{recent_actions}
请用一句话给出下一步勘查建议（中文，维多利亚口吻）。
"""

WATSON_INTERROGATION_TIPS = """华生在审讯室一旁，需要给侦探：
1. 1 条审问话术建议（基于已知线索）
2. 0-2 条可疑点（嫌疑人最近的话与既有线索是否冲突）
注意：你智商一般，可能会指错方向（约 20% 概率给出无关提示）。

## 案件已知线索
{clues_block}

## 嫌疑人
{suspect_name} (id={suspect_id})

## 最近 8 轮对话
{conversation_block}

输出 JSON:
{{
  "tips": [
    {{ "type": "suggestion", "text": "...", "related_clue_ids": [...] }},
    {{ "type": "contradiction", "text": "...", "related_clue_ids": [...] }}
  ]
}}
"""

WATSON_DEDUCTION_HINT = """华生看着推理板，给出一句关联提示。
线索:
{clues_block}
现有推理记录:
{inferences_block}
用一句话指出可能被忽略的关联（中文）。
"""

WATSON_CONTRADICTION = """华生需要分析多名嫌疑人的陈述，找出矛盾。
所有线索:
{clues_block}
嫌疑人陈述:
{statements_block}
输出 JSON:
{{
  "contradictions": [
    {{
      "type": "timeline_conflict|location_conflict|motive_conflict",
      "topic": "...",
      "suspect_1": {{"suspect_id": "...", "suspect_name": "...", "statement": "..."}},
      "suspect_2": {{"suspect_id": "...", "suspect_name": "...", "statement": "..."}},
      "description": "...",
      "confidence": 0.0-1.0
    }}
  ]
}}
"""
```

### 6.2 `watson_agent.py` 新增方法

```python
async def offer_scene_hint(self, scene_name: str, recent_actions: List[str]) -> str:
    # 复用 invoke_with_retry，纯文本返回
    ...

async def offer_interrogation_tips(
    self,
    case: Case,
    suspect: Suspect,
    conversation_history: List[Dict[str, str]],
    clues: List[Clue],
) -> List[Dict[str, Any]]:
    # JSON 模式，返回 tips 数组
    ...

async def offer_deduction_hint(
    self, clues: List[Clue], inferences: List[Inference]
) -> str:
    ...

async def detect_contradictions(
    self,
    case: Case,
    conversation_history: List[Dict[str, str]],
    suspect_statements: Dict[str, List[str]],
) -> List[Dict[str, Any]]:
    # 替代旧关键词启发式
    ...
```

### 6.3 验收标准
- 4 个新方法均可被 `from app.agents.watson_agent import WatsonAgent` 调用
- 单测：用 mock fallback 路径验证返回 schema 正确

---

## 章节 7 · 前端改造

### 7.1 类型与 API 客户端先行

#### 7.1.1 `frontend/src/types/game.ts` 新增
```ts
export interface SceneObject {
  id: string;
  name: string;
  description: string;
  hiddenClueIds: string[];
  searchHints: string[];
}

export interface Scene {
  id: string;
  name: string;
  description: string;
  atmosphereImage?: string;
  npcPersona: string;
  objects: SceneObject[];
}

export interface SceneSearchResponse {
  narrative: string;
  matchedObjectIds: string[];
  clueCandidates: Array<{
    objectId: string;
    suggestedClueId?: string;
    hint: string;
  }>;
}

export interface ReasoningRecord {
  id: string;
  content: string;
  clueIds: string[];
  verificationResult?: 'correct' | 'wrong' | 'partial';
  oracleExplanation?: string;
  confidence: number;
  createdAt: string;
  userMarkedImportant: boolean;
}

export interface WatsonTip {
  type: 'suggestion' | 'contradiction' | 'question_template';
  text: string;
  relatedClueIds: string[];
}
```

#### 7.1.2 `frontend/src/services/api.ts` 新增方法
```ts
export const gameApi = {
  // ... 既有 ...
  sceneSearch: (gameId: string, sceneId: string, query: string, history: any[]) =>
    api.post(`/api/game/${gameId}/scene/${sceneId}/search`, { query, history }),

  addClue: (gameId: string, payload: {
    userLabel: string;
    description: string;
    sourceType: 'scene' | 'interrogation';
    sourceRef?: string;
    baseClueId?: string;
    quotedText?: string;
  }) => api.post(`/api/game/${gameId}/clues`, payload),

  submitReasoning: (gameId: string, clueIds: string[], conclusion: string) =>
    api.post(`/api/game/${gameId}/deduction/reasoning`, { clueIds, conclusion }),

  extractClueFromInterrogation: (gameId: string, payload: {
    suspectId: string;
    quotedText: string;
    contextMessages: any[];
    userLabel: string;
  }) => api.post(`/api/game/${gameId}/interrogation/extract-clue`, payload),

  getInterrogationTips: (gameId: string, suspectId: string, history: any[]) =>
    api.post(`/api/game/${gameId}/interrogation/watson-tips`, {
      suspectId, conversationHistory: history,
    }),

  accuse: (gameId: string, suspectId: string, reasoningRecordIds: string[]) =>
    api.post(`/api/game/${gameId}/conclusion/accuse`, {
      suspectId, reasoningRecordIds,
    }),
};
```

### 7.2 勘查页面重构

**目标**：从 6 热区点图 → 场景列表 + 场景详情两级结构。

#### 7.2.1 路由调整 `frontend/src/App.tsx`
```tsx
<Route path="/investigation/:gameId" element={<InvestigationPage />} />
<Route path="/investigation/:gameId/scene/:sceneId" element={<ScenePage />} />
```

#### 7.2.2 新文件 `frontend/src/pages/ScenePage.tsx`
三列布局：
```tsx
<div className="scene-page">
  <aside className="scene-page__objects">
    {scene.objects.map(obj => (
      <SceneObjectCard key={obj.id} object={obj} onClick={...} />
    ))}
  </aside>
  <main className="scene-page__atmosphere">
    <img src={scene.atmosphereImage || PLACEHOLDER} />
    <h2>{scene.name}</h2>
    <p>{scene.description}</p>
  </main>
  <section className="scene-page__chat">
    <SceneChat
      messages={messages}
      onSend={handleSend}
      clueCandidates={lastCandidates}
      onAddClue={openAddClueModal}
    />
  </section>
</div>
```

#### 7.2.3 新组件 `frontend/src/components/ScenePanel/SceneChat.tsx`
- 调 `gameApi.sceneSearch`
- 当返回 `clueCandidates` 非空时，在消息下方渲染"📎 添加为线索"按钮
- 点击按钮 → 弹出 `AddClueModal`（必填 userLabel，校验非空），提交后调 `gameApi.addClue`

#### 7.2.4 `cluesStore.ts` 调整
```ts
interface Clue {
  id: string;
  userLabel?: string;
  description: string;
  sourceType: 'initial' | 'scene' | 'interrogation';
  sourceRef?: string;
  // ...
}
addClueFromBackend(clue: Clue): void;
```

#### 7.2.5 `InvestigationPage.tsx` 改造
- 替换原热区点图：渲染 `case.scenes` 列表卡片
- 点击卡片 → `navigate('/investigation/{gameId}/scene/{sceneId}')`
- 保留华生对话框
- 在场景列表下方仍展示已添加线索面板

### 7.3 推理板重构 `DeductionBoard.tsx`

按优化方案 DSL 完整重写。骨架：

```tsx
export default function DeductionBoard() {
  const { gameId } = useParams();
  const clues = useCluesStore(s => s.clues);
  const records = useDeductionStore(s => s.reasoningRecords);
  const selectedClueIds = useDeductionStore(s => s.selectedClueIds);
  const filter = useDeductionStore(s => s.filter); // 'all' | 'correct' | 'wrong'
  const [showCombineModal, setShowCombineModal] = useState(false);
  const [showAccuseModal, setShowAccuseModal] = useState(false);

  const filteredRecords = useMemo(() => {
    if (filter === 'all') return records;
    return records.filter(r => r.verificationResult === filter);
  }, [records, filter]);

  const canAccuse = records.some(r => r.verificationResult === 'correct');

  return (
    <div className="deduction-board">
      <aside className="deduction-board__clues">
        <h2>📋 线索列表</h2>
        {clues.map(c => (
          <ClueCheckbox
            key={c.id}
            clue={c}
            checked={selectedClueIds.includes(c.id)}
            onToggle={() => toggleClue(c.id)}
          />
        ))}
        <div className="deduction-board__footer">
          <span>已选 {selectedClueIds.length} 条线索</span>
          <button
            disabled={selectedClueIds.length === 0}
            onClick={() => setShowCombineModal(true)}
          >✨ 组合推理</button>
        </div>
      </aside>

      <main className="deduction-board__records">
        <header>
          <h2>📝 推理记录</h2>
          <FilterTabs value={filter} onChange={setFilter} />
        </header>
        <ul>
          {filteredRecords.map((r, i) => (
            <ReasoningRecordCard
              key={r.id}
              index={records.length - i}
              record={r}
              onMarkImportant={() => markImportant(r.id)}
              onDelete={() => deleteRecord(r.id)}
            />
          ))}
        </ul>
      </main>

      <button
        className="deduction-board__accuse-fab"
        disabled={!canAccuse}
        onClick={() => setShowAccuseModal(true)}
      >🔍 指认凶手</button>

      {showCombineModal && (
        <CombineReasoningModal
          selectedClues={clues.filter(c => selectedClueIds.includes(c.id))}
          onClose={() => setShowCombineModal(false)}
          onSubmit={async (conclusion) => {
            await submitReasoning(selectedClueIds, conclusion);
            setShowCombineModal(false);
          }}
        />
      )}

      {showAccuseModal && (
        <AccusationModal
          suspects={case_.suspects}
          records={records.filter(r => r.verificationResult === 'correct')}
          onSubmit={(suspectId, recordIds) => accuse(suspectId, recordIds)}
        />
      )}
    </div>
  );
}
```

#### 7.3.1 `deductionStore.ts` 改造
```ts
interface DeductionState {
  reasoningRecords: ReasoningRecord[];
  selectedClueIds: string[];
  filter: 'all' | 'correct' | 'wrong';
  toggleClue(id: string): void;
  setFilter(f: 'all'|'correct'|'wrong'): void;
  submitReasoning(gameId: string, clueIds: string[], conclusion: string): Promise<void>;
  markImportant(recordId: string): void;
  deleteRecord(gameId: string, recordId: string): Promise<void>;
  accuse(gameId: string, suspectId: string, recordIds: string[]): Promise<void>;
}
```

每个 action 完成后调用 `console.info('[DeductionStore] action_name', { ... })`。

#### 7.3.2 新组件
- `frontend/src/components/ReasoningRecordCard.tsx`
  - 头部：`#N` + verdict 徽章（✅/❌/⚠️）
  - 关联线索 chip 列表
  - 推理结论文本
  - 时间戳 + 右键菜单（标记重要 / 删除）
- `frontend/src/components/CombineReasoningModal.tsx`
- `frontend/src/components/AccusationModal.tsx`

#### 7.3.3 样式
在 `index.css` 已有维多利亚哥特变量基础上，新增 `.deduction-board__*` 类：暗色背景、金色边框 `#c9a05c`、卡片轻微发光（`box-shadow: 0 0 8px rgba(201,160,92,0.3)`）。

### 7.4 审讯页面增强 `InterrogationPage.tsx`

#### 7.4.1 可选中消息组件 `frontend/src/components/SelectableMessage.tsx`
```tsx
export function SelectableMessage({ text, onExtract }: Props) {
  const [selection, setSelection] = useState<string>('');
  const [tooltipPos, setTooltipPos] = useState<{x:number;y:number}|null>(null);

  const handleMouseUp = () => {
    const sel = window.getSelection();
    const t = sel?.toString().trim() || '';
    if (t.length > 5) {
      const range = sel!.getRangeAt(0).getBoundingClientRect();
      setSelection(t);
      setTooltipPos({ x: range.left, y: range.top - 32 });
    } else {
      setSelection('');
      setTooltipPos(null);
    }
  };

  return (
    <div onMouseUp={handleMouseUp}>
      <p>{text}</p>
      {tooltipPos && (
        <button
          className="extract-clue-tooltip"
          style={{ left: tooltipPos.x, top: tooltipPos.y }}
          onClick={() => onExtract(selection)}
        >📎 生成线索</button>
      )}
    </div>
  );
}
```

#### 7.4.2 在 `InterrogationPage.tsx` 集成
- 嫌疑人消息渲染替换为 `<SelectableMessage>`
- `onExtract` → 弹出 `ExtractClueModal`（必填 userLabel）→ `gameApi.extractClueFromInterrogation`
- 每发送一轮问答后，调用 `gameApi.getInterrogationTips`，把 tips 显示在右侧 `<WatsonTipsPanel>`

#### 7.4.3 `interrogationStore` 新增
```ts
watsonTips: WatsonTip[];
extractedClues: Clue[];
fetchTips(gameId: string, suspectId: string, history: any[]): Promise<void>;
extractClue(gameId: string, payload: ExtractCluePayload): Promise<void>;
```

### 7.5 验收标准
- `npm run typecheck` 全绿
- `npm run lint` 全绿
- `npm run dev` 启动后浏览器手工冒烟（详见章节 8.5）

---

## 章节 8 · 测试与验证

### 8.1 `backend/tests/test_oracle_agent.py`
```python
import pytest
from app.models.case import Case, Suspect, Clue, Inference
from app.agents.oracle_agent import OracleAgent

@pytest.fixture
def fixture_case():
    return Case(
        id="c1", victim_name="Sir Henry", victim_background="...",
        cause_of_death="poison", time_of_death="昨夜 11 点",
        location="书房", date=__import__('datetime').datetime.utcnow(),
        suspects=[
            Suspect(id="s1", name="管家", age=50, background="", motive="债务", timeline="", is_guilty=True),
            Suspect(id="s2", name="侄子", age=30, background="", motive="遗产", timeline="", is_guilty=False),
        ],
        clues=[
            Clue(id="c1", description="书房有未喝完的红酒", clue_type="physical"),
            Clue(id="c2", description="管家昨晚出现在酒窖", clue_type="testimonial"),
        ],
        true_murderer_id="s1",
    )

@pytest.mark.asyncio
async def test_verify_inference_returns_schema(fixture_case):
    oracle = OracleAgent()
    result = await oracle.verify_inference(
        case=fixture_case, clues=fixture_case.clues, conclusion="管家在红酒中下毒"
    )
    assert "verdict" in result
    assert result["verdict"] in ("correct", "wrong", "partial")

@pytest.mark.asyncio
async def test_verify_accusation_fallback_correct(fixture_case, monkeypatch):
    # 模拟 LLM 不可用 → fallback 路径
    monkeypatch.setattr("app.agents._llm_helpers.invoke_with_retry",
                        lambda **kw: kw["fallback"])
    oracle = OracleAgent()
    result = await oracle.verify_accusation(
        case=fixture_case, suspect_id="s1", reasoning_records=[]
    )
    assert result["is_correct"] is True
```

### 8.2 `backend/tests/test_scene_search.py`
- 用 fixture case + 预设 scene
- mock `invoke_with_retry` 返回 `{"narrative": "...", "matched_object_ids": ["obj1"], "clue_candidates": []}`
- 断言 `SceneAgent.search` 解析正确

### 8.3 `backend/tests/test_accuse_validation.py`
```python
@pytest.mark.asyncio
async def test_accuse_requires_reasoning_records(client, game_id):
    r = await client.post(f"/api/game/{game_id}/conclusion/accuse",
                          json={"suspect_id": "s1", "reasoning_record_ids": []})
    assert r.status_code == 400

async def test_accuse_rejects_wrong_records(client, game_id, wrong_record_id):
    r = await client.post(f"/api/game/{game_id}/conclusion/accuse",
                          json={"suspect_id": "s1", "reasoning_record_ids": [wrong_record_id]})
    assert r.status_code == 400
```

### 8.4 扩展 `test_difficulty.py`
- 用例：不同 difficulty 调用 case_generator → 断言 `len(case.scenes) >= 3`、每个 scene `len(objects) in [3, 6]`

### 8.5 端到端冒烟（手工，用浏览器）
| 步骤 | 操作 | 期望 |
|---|---|---|
| 1 | `cd backend && uvicorn app.main:app --reload` | 后端启动无报错 |
| 2 | `cd frontend && npm run dev` | 前端启动 |
| 3 | 打开 `/`，选难度，开局 | 跳到 `/investigation/{gameId}` |
| 4 | 看到场景列表（≥3 个） | ✅ |
| 5 | 点击某场景 | 跳到 `/scene/{sceneId}`，三列布局 |
| 6 | 在右侧聊天输入"查看办公桌" | 收到场景 NPC 回复，若有线索候选则显示"添加线索"按钮 |
| 7 | 点击"添加线索" → 输入名称"债务信件" → 提交 | 左侧线索面板出现该条 |
| 8 | 进入 `/interrogation/{gameId}` 选嫌疑人审讯 | 提问后右侧出现华生 tips |
| 9 | 选中嫌疑人某句话 → "📎 生成线索" → 命名 → 提交 | 线索列表新增 |
| 10 | 进入 `/deduction/{gameId}` | 看到线索面板 + 推理记录面板 |
| 11 | 勾选 ≥1 条线索 → "✨ 组合推理" → 输入结论 → 提交 | 右侧推理记录面板新增一条带 verdict 徽章 |
| 12 | 至少有一条 ✅ correct 后，右下角"🔍 指认凶手"可点 | ✅ |
| 13 | 点击 → 选择嫌疑人 + 1-3 条推理记录 → 提交 | 跳到结案页面，显示 Oracle 判定 |

### 8.6 验收标准
- 后端：`pytest` 全绿
- 前端：`npm run typecheck && npm run lint` 全绿
- 端到端 13 步冒烟全部通过

---

## 章节 9 · 风险与回滚

| 风险 | 影响 | 预案 |
|---|---|---|
| Case schema 改动破坏旧存档 | 无法 load 旧 game | 全部新字段可选+默认值；`game.case` 反序列化时若缺失 scenes 则 `case.scenes = []` |
| Oracle Agent LLM 不稳定 | 推理无法验证 | `fallback` 路径返回 partial + "请稍后重试"，不阻塞流程 |
| SceneAgent 剧透真相 | 玩家失去乐趣 | Prompt 严格约束"不可剧透"+ 单测验证 narrative 不含 true_murderer 名字 |
| 前端三页面同时大改 | PR 体积过大 | 拆为三个 PR：1) 数据模型+新 Agent+API；2) 勘查页；3) 推理板+审讯页 |
| 矛盾检测从启发式切到 LLM | 准确率短期波动 | 保留旧端点行为开关 `WATSON_USE_LLM_CONTRADICTION=true`，灰度切换 |

---

## 章节 10 · 文件清单（交付 Checklist）

### 新增
- [ ] `backend/app/agents/oracle_agent.py`
- [ ] `backend/app/agents/scene_agent.py`
- [ ] `backend/app/agents/prompts/oracle_prompts.py`
- [ ] `backend/app/agents/prompts/scene_prompts.py`
- [ ] `backend/tests/test_oracle_agent.py`
- [ ] `backend/tests/test_scene_search.py`
- [ ] `backend/tests/test_accuse_validation.py`
- [ ] `frontend/src/pages/ScenePage.tsx`
- [ ] `frontend/src/components/ScenePanel/SceneChat.tsx`
- [ ] `frontend/src/components/ScenePanel/SceneObjectCard.tsx`
- [ ] `frontend/src/components/ScenePanel/AddClueModal.tsx`
- [ ] `frontend/src/components/SelectableMessage.tsx`
- [ ] `frontend/src/components/ExtractClueModal.tsx`
- [ ] `frontend/src/components/WatsonTipsPanel.tsx`
- [ ] `frontend/src/components/ReasoningRecordCard.tsx`
- [ ] `frontend/src/components/CombineReasoningModal.tsx`
- [ ] `frontend/src/components/AccusationModal.tsx`

### 修改
- [ ] `backend/app/models/case.py`（+Scene/SceneObject + Clue/Inference 扩展）
- [ ] `backend/app/routers/game.py`（5 个新端点 + accuse/contradiction 改造）
- [ ] `backend/app/services/game_service.py`（add_user_clue / update_inference / record_accusation）
- [ ] `backend/app/agents/case_generator_agent.py`（+ scenes 生成 + mock 降级更新）
- [ ] `backend/app/agents/watson_agent.py`（+offer_scene_hint / offer_interrogation_tips / offer_deduction_hint / detect_contradictions）
- [ ] `backend/app/agents/prompts/case_prompts.py`（schema 追加 scenes）
- [ ] `backend/app/agents/prompts/watson_prompts.py`（+4 个 prompt）
- [ ] `backend/tests/test_difficulty.py`（验证 scenes 生成）
- [ ] `frontend/src/App.tsx`（+ScenePage 路由）
- [ ] `frontend/src/pages/InvestigationPage.tsx`（场景列表式重构）
- [ ] `frontend/src/pages/DeductionBoard.tsx`（按 DSL 完全重写）
- [ ] `frontend/src/pages/InterrogationPage.tsx`（可选中消息 + tips）
- [ ] `frontend/src/store/cluesStore.ts`
- [ ] `frontend/src/store/deductionStore.ts`
- [ ] `frontend/src/store/interrogationStore.ts`（若不存在则新增）
- [ ] `frontend/src/services/api.ts`
- [ ] `frontend/src/types/game.ts`
- [ ] `frontend/src/index.css`（新推理板暗色主题局部样式）

### 完成标志
- [ ] 章节 1-7 全部代码合入
- [ ] 章节 8 测试全绿（后端 pytest + 前端 typecheck/lint + 13 步手工冒烟）
- [ ] `progress/` 目录追加本次实施记录
- [ ] `project_overview.md` 更新进度到当日

---

## 附：执行 Agent 行动指引

1. **先读全文**，理解 10 个章节的依赖关系
2. **严格按顺序执行**：1 → 2 → 3 → 4 → 5 → 6 → 7（7.1 → 7.2 → 7.3 → 7.4）→ 8 → 9 → 10
3. **每章完成后**：跑该章对应的测试 / 冒烟，绿了再下一章
4. **遇到不一致**：以本文档为准；如本文档与现有代码 API 签名冲突（如 `_llm_helpers.invoke_with_retry` 参数名），先 `cat` 现有源码确认实际签名再适配
5. **日志/注释规范**：严格遵循 `CLAUDE.md` 的全局/项目约束
6. **禁止跨阶段并行**：例如不要在章节 1 数据模型未合入时就动章节 7 前端
