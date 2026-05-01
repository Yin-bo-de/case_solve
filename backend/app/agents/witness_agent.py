"""
证人 Agent - 目击者/邻居等证人的对话，可能因恐惧或利益有所保留
"""
import random
from typing import List, Optional, Dict, Any
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from app.config import get_settings
from app.models.case import Witness, Case
from app.agents.prompts.witness_prompts import (
    witness_response_prompt,
    witness_credibility_prompt,
)
from app.agents._llm_helpers import invoke_with_retry, truncate_messages_by_token, estimate_token_count


class WitnessAgent:
    """证人 Agent 类"""

    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7,
            extra_body={"enable_thinking": False},
        )
        logger.info("[WitnessAgent] 初始化证人 Agent")

    async def generate_response(
        self,
        witness: Witness,
        case: Case,
        user_question: str,
        conversation_history: List[Dict[str, str]] = None,
    ) -> str:
        """
        生成证人回复

        Args:
            witness: 证人对象
            case: 案件信息
            user_question: 侦探的问题
            conversation_history: 对话历史 [{role, content}]

        Returns:
            证人的回复文本
        """
        logger.info(f"[WitnessAgent] 生成回复: {witness.name}, 问题: {user_question[:50]}...")
        settings = get_settings()
        if not settings.openai_api_key:
            return self._generate_mock_response(witness, user_question)

        raw_history = conversation_history or []
        original_count = len(raw_history)
        max_messages = settings.witness_agent_max_history_messages * 2
        if original_count > max_messages:
            raw_history = raw_history[-max_messages:]
            logger.debug(f"[WitnessAgent] 历史截断: {original_count} -> {len(raw_history)}")

        history = []
        for msg in raw_history:
            if msg.get("role") == "user":
                history.append(HumanMessage(content=msg["content"]))
            else:
                history.append(AIMessage(content=msg["content"]))

        # 构建撒谎上下文
        lying_context, lying_instruction = self._build_lying_context(witness, case)

        key_observations_block = "\n".join(
            f"- {obs}" for obs in witness.key_observations
        ) if witness.key_observations else "（无特别目击记录）"

        chain = witness_response_prompt | self.llm
        result = await invoke_with_retry(
            chain=chain,
            inputs={
                "witness_name": witness.name,
                "occupation": witness.occupation,
                "relationship_to_case": witness.relationship_to_case,
                "timeline": witness.timeline,
                "personality_traits": "、".join(witness.personality_traits) if witness.personality_traits else "普通市民",
                "key_observations_block": key_observations_block,
                "lying_context": lying_context,
                "lying_instruction": lying_instruction,
                "user_question": user_question,
                "history": history,
            },
            fallback_fn=lambda: self._generate_mock_response(witness, user_question),
        )
        return result.content if hasattr(result, "content") else str(result)

    async def detect_credibility(
        self,
        witness: Witness,
        response: str,
        case: Case,
    ) -> Dict[str, Any]:
        """
        判断证人证词的可信度

        Returns:
            {credibility_concern, concern_type, confidence, microexpression, notes}
        """
        logger.info(f"[WitnessAgent] 可信度判断: {witness.name}")
        settings = get_settings()
        if not settings.openai_api_key:
            return self._generate_mock_credibility(witness, response)

        clues_block = "\n".join(
            f"- [{c.id}] {c.description}" for c in case.clues if c.discovered
        ) or "暂无已发现线索"

        chain = witness_credibility_prompt | self.llm
        result = await invoke_with_retry(
            chain=chain,
            inputs={
                "witness_name": witness.name,
                "is_lying_for_someone": str(witness.is_lying_for_someone),
                "response": response,
                "clues_block": clues_block,
            },
            fallback_fn=lambda: self._generate_mock_credibility(witness, response),
            parse_json=True,
        )
        if isinstance(result, dict):
            return result
        return self._generate_mock_credibility(witness, response)

    def _build_lying_context(self, witness: Witness, case: Case):
        """构建撒谎相关上下文字符串，用于注入 prompt"""
        if witness.is_lying_for_someone and witness.bribed_by_suspect_id:
            bribed_name = next(
                (s.name for s in case.suspects if s.id == witness.bribed_by_suspect_id),
                "某人"
            )
            lying_context = f"你被 {bribed_name} 收买，会淡化/美化其行为"
            lying_instruction = (
                f"当话题涉及 {bribed_name} 时，避谈不利于他/她的细节，"
                "但不主动撒谎陷害他人；若被追问，表现出轻微的紧张与回避"
            )
        elif witness.is_lying_for_someone:
            lying_context = "你出于恐惧而有所保留，不敢透露全部事实"
            lying_instruction = "对敏感问题表现得紧张、回避，用模糊的措辞搪塞；不需要主动撒谎"
        else:
            lying_context = "你是诚实的证人，没有隐瞒动机"
            lying_instruction = "如实回答你目击到的事实，对没目击到的如实说'不知道'"
        return lying_context, lying_instruction

    def _generate_mock_response(self, witness: Witness, user_question: str) -> str:
        """mock 降级：根据问题关键词返回贴合 key_observations 的固定回复"""
        question_lower = user_question.lower()
        if witness.key_observations:
            first_obs = witness.key_observations[0]
            if any(kw in question_lower for kw in ["看到", "目击", "昨晚", "时间", "哪里", "什么时候"]):
                return f"是的，阁下。{first_obs}。不过我也只是看到这些，别的我真的不清楚。"
            elif any(kw in question_lower for kw in ["嫌疑", "怀疑", "谁", "凶手"]):
                return f"我……我不敢妄加揣测。我只是个普通的{witness.occupation}，不懂这些。"
        if witness.is_lying_for_someone:
            return "这个……我当时没注意。真的，我那天很忙，很多细节记不清楚了。"
        return f"请原谅，阁下，我只知道我亲眼见到的事情。我尽量如实回答您的问题。"

    def _generate_mock_credibility(self, witness: Witness, response: str) -> Dict[str, Any]:
        """mock 降级：根据 is_lying_for_someone 生成可信度结果"""
        if witness.is_lying_for_someone:
            concern_type = "bribery" if witness.bribed_by_suspect_id else "fear"
            return {
                "credibility_concern": True,
                "concern_type": concern_type,
                "confidence": round(random.uniform(0.5, 0.75), 2),
                "microexpression": random.choice(["目光闪烁", "双手轻微颤抖", "回答时停顿过长"]),
                "notes": "证人似乎有所保留，部分陈述过于含糊"
            }
        uncertainty = witness.credibility < 0.65
        if uncertainty and random.random() < 0.3:
            return {
                "credibility_concern": True,
                "concern_type": "memory_gap",
                "confidence": round(random.uniform(0.3, 0.55), 2),
                "microexpression": None,
                "notes": "证人记忆可能不够准确，部分细节存疑"
            }
        return {
            "credibility_concern": False,
            "concern_type": None,
            "confidence": round(random.uniform(0.6, 0.85), 2),
            "microexpression": None,
            "notes": "证词基本可信，陈述前后一致"
        }


# 全局证人 Agent 单例
_witness_agent: Optional[WitnessAgent] = None


def get_witness_agent() -> WitnessAgent:
    """获取证人 Agent 单例"""
    global _witness_agent
    if _witness_agent is None:
        _witness_agent = WitnessAgent()
    return _witness_agent
