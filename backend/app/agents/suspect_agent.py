"""
嫌疑人 Agent - 符合维多利亚时代特征的对话
"""
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime
import random

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from app.config import get_settings
from app.models.case import Suspect, Case
from app.agents.prompts.suspect_prompts import (
    suspect_response_prompt,
    suspect_lie_detection_prompt,
    suspect_interjection_prompt,
    suspect_confront_clue_prompt,
)
from app.agents._llm_helpers import invoke_with_retry, truncate_messages_by_token, estimate_token_count


class SuspectAgent:
    """嫌疑人 Agent 类"""

    def __init__(self):
        """初始化嫌疑人 Agent"""
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.8,
            extra_body={"enable_thinking": False},
        )
        logger.info("[SuspectAgent] 初始化嫌疑人 Agent")

    # P3: 状态指令映射表
    _STATE_DIRECTIVES = {
        "calm": "你目前表现冷静、礼貌、克制，滴水不漏。回答要镇定自信，不轻易暴露情绪。",
        "pressured": "你目前承受压力，回答中会带出口误、停顿、过度解释等紧张迹象。措辞变得过于精确，或主动更改故事细节。",
        "broken": "你已近情绪崩溃，倾向于坦白或揭露隐藏的陈述。语气颤抖，可能承认部分事实。",
    }

    async def generate_response(
        self,
        suspect: Suspect,
        case: Case,
        user_question: str,
        conversation_history: List[Dict[str, str]] = None,
        is_private: bool = True,
        other_suspects_present: List[str] = None,
        current_state: str = "calm",
    ) -> str:
        """
        生成嫌疑人的回复

        Args:
            suspect: 当前嫌疑人
            case: 案件信息
            user_question: 用户的问题
            conversation_history: 对话历史
            is_private: 是否是单独审讯（密室问话）
            other_suspects_present: 在场的其他嫌疑人（仅全体质询时）

        Returns:
            她疑人的回复
        """
        logger.info(f"[SuspectAgent] 生成回复: {suspect.name}, 问题: {user_question[:50]}...")
        settings = get_settings()
        if not settings.openai_api_key:
            return self._generate_mock_response(suspect, case, user_question, is_private)

        # 上下文截断：防止对话历史线性增长超出 LLM 上下文窗口
        raw_history = conversation_history or []
        original_count = len(raw_history)

        # 1. 按消息数量截断：保留最近 N 轮（每轮含 user + assistant 2 条消息）
        max_messages = settings.suspect_agent_max_history_messages * 2  # 每轮 2 条
        if original_count > max_messages:
            raw_history = raw_history[-max_messages:]
            logger.info(
                f"[SuspectAgent] 历史消息数量截断: {original_count} -> {len(raw_history)} "
                f"(保留最近 {settings.suspect_agent_max_history_messages} 轮)"
            )

        # 2. 按 token 数量截断
        max_tokens = settings.suspect_agent_max_history_tokens
        history_tokens = sum(
            estimate_token_count(msg.get("content", ""), model=settings.openai_model)
            for msg in raw_history
        )
        if history_tokens > max_tokens:
            raw_history = truncate_messages_by_token(
                raw_history, max_tokens=max_tokens, model=settings.openai_model
            )
            new_tokens = sum(
                estimate_token_count(msg.get("content", ""), model=settings.openai_model)
                for msg in raw_history
            )
            logger.info(
                f"[SuspectAgent] 历史消息 token 截断: {history_tokens} -> {new_tokens} tokens, "
                f"消息数 {original_count} -> {len(raw_history)}"
            )

        # 构建对话历史为 LangChain messages
        history = []
        for msg in raw_history:
            if msg.get("role") == "user":
                history.append(HumanMessage(content=msg["content"]))
            else:
                history.append(AIMessage(content=msg["content"]))

        # 构建在场人员背景信息（其他嫌疑人、证人）
        other_suspects = [s for s in case.suspects if s.id != suspect.id]
        other_suspects_block = "\n".join(
            f"- {s.name}：{s.background}" for s in other_suspects
        ) if other_suspects else "（无其他嫌疑人）"

        witnesses_block = "\n".join(
            f"- {w.name}（{w.occupation}）：{w.relationship_to_case}"
            for w in (case.witnesses or [])
        ) if case.witnesses else "（无证人）"

        state_directive = self._STATE_DIRECTIVES.get(current_state, self._STATE_DIRECTIVES["calm"])

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
                "other_suspects_block": other_suspects_block,
                "witnesses_block": witnesses_block,
                "interrogation_mode": "私下单独审讯" if is_private else "全体质询，其他嫌疑人在场",
                "user_question": user_question,
                "history": history,
                "state_directive": state_directive,
            },
            fallback_fn=lambda: self._generate_mock_response(suspect, case, user_question, is_private),
        )
        return result.content if hasattr(result, "content") else str(result)

    async def detect_lie(
        self,
        suspect: Suspect,
        response: str,
        case: Case
    ) -> Dict[str, Any]:
        """
        检测嫌疑人是否在说谎

        Args:
            suspect: 当前嫌疑人
            response: 嫌疑人的回复
            case: 案件信息

        Returns:
            包含 lie_detected, confidence, microexpression 等信息的字典
        """
        logger.info(f"[SuspectAgent] 检测谎言: {suspect.name}")
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

    async def generate_interjection(
        self,
        responding_suspect: Suspect,
        other_suspect: Suspect,
        case: Case,
        context: str
    ) -> Optional[str]:
        """
        生成嫌疑人的插话/反驳（全体质询时）

        Args:
            responding_suspect: 刚刚说话的嫌疑人
            other_suspect: 要插插的嫌疑人
            case: 案件信息
            context: 对话上下文

        Returns:
            插话内容，可能为None（不是每次都插话）
        """
        logger.info(f"[SuspectAgent] 生成插话: {other_suspect.name} -> {responding_suspect.name}")
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

    async def confront_with_clue(
        self,
        suspect: Suspect,
        case: Case,
        clue: Any,  # Clue 实例
        conversation_history: List[Dict[str, str]] = None,
        other_suspects_block: str = "",
        witnesses_block: str = "",
        current_state: str = "calm",
    ) -> Dict[str, Any]:
        """
        嫌疑人对出示线索的回应（对质）

        Args:
            suspect: 当前嫌疑人
            case: 案件信息
            clue: 出示的线索
            conversation_history: 对话历史
            other_suspects_block: 其他嫌疑人信息块
            witnesses_block: 证人信息块
            current_state: 当前嫌疑人状态（calm/pressured/broken）

        Returns:
            {
                response: str,
                relevance: str (irrelevant|related|critical),
                statement_refuted_id: Optional[str],
                status_delta: Dict[str, str] | None,
                suggested_verification: bool
            }
        """
        logger.info(f"[SuspectAgent] 对质线索: {suspect.name}, clue={clue.id}, state={current_state}")
        settings = get_settings()
        if not settings.openai_api_key:
            return self._generate_mock_confront_response(suspect, case, clue)

        # 构建陈述块
        statements_block = "\n".join(
            f"- [{stmt.id}] {stmt.content}"
            for stmt in suspect.statements
        ) if suspect.statements else "（无已知陈述）"

        # 构建对话历史
        raw_history = conversation_history or []
        history = []
        for msg in raw_history:
            if msg.get("role") == "user":
                history.append(HumanMessage(content=msg["content"]))
            else:
                history.append(AIMessage(content=msg["content"]))

        state_directive = self._STATE_DIRECTIVES.get(current_state, self._STATE_DIRECTIVES["calm"])

        chain = suspect_confront_clue_prompt | self.llm
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
                "other_suspects_block": other_suspects_block or "（无其他嫌疑人）",
                "witnesses_block": witnesses_block or "（无证人）",
                "statements_block": statements_block,
                "clue_label": getattr(clue, "user_label", None) or clue.description[:30],
                "clue_description": clue.description,
                "clue_quoted_text": getattr(clue, "quoted_text", None) or clue.description,
                "history": history,
                "state_directive": state_directive,
            },
            fallback_fn=lambda: self._generate_mock_confront_response(suspect, case, clue),
            parse_json=True,
        )

        if isinstance(result, dict):
            # 归一化 key 别名
            normalized = self._normalize_confront_result(result)
            return normalized
        return self._generate_mock_confront_response(suspect, case, clue)

    def _normalize_confront_result(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """归一化 LLM 返回的对质结果，处理可能的 key 别名"""
        relevance = raw.get("relevance", "irrelevant")
        # 校验 relevance 合法性
        if relevance not in ("irrelevant", "related", "critical"):
            relevance = "irrelevant"

        suggested = raw.get("suggested_verification", False)
        if isinstance(suggested, str):
            suggested = suggested.lower() in ("true", "yes", "1")

        status_delta = raw.get("status_delta")
        if status_delta and not isinstance(status_delta, dict):
            status_delta = None

        statement_refuted_id = raw.get("statement_refuted_id")
        if statement_refuted_id is not None and not isinstance(statement_refuted_id, str):
            statement_refuted_id = None

        return {
            "response": raw.get("response", "……（沉默）"),
            "relevance": relevance,
            "statement_refuted_id": statement_refuted_id,
            "status_delta": status_delta,
            "suggested_verification": suggested,
        }

    def _generate_mock_confront_response(
        self,
        suspect: Suspect,
        case: Case,
        clue: Any,
    ) -> Dict[str, Any]:
        """生成模拟的对质回复（API key 缺失时降级）"""
        # 简单启发式：若 clue 的 related_suspect_ids 包含 suspect.id → critical
        related_ids = getattr(clue, "related_suspect_ids", [])
        if suspect.id in related_ids:
            relevance = "critical"
            response = f"这……这不可能！{clue.description[:20]}……我从未见过这个！请你相信我，{suspect.name}绝不会做这种事！"
            status_delta = {"from": "calm", "to": "pressured"}
            suggested = True
        elif len(related_ids) == 0:
            # 与嫌疑人完全无关的线索 → 固定 irrelevant，保证测试确定性
            relevance = "irrelevant"
            response = f"抱歉，我不明白这条线索与我有何关系。{suspect.name}对此一无所知。"
            status_delta = None
            suggested = False
        elif random.random() < 0.4:
            relevance = "related"
            response = f"这确实让我有些不安。{clue.description[:20]}……我记得好像在哪里听说过，但具体细节我记不清了。"
            status_delta = {"from": "calm", "to": "pressured"}
            suggested = True
        else:
            relevance = "irrelevant"
            response = f"抱歉，我不明白这条线索与我有何关系。{suspect.name}对此一无所知。"
            status_delta = None
            suggested = False

        return {
            "response": response,
            "relevance": relevance,
            "statement_refuted_id": None,
            "status_delta": status_delta,
            "suggested_verification": suggested,
        }

    def _generate_mock_response(
        self,
        suspect: Suspect,
        case: Case,
        user_question: str,
        is_private: bool
    ) -> str:
        """生成模拟的嫌疑人回复（临时实现）"""
        question_lower = user_question.lower()

        # 根据问题类型生成不同回复
        if "昨晚" in question_lower or "时间" in question_lower or "哪里" in question_lower:
            # 关于时间线的问题
            responses = [
                f"我...我在自己的房间里。{suspect.name}绝不会做这种可怕的事情！",
                f"让我想想...昨晚我很早就休息了。我真的什么都不知道。",
                f"我为什么要告诉你？你在怀疑我吗？",
            ]
            return random.choice(responses)
        elif "死者" in question_lower or "布莱克伍德" in question_lower:
            # 关于死者的问题
            responses = [
                f"布莱克伍德先生...他是个复杂的人。有些人不喜欢他，但不是我。",
                f"我只是为他工作。我尽量不去打听他的私事。",
                f"他对我一直很好...至少表面上是这样。",
            ]
            return random.choice(responses)
        elif "凶器" in question_lower or "烛台" in question_lower or "刀" in question_lower:
            # 关于凶器的问题
            responses = [
                "我...我不知道那是什么。我从没见过那样的东西。",
                "这太可怕了！你怎么能认为我和这个有关？",
                "我想我在书房里见过类似的东西，但我不确定。",
            ]
            return random.choice(responses)
        else:
            # 通用回复
            responses = [
                f"请原谅，{suspect.name}不太明白你的意思。能再说一遍吗？",
                "这真是个令人不安的问题。我需要想想怎么回答。",
                "我向你保证，我和这起可怕的事件毫无关系。",
                f"你应该去问问其他人。{suspect.name}真的没什么可说的。",
            ]
            return random.choice(responses)

    def _generate_mock_lie_detection(
        self,
        suspect: Suspect,
        response: str
    ) -> Dict[str, Any]:
        """生成模拟的谎言检测结果"""
        # 随机决定是否检测到谎言
        lie_detected = random.random() < 0.3
        confidence = random.uniform(0.4, 0.8) if lie_detected else random.uniform(0.2, 0.5)

        microexpressions = [
            "眼神躲闪",
            "双手紧张地绞在一起",
            "语速突然加快",
            "喉咙吞咽动作",
            "脚尖微微转向门口",
        ]

        return {
            "lie_detected": lie_detected,
            "confidence": confidence,
            "microexpression": random.choice(microexpressions) if lie_detected else None,
            "notes": "需要更多证据来确认" if lie_detected else "言辞似乎一致"
        }

    def _generate_mock_interjection(
        self,
        responding_suspect: Suspect,
        other_suspect: Suspect,
        case: Case
    ) -> Optional[str]:
        """生成模拟的插话/反驳"""
        # 30%的概率插话
        if random.random() > 0.3:
            return None

        interjections = [
            f"等等！{responding_suspect.name}在说谎！我昨晚明明看到他了！",
            f"这不可能！我知道{responding_suspect.name}那天晚上在做什么！",
            f"你怎么能这么说？{responding_suspect.name}，你明明不是这样告诉我的！",
        ]
        return random.choice(interjections)


# 全局嫌疑人 Agent 实例
_suspect_agent: Optional[SuspectAgent] = None


def get_suspect_agent() -> SuspectAgent:
    """获取嫌疑人 Agent 单例"""
    global _suspect_agent
    if _suspect_agent is None:
        _suspect_agent = SuspectAgent()
    return _suspect_agent
