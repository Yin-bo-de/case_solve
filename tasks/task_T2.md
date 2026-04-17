 实现计划：T2.1 → T2.2/T2.3/T2.4（并行）→ T2.5

 Context

 项目是 AI 驱动的福尔摩斯式探案游戏（FastAPI + LangChain + React）。
 三个 LangChain Agent（CaseGeneratorAgent / SuspectAgent / WatsonAgent）均已有 self.llm = ChatOpenAI(...) 实例，但所有方法都直接调用
 _generate_mock_* 函数，未真正接入 LLM。
 本计划目标：将 Mock 实现替换为真实 LLM 调用，同时保留 API key 缺失时的 mock 降级路径。

 ---
 关键文件

 ┌───────────────────────────────────────────────┬──────────┬─────────────────────────────────┐
 │                     文件                      │   状态   │              说明               │
 ├───────────────────────────────────────────────┼──────────┼─────────────────────────────────┤
 │ backend/app/agents/case_generator_agent.py    │ 修改     │ 接入 LLM 生成案件               │
 ├───────────────────────────────────────────────┼──────────┼─────────────────────────────────┤
 │ backend/app/agents/suspect_agent.py           │ 修改     │ 接入 LLM 生成对话/谎言检测/插话 │
 ├───────────────────────────────────────────────┼──────────┼─────────────────────────────────┤
 │ backend/app/agents/watson_agent.py            │ 修改     │ 接入 LLM 生成华生回复           │
 ├───────────────────────────────────────────────┼──────────┼─────────────────────────────────┤
 │ backend/app/agents/prompts/                   │ 新建目录 │ Prompt 模板集中管理             │
 ├───────────────────────────────────────────────┼──────────┼─────────────────────────────────┤
 │ backend/app/agents/prompts/__init__.py        │ 新建     │ 空文件                          │
 ├───────────────────────────────────────────────┼──────────┼─────────────────────────────────┤
 │ backend/app/agents/prompts/case_prompts.py    │ 新建     │ 案件生成 Prompt                 │
 ├───────────────────────────────────────────────┼──────────┼─────────────────────────────────┤
 │ backend/app/agents/prompts/suspect_prompts.py │ 新建     │ 嫌疑人 Prompt                   │
 ├───────────────────────────────────────────────┼──────────┼─────────────────────────────────┤
 │ backend/app/agents/prompts/watson_prompts.py  │ 新建     │ 华生 Prompt                     │
 ├───────────────────────────────────────────────┼──────────┼─────────────────────────────────┤
 │ backend/app/agents/_llm_helpers.py            │ 新建     │ 通用 LLM 调用封装               │
 └───────────────────────────────────────────────┴──────────┴─────────────────────────────────┘

 ---
 T2.1：Prompt 工程化管理

 目录结构

 backend/app/agents/prompts/
 ├── __init__.py
 ├── case_prompts.py
 ├── suspect_prompts.py
 └── watson_prompts.py

 case_prompts.py

 from langchain_core.prompts import ChatPromptTemplate

 CASE_GENERATION_SYSTEM = """\
 You are a Victorian era murder mystery writer creating a fully playable detective game case.
 Set in 1890s London. All output must be in Chinese.

 Difficulty rules:
 - easy: clues are obvious (obviousness 0.7-1.0), 1 red herring, evidence points clearly to killer
 - classic: clues moderate (0.4-0.8), 2 red herrings, some ambiguity
 - hardcore: clues subtle (0.1-0.4), 3 red herrings, highly misleading evidence

 Return ONLY valid JSON with this exact structure (no markdown, no explanation):
 {{
   "victim_name": "string",
   "victim_background": "string",
   "cause_of_death": "string",
   "time_of_death": "string",
   "location": "string",
   "summary": "string",
   "murder_method": "string",
   "investigation_locations": ["string"],
   "true_murderer_index": 0,
   "suspects": [
     {{
       "name": "string",
       "age": 30,
       "background": "string",
       "motive": "string",
       "timeline": "string",
       "is_guilty": false,
       "personality_traits": ["string"],
       "secrets": ["string"]
     }}
   ],
   "clues": [
     {{
       "description": "string",
       "clue_type": "physical",
       "location": "string",
       "related_suspect_indices": [0],
       "is_red_herring": false
     }}
   ]
 }}
 Include exactly 3 suspects and 5 clues. true_murderer_index must be 0, 1, or 2.
 """

 CASE_GENERATION_HUMAN = "Generate a murder mystery case. Difficulty: {difficulty}"

 case_generation_prompt = ChatPromptTemplate.from_messages([
     ("system", CASE_GENERATION_SYSTEM),
     ("human", CASE_GENERATION_HUMAN),
 ])

 suspect_prompts.py

 from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

 SUSPECT_RESPONSE_SYSTEM = """\
 你正在扮演{suspect_name}，维多利亚时代伦敦一起谋杀案的嫌疑人。

 你的人物设定：
 - 背景：{background}
 - 动机（隐秘）：{motive}
 - 时间线：{timeline}
 - 性格特征：{personality_traits}
 - 秘密：{secrets}
 - 是否有罪：{is_guilty}

 案件背景：
 - 受害者：{victim_name}，{victim_background}
 - 案件概要：{case_summary}

 审讯模式：{"私下单独审讯" if "{is_private}" == "True" else "全体质询，其他嫌疑人在场"}

 回复规则：
 1. 使用维多利亚时代的措辞风格，礼貌而正式
 2. 若有罪：转移话题、撒谎或只承认无关紧要的部分
 3. 若无辜：可能紧张但最终诚实
 4. 回复用中文，100字以内，保持角色一致性
 """

 SUSPECT_RESPONSE_HUMAN = "{user_question}"

 suspect_response_prompt = ChatPromptTemplate.from_messages([
     ("system", SUSPECT_RESPONSE_SYSTEM),
     MessagesPlaceholder(variable_name="history", optional=True),
     ("human", SUSPECT_RESPONSE_HUMAN),
 ])

 SUSPECT_LIE_DETECTION_SYSTEM = """\
 你是福尔摩斯，正在分析嫌疑人证词。
 基于案件事实判断嫌疑人是否在说谎。

 案件事实：
 - 真凶：{true_murderer_name}（是否是本人：{is_guilty}）
 - 作案手法：{murder_method}

 嫌疑人：{suspect_name}

 只返回 JSON，不要任何解释：
 {{"lie_detected": true/false, "confidence": 0.0-1.0, "microexpression": "描述或null", "notes": "分析备注"}}
 """

 SUSPECT_LIE_DETECTION_HUMAN = "分析以下证词是否有谎言：\n{response}"

 suspect_lie_detection_prompt = ChatPromptTemplate.from_messages([
     ("system", SUSPECT_LIE_DETECTION_SYSTEM),
     ("human", SUSPECT_LIE_DETECTION_HUMAN),
 ])

 SUSPECT_INTERJECTION_SYSTEM = """\
 你正在扮演{other_suspect_name}，正在全体质询场景中。
 刚才{responding_suspect_name}发表了一段证词。

 你的人物：{other_background}
 你和{responding_suspect_name}的关系：有可能相互了解对方的行踪。

 决定是否插话反驳。30%概率插话。
 若插话，返回一句维多利亚风格的中文反驳（50字以内）。
 若不插话，只返回：null
 """

 SUSPECT_INTERJECTION_HUMAN = "刚才的证词：\n{context}"

 suspect_interjection_prompt = ChatPromptTemplate.from_messages([
     ("system", SUSPECT_INTERJECTION_SYSTEM),
     ("human", SUSPECT_INTERJECTION_HUMAN),
 ])

 watson_prompts.py

 from langchain_core.prompts import ChatPromptTemplate

 WATSON_BASE_SYSTEM = """\
 你是华生医生（Dr. John H. Watson），福尔摩斯的忠实伙伴。
 正在协助调查1890年代伦敦的一起谋杀案。

 案件背景：
 - 受害者：{victim_name}
 - 案发地点：{case_location}
 - 案件概要：{case_summary}

 你的性格：热情、支持、偶尔推理偏差但忠诚可靠。
 用维多利亚时代语气，回复用中文，简短（1-3句话）。
 """

 WATSON_OBSERVATION_HUMAN = """\
 刚刚在"{observation_location}"发现了新情况：
 "{observation_description}"

 请作为华生评论这个发现。
 """

 watson_observation_prompt = ChatPromptTemplate.from_messages([
     ("system", WATSON_BASE_SYSTEM),
     ("human", WATSON_OBSERVATION_HUMAN),
 ])

 WATSON_QUESTION_REASONING_HUMAN = """\
 侦探刚刚做出了以下推理：
 "{inference_content}"

 请作为华生对这个推理提出一个疑问或补充看法（可以稍微偏差一点）。
 """

 watson_question_reasoning_prompt = ChatPromptTemplate.from_messages([
     ("system", WATSON_BASE_SYSTEM),
     ("human", WATSON_QUESTION_REASONING_HUMAN),
 ])

 WATSON_KNOWLEDGE_HUMAN = """\
 侦探询问关于"{topic}"的专业知识。
 请以军医身份提供相关的医学或专业知识，结合案件背景。
 """

 watson_knowledge_prompt = ChatPromptTemplate.from_messages([
     ("system", WATSON_BASE_SYSTEM),
     ("human", WATSON_KNOWLEDGE_HUMAN),
 ])

 WATSON_SUGGEST_HYPOTHESIS_HUMAN = """\
 目前已经收集了以下观察记录：
 {observations_summary}

 请作为华生提出一个（可能不完全正确的）假设，带动侦探思考。
 """

 watson_suggest_hypothesis_prompt = ChatPromptTemplate.from_messages([
     ("system", WATSON_BASE_SYSTEM),
     ("human", WATSON_SUGGEST_HYPOTHESIS_HUMAN),
 ])

 WATSON_CHAT_SYSTEM = """\
 你是华生医生（Dr. John H. Watson），福尔摩斯的忠实伙伴。
 正在协助调查1890年代伦敦的一起谋杀案。

 当前游戏状态：
 - 游戏阶段：{game_phase}
 - 已收集观察：{observations_count}条
 - 已找到线索：{clues_collected}个
 - 已审讯嫌疑人：{suspects_interviewed}
 - 推理数量：{inferences_count}
 - 假设数量：{hypotheses_count}

 案件概要：{case_summary}

 用维多利亚时代中文回复，根据消息类型给出恰当响应（指导/分析/知识/鼓励等）。回复简短。
 """

 WATSON_CHAT_HUMAN = "{user_message}"

 watson_chat_prompt = ChatPromptTemplate.from_messages([
     ("system", WATSON_CHAT_SYSTEM),
     ("human", WATSON_CHAT_HUMAN),
 ])

 ---
 T2.5：通用 LLM 封装（先设计，T2.2/T2.3/T2.4 实现时直接用）

 _llm_helpers.py

 """
 LLM 调用通用封装：统一重试 / 超时 / 日志 / 降级
 """
 import asyncio
 import json
 import time
 from typing import Any, Callable, Optional
 from loguru import logger


 async def invoke_with_retry(
     chain,
     inputs: dict,
     fallback_fn: Optional[Callable] = None,
     max_retries: int = 2,
     timeout: float = 30.0,
     parse_json: bool = False,
 ) -> Any:
     """
     带重试/超时/日志/降级的 LLM 链调用。

     Args:
         chain: LangChain Runnable（prompt | llm | parser）
         inputs: 链输入字典
         fallback_fn: API 失败时的降级函数（无参数，返回默认值）
         max_retries: 最大重试次数
         timeout: 单次调用超时（秒）
         parse_json: 是否将输出字符串解析为 JSON

     Returns:
         LLM 输出或 fallback_fn() 的返回值
     """
     last_error = None
     for attempt in range(max_retries + 1):
         t0 = time.perf_counter()
         try:
             result = await asyncio.wait_for(chain.ainvoke(inputs), timeout=timeout)
             elapsed = time.perf_counter() - t0
             logger.info(f"[LLMHelper] 调用成功 (attempt={attempt+1}, elapsed={elapsed:.2f}s)")

             if parse_json and isinstance(result, str):
                 # 去除 markdown 代码块
                 cleaned = result.strip()
                 if cleaned.startswith("```"):
                     cleaned = cleaned.split("```")[1]
                     if cleaned.startswith("json"):
                         cleaned = cleaned[4:]
                 return json.loads(cleaned.strip())
             return result

         except asyncio.TimeoutError:
             elapsed = time.perf_counter() - t0
             logger.warning(f"[LLMHelper] 超时 (attempt={attempt+1}, elapsed={elapsed:.2f}s)")
             last_error = TimeoutError(f"LLM call timed out after {timeout}s")
         except Exception as e:
             elapsed = time.perf_counter() - t0
             logger.warning(f"[LLMHelper] 调用失败 (attempt={attempt+1}, elapsed={elapsed:.2f}s): {e}")
             last_error = e

         if attempt < max_retries:
             await asyncio.sleep(1.0 * (attempt + 1))

     if fallback_fn is not None:
         logger.warning(f"[LLMHelper] 所有重试失败，使用降级方案: {last_error}")
         return fallback_fn()

     raise last_error

 ---
 T2.2：case_generator_agent 接入真实 LLM

 关键改动

 generate_case 方法中：

 async def generate_case(self, difficulty: str = "classic") -> Case:
     settings = get_settings()

     # API key 缺失时直接降级，不做 LLM 调用
     if not settings.openai_api_key:
         logger.warning("[CaseGeneratorAgent] openai_api_key 未配置，使用 mock 降级")
         case_id = str(uuid.uuid4())
         return self._generate_mock_case(case_id, difficulty)

     case_id = str(uuid.uuid4())
     chain = case_generation_prompt | self.llm

     raw_data = await invoke_with_retry(
         chain=chain,
         inputs={"difficulty": difficulty},
         fallback_fn=lambda: None,  # None 时走下面的降级逻辑
         max_retries=2,
         timeout=45.0,
         parse_json=True,
     )

     if raw_data is None:
         logger.warning("[CaseGeneratorAgent] LLM 返回空，使用 mock 降级")
         return self._generate_mock_case(case_id, difficulty)

     return self._build_case_from_llm_output(case_id, difficulty, raw_data)

 _build_case_from_llm_output 方法（后处理）

 def _build_case_from_llm_output(self, case_id: str, difficulty: str, data: dict) -> Case:
     """将 LLM 返回的 JSON 转换为 Case 对象，补充 ID/时间戳/obviousness 等"""
     difficulty_config = {
         "easy":     {"red_herring_count": 1, "real_range": (0.7, 1.0), "decoy_range": (0.3, 0.5)},
         "classic":  {"red_herring_count": 2, "real_range": (0.4, 0.8), "decoy_range": (0.2, 0.4)},
         "hardcore": {"red_herring_count": 3, "real_range": (0.1, 0.4), "decoy_range": (0.1, 0.3)},
     }
     config = difficulty_config.get(difficulty, difficulty_config["classic"])
     real_lo, real_hi = config["real_range"]
     decoy_lo, decoy_hi = config["decoy_range"]

     # 构建嫌疑人（补充 ID）
     suspects = []
     for i, s in enumerate(data["suspects"]):
         suspects.append(Suspect(
             id=f"suspect-{i+1}",
             **{k: v for k, v in s.items()},
         ))

     true_murderer_id = suspects[data["true_murderer_index"]].id

     # 构建线索（补充 ID / obviousness）
     clues = []
     for i, c in enumerate(data["clues"]):
         is_rh = c.get("is_red_herring", False)
         lo, hi = (decoy_lo, decoy_hi) if is_rh else (real_lo, real_hi)
         # related_suspect_indices → related_suspect_ids
         related_ids = [suspects[idx].id for idx in c.get("related_suspect_indices", []) if idx < len(suspects)]
         clues.append(Clue(
             id=f"clue-{i+1}",
             description=c["description"],
             clue_type=c.get("clue_type", "physical"),
             location=c.get("location"),
             related_suspect_ids=related_ids,
             is_red_herring=is_rh,
             obviousness=round(random.uniform(lo, hi), 2),
         ))

     return Case(
         id=case_id,
         victim_name=data["victim_name"],
         victim_background=data["victim_background"],
         cause_of_death=data["cause_of_death"],
         time_of_death=data["time_of_death"],
         location=data["location"],
         date=datetime.utcnow(),
         suspects=suspects,
         clues=clues,
         summary=data["summary"],
         murder_method=data["murder_method"],
         true_murderer_id=true_murderer_id,
         investigation_locations=data.get("investigation_locations", []),
     )

 ---
 T2.3：suspect_agent 接入真实 LLM

 generate_response

 async def generate_response(self, suspect, case, user_question, conversation_history=None, is_private=True, other_suspects_present=None):
     settings = get_settings()
     if not settings.openai_api_key:
         return self._generate_mock_response(suspect, case, user_question, is_private)

     # 构建对话历史为 LangChain messages
     history = []
     for msg in (conversation_history or []):
         if msg.get("role") == "user":
             history.append(HumanMessage(content=msg["content"]))
         else:
             history.append(AIMessage(content=msg["content"]))

     chain = suspect_response_prompt | self.llm
     result = await invoke_with_retry(
         chain=chain,
         inputs={
             "suspect_name": suspect.name,
             "background": suspect.background,
             "motive": suspect.motive,
             "timeline": suspect.timeline,
             "personality_traits": "、".join(suspect.personality_traits),
             "secrets": "；".join(suspect.secrets),
             "is_guilty": str(suspect.is_guilty),
             "victim_name": case.victim_name,
             "victim_background": case.victim_background,
             "case_summary": case.summary,
             "is_private": str(is_private),
             "user_question": user_question,
             "history": history,
         },
         fallback_fn=lambda: self._generate_mock_response(suspect, case, user_question, is_private),
     )
     return result.content if hasattr(result, "content") else str(result)

 detect_lie

 async def detect_lie(self, suspect, response, case):
     settings = get_settings()
     if not settings.openai_api_key:
         return self._generate_mock_lie_detection(suspect, response)

     true_murderer = next((s for s in case.suspects if s.id == case.true_murderer_id), None)
     chain = suspect_lie_detection_prompt | self.llm

     result = await invoke_with_retry(
         chain=chain,
         inputs={
             "true_murderer_name": true_murderer.name if true_murderer else "未知",
             "is_guilty": str(suspect.is_guilty),
             "murder_method": case.murder_method,
             "suspect_name": suspect.name,
             "response": response,
         },
         fallback_fn=lambda: self._generate_mock_lie_detection(suspect, response),
         parse_json=True,
     )
     # result 可能是 dict（parse_json=True）或 mock dict
     if isinstance(result, dict):
         return result
     return self._generate_mock_lie_detection(suspect, response)

 generate_interjection

 async def generate_interjection(self, responding_suspect, other_suspect, case, context):
     settings = get_settings()
     if not settings.openai_api_key:
         return self._generate_mock_interjection(responding_suspect, other_suspect, case)

     chain = suspect_interjection_prompt | self.llm
     result = await invoke_with_retry(
         chain=chain,
         inputs={
             "other_suspect_name": other_suspect.name,
             "responding_suspect_name": responding_suspect.name,
             "other_background": other_suspect.background,
             "context": context,
         },
         fallback_fn=lambda: self._generate_mock_interjection(responding_suspect, other_suspect, case),
     )
     content = result.content if hasattr(result, "content") else str(result)
     return None if content.strip().lower() == "null" else content

 ---
 T2.4：watson_agent 接入真实 LLM

 公共 context 提取工具函数（内部方法）

 def _get_case_context(self, case=None) -> dict:
     """从 case 对象提取 prompt 所需字段，case 为 None 时返回占位符"""
     if case:
         return {
             "victim_name": case.victim_name,
             "case_location": case.location,
             "case_summary": case.summary,
         }
     return {"victim_name": "受害者", "case_location": "案发现场", "case_summary": "维多利亚时代谋杀案"}

 注意：现有的 share_observation、question_reasoning 等方法签名只接收 observation/inference，不含 case 参数。
 解决方案：在这些方法中使用占位符 case context（_get_case_context(None)），或在路由层调用时额外传 case（需评估改动范围）。
 决策：暂不修改路由层签名，使用通用 case context 占位符，LLM 仍能基于 observation/inference 内容生成有意义回复。

 share_observation

 async def share_observation(self, observation):
     if random.random() > self.proactive_rate:
         return None

     settings = get_settings()
     if not settings.openai_api_key:
         return self._generate_mock_observation_comment(observation)

     chain = watson_observation_prompt | self.llm
     result = await invoke_with_retry(
         chain=chain,
         inputs={
             **self._get_case_context(),
             "observation_location": observation.location,
             "observation_description": observation.description,
         },
         fallback_fn=lambda: self._generate_mock_observation_comment(observation),
     )
     return result.content if hasattr(result, "content") else str(result)

 question_reasoning

 async def question_reasoning(self, inference):
     if random.random() > self.proactive_rate:
         return None

     settings = get_settings()
     if not settings.openai_api_key:
         return self._generate_mock_reasoning_question(inference)

     chain = watson_question_reasoning_prompt | self.llm
     result = await invoke_with_retry(
         chain=chain,
         inputs={
             **self._get_case_context(),
             "inference_content": inference.content,
         },
         fallback_fn=lambda: self._generate_mock_reasoning_question(inference),
     )
     return result.content if hasattr(result, "content") else str(result)

 provide_knowledge

 async def provide_knowledge(self, topic):
     settings = get_settings()
     if not settings.openai_api_key:
         return self._generate_mock_knowledge(topic)

     chain = watson_knowledge_prompt | self.llm
     result = await invoke_with_retry(
         chain=chain,
         inputs={**self._get_case_context(), "topic": topic},
         fallback_fn=lambda: self._generate_mock_knowledge(topic),
     )
     return result.content if hasattr(result, "content") else str(result)

 suggest_hypothesis

 async def suggest_hypothesis(self, observations):
     settings = get_settings()
     if not settings.openai_api_key:
         return None

     if not observations:
         return None

     obs_summary = "\n".join(f"- {o.description}（{o.location}）" for o in observations[:5])
     chain = watson_suggest_hypothesis_prompt | self.llm
     result = await invoke_with_retry(
         chain=chain,
         inputs={**self._get_case_context(), "observations_summary": obs_summary},
         fallback_fn=lambda: None,
     )
     return result.content if hasattr(result, "content") else str(result)

 _generate_response（chat 入口）

 async def _generate_response(self, message, message_type, context):
     settings = get_settings()
     if not settings.openai_api_key:
         # 走原有 mock 分支
         return await self._mock_generate_response(message, message_type, context)

     # 统一走 watson_chat_prompt + LLM
     chain = watson_chat_prompt | self.llm
     suspects_str = "、".join(context.suspects_interviewed) if context.suspects_interviewed else "无"
     result = await invoke_with_retry(
         chain=chain,
         inputs={
             "game_phase": context.game_phase.value if hasattr(context.game_phase, "value") else context.game_phase,
             "observations_count": context.observations_count,
             "clues_collected": context.clues_collected,
             "suspects_interviewed": suspects_str,
             "inferences_count": context.inferences_count,
             "hypotheses_count": context.hypotheses_count,
             "case_summary": "正在进行中的谋杀案调查",
             "user_message": message,
         },
         fallback_fn=lambda: self._generate_general_response(context),
     )
     return result.content if hasattr(result, "content") else str(result)

 注意：将原 _generate_response 中的 mock 分支重命名为 _mock_generate_response，保持原有 mock 路由。

 ---
 导入变更

 case_generator_agent.py 新增导入

 from app.agents.prompts.case_prompts import case_generation_prompt
 from app.agents._llm_helpers import invoke_with_retry

 suspect_agent.py 新增导入

 from langchain_core.messages import HumanMessage, AIMessage
 from app.agents.prompts.suspect_prompts import (
     suspect_response_prompt,
     suspect_lie_detection_prompt,
     suspect_interjection_prompt,
 )
 from app.agents._llm_helpers import invoke_with_retry

 watson_agent.py 新增导入

 from app.agents.prompts.watson_prompts import (
     watson_observation_prompt,
     watson_question_reasoning_prompt,
     watson_knowledge_prompt,
     watson_suggest_hypothesis_prompt,
     watson_chat_prompt,
 )
 from app.agents._llm_helpers import invoke_with_retry

 ---
 降级策略

 ┌─────────────────────┬───────────────────────────────────────┐
 │        情况         │                 行为                  │
 ├─────────────────────┼───────────────────────────────────────┤
 │ openai_api_key 为空 │ 立即降级 mock，记录 WARNING           │
 ├─────────────────────┼───────────────────────────────────────┤
 │ LLM 调用超时 (>30s) │ 重试最多 2 次，全部超时则降级 mock    │
 ├─────────────────────┼───────────────────────────────────────┤
 │ LLM 返回无效 JSON   │ invoke_with_retry 捕获异常，降级 mock │
 ├─────────────────────┼───────────────────────────────────────┤
 │ LLM 返回空内容      │ 调用方检查 None 并降级                │
 └─────────────────────┴───────────────────────────────────────┘

 ---
 验证步骤

 1. 有 API Key 时的验证（真实 LLM）

 cd backend
 # 确认 .env 中有 OPENAI_API_KEY
 curl -X POST http://localhost:8000/api/game/new \
   -H "Content-Type: application/json" \
   -d '{"difficulty": "classic"}'
 # 期望：返回包含真实故事情节的案件 JSON，嫌疑人/线索内容不重复

 2. 无 API Key 时的降级验证

 # 临时移除 API Key
 OPENAI_API_KEY="" uvicorn app.main:app --reload
 curl -X POST http://localhost:8000/api/game/new -H "Content-Type: application/json" -d '{"difficulty": "easy"}'
 # 期望：正常返回 mock 案件，后端日志出现 WARNING "openai_api_key 未配置"

 3. 嫌疑人对话验证

 # 先创建游戏获取 game_id
 curl -X POST http://localhost:8000/api/game/{game_id}/interrogation/question \
   -H "Content-Type: application/json" \
   -d '{"suspect_id": "suspect-1", "question": "昨晚你在哪里？", "is_private": true}'
 # 期望：返回符合嫌疑人性格的维多利亚风格中文回复，不是固定模板

 4. 华生对话验证

 curl -X POST http://localhost:8000/api/game/{game_id}/watson/chat \
   -H "Content-Type: application/json" \
   -d '{"message": "我该怎么办？"}'
 # 期望：返回有案件针对性的华生建议，不是重复的固定文案

 5. 日志检查

 后端日志应包含：
 [LLMHelper] 调用成功 (attempt=1, elapsed=X.XXs)
 [CaseGeneratorAgent] 案件生成完成: <uuid>

 ---
 执行顺序

 T2.1: 新建 prompts/ 目录和三个 prompt 文件
    ↓
 T2.5: 新建 _llm_helpers.py（供 T2.2/T2.3/T2.4 直接复用）
    ↓
 T2.2 + T2.3 + T2.4（可并行修改三个 Agent 文件）

 注：T2.5 提前到 T2.1 之后创建，避免三个 Agent 各自写重复的 try/retry 逻辑。