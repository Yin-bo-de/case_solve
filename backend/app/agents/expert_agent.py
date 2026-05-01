"""
专家 Agent - 皇家法医等技术专家，完全可信，只基于相关物证发言
"""
import random
from typing import List, Optional, Dict, Any
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from app.config import get_settings
from app.models.case import Expert, Case
from app.agents.prompts.expert_prompts import expert_response_prompt
from app.agents._llm_helpers import invoke_with_retry


class ExpertAgent:
    """专家 Agent 类（法医）"""

    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.4,  # 专家回答需要更低温度以保证严谨性
        )
        logger.info("[ExpertAgent] 初始化专家 Agent")

    async def get_preliminary_report(self, expert: Expert, case: Case) -> str:
        """
        获取专家初步报告。
        优先返回案件生成时已写好的 preliminary_report，为空时通过 LLM 生成兜底。

        Args:
            expert: 专家对象
            case: 案件信息

        Returns:
            初步报告文本
        """
        if expert.preliminary_report and expert.preliminary_report.strip():
            logger.info(f"[ExpertAgent] 使用预生成报告: {expert.name}")
            return expert.preliminary_report

        logger.info(f"[ExpertAgent] preliminary_report 为空，LLM 生成兜底: {expert.name}")
        settings = get_settings()
        if not settings.openai_api_key:
            return self._generate_mock_preliminary_report(expert, case)

        related_clue_desc = self._build_related_clue_descriptions(expert, case)
        chain = expert_response_prompt | self.llm
        result = await invoke_with_retry(
            chain=chain,
            inputs={
                "expert_name": expert.name,
                "title": expert.title,
                "expertise": "、".join(expert.expertise) if expert.expertise else "法医病理",
                "related_clue_descriptions": related_clue_desc,
                "methodology_notes": "\n".join(f"- {n}" for n in expert.methodology_notes) or "（无特别局限说明）",
                "user_question": "请给出您的初步法医报告。",
                "history": [],
            },
            fallback_fn=lambda: self._generate_mock_preliminary_report(expert, case),
        )
        return result.content if hasattr(result, "content") else str(result)

    async def answer_question(
        self,
        expert: Expert,
        case: Case,
        user_question: str,
        conversation_history: List[Dict[str, str]] = None,
    ) -> str:
        """
        回答侦探的技术问题，只能基于 related_clue_ids 中的物证发言。

        Args:
            expert: 专家对象
            case: 案件信息
            user_question: 侦探的问题
            conversation_history: 对话历史

        Returns:
            专家的回复
        """
        logger.info(f"[ExpertAgent] 回答问题: {expert.name}, 问题: {user_question[:50]}...")
        settings = get_settings()
        if not settings.openai_api_key:
            return self._generate_mock_response(expert, user_question)

        raw_history = conversation_history or []
        max_messages = settings.expert_agent_max_history_messages * 2
        if len(raw_history) > max_messages:
            raw_history = raw_history[-max_messages:]

        history = []
        for msg in raw_history:
            if msg.get("role") == "user":
                history.append(HumanMessage(content=msg["content"]))
            else:
                history.append(AIMessage(content=msg["content"]))

        related_clue_desc = self._build_related_clue_descriptions(expert, case)
        chain = expert_response_prompt | self.llm
        result = await invoke_with_retry(
            chain=chain,
            inputs={
                "expert_name": expert.name,
                "title": expert.title,
                "expertise": "、".join(expert.expertise) if expert.expertise else "法医病理",
                "related_clue_descriptions": related_clue_desc,
                "methodology_notes": "\n".join(f"- {n}" for n in expert.methodology_notes) or "（无特别局限说明）",
                "user_question": user_question,
                "history": history,
            },
            fallback_fn=lambda: self._generate_mock_response(expert, user_question),
        )
        return result.content if hasattr(result, "content") else str(result)

    def _build_related_clue_descriptions(self, expert: Expert, case: Case) -> str:
        """构建专家可引用的物证描述块（反幻觉核心）"""
        if not expert.related_clue_ids or not case.clues:
            return "（暂无已分析的物证）"
        relevant = [c for c in case.clues if c.id in expert.related_clue_ids]
        if not relevant:
            return "（暂无已分析的物证）"
        lines = []
        for c in relevant:
            label = c.user_label or c.id
            lines.append(f"- [{c.id}] {label}：{c.description}（发现于：{c.location or '不明地点'}）")
        return "\n".join(lines)

    def _generate_mock_preliminary_report(self, expert: Expert, case: Case) -> str:
        """mock 降级：从 expert 对象拼接初步报告"""
        if expert.key_findings:
            findings_text = "；".join(f.finding for f in expert.key_findings[:2])
            return (
                f"根据本人对现场及遗体的初步检验，死者{case.victim_name}死于{case.cause_of_death}。"
                f"死亡时间估计为{case.time_of_death}，误差约在一小时以内。"
                f"初步发现：{findings_text}。"
                f"完整报告尚待进一步化验确认。"
            )
        return (
            f"初步法医检验已完成。死者死因为{case.cause_of_death}，"
            f"死亡时间{case.time_of_death}。现场物证已采集，化验结果需数日出具。"
        )

    def _generate_mock_response(self, expert: Expert, user_question: str) -> str:
        """mock 降级：根据问题关键词返回专业回复"""
        question_lower = user_question.lower()
        if any(kw in question_lower for kw in ["死亡时间", "几点", "何时"]):
            return f"根据尸体僵硬程度与体温推算，死亡时间窗口为{next((f.finding for f in expert.key_findings if '时间' in f.topic), '案发当晚数小时内')}。此推断存在±30分钟的误差。"
        elif any(kw in question_lower for kw in ["凶器", "伤口", "伤痕", "血迹"]):
            if expert.key_findings:
                return f"从伤口特征分析，{expert.key_findings[0].finding}。具体物证尚需进一步化验。"
            return "伤口呈典型钝器损伤形态，凶器应为质地坚硬的金属物品，具体型号待化验确认。"
        elif any(kw in question_lower for kw in ["动机", "凶手", "嫌疑人", "谁"]):
            return "恕我直言，判断动机与锁定凶手超出了法医工作的范围。本人只能就物证提供客观分析。"
        elif any(kw in question_lower for kw in ["报告", "总结", "概述"]):
            return self._generate_mock_preliminary_report(expert, Case(
                id="mock", victim_name="死者", victim_background="",
                cause_of_death="钝器伤", time_of_death="昨晚10点前后",
                location="", date=__import__('datetime').datetime.utcnow()
            ))
        return "根据现有物证，目前尚无法得出更进一步的结论。如您有具体的物证疑问，我可以详细解答。"


# 全局专家 Agent 单例
_expert_agent: Optional[ExpertAgent] = None


def get_expert_agent() -> ExpertAgent:
    """获取专家 Agent 单例"""
    global _expert_agent
    if _expert_agent is None:
        _expert_agent = ExpertAgent()
    return _expert_agent
