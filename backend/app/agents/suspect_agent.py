"""
嫌疑人 Agent - 符合维多利亚时代特征的对话
"""
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime
import random

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.config import get_settings
from app.models.case import Suspect, Case


class SuspectAgent:
    """嫌疑人 Agent 类"""

    def __init__(self):
        """初始化嫌疑人 Agent"""
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.8,
        )
        logger.info("[SuspectAgent] 初始化嫌疑人 Agent")

    async def generate_response(
        self,
        suspect: Suspect,
        case: Case,
        user_question: str,
        conversation_history: List[Dict[str, str]] = None,
        is_private: bool = True,
        other_suspects_present: List[str] = None
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
            嫌疑人的回复
        """
        logger.info(f"[SuspectAgent] 生成回复: {suspect.name}, 问题: {user_question[:50]}...")
        # TODO: 实际调用LLM生成回复
        return self._generate_mock_response(
            suspect, case, user_question, is_private
        )

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
        # TODO: 实际调用LLM检测谎言
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
            other_suspect: 要插话的嫌疑人
            case: 案件信息
            context: 对话上下文

        Returns:
            插话内容，可能为None（不是每次都插话）
        """
        logger.info(f"[SuspectAgent] 生成插话: {other_suspect.name} -> {responding_suspect.name}")
        # TODO: 实际调用LLM生成插话
        return self._generate_mock_interjection(
            responding_suspect, other_suspect, case
        )

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
