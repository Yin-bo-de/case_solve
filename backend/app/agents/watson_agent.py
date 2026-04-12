"""
华生NPC Agent - 主动的探案伙伴
"""
from typing import List, Optional
from loguru import logger
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.config import get_settings
from app.models.case import Observation, Inference, Hypothesis, Clue


class WatsonAgent:
    """华生NPC Agent类"""

    def __init__(self):
        """初始化华生Agent"""
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7,
        )
        logger.info("[WatsonAgent] 初始化华生NPC Agent")

    async def share_observation(self, observation: Observation) -> str:
        """
        分享观察到的细节

        Args:
            observation: 用户刚刚发现的观察

        Returns:
            华生的评论
        """
        logger.info(f"[WatsonAgent] 分享观察: {observation.id}")
        # TODO: 实际调用LLM生成评论
        return self._generate_mock_observation_comment(observation)

    async def question_reasoning(self, inference: Inference) -> str:
        """
        对推理提出疑问

        Args:
            inference: 用户刚刚做出的推理

        Returns:
            华生的疑问或评论
        """
        logger.info(f"[WatsonAgent] 质疑推理: {inference.id}")
        # TODO: 实际调用LLM生成评论
        return self._generate_mock_reasoning_question(inference)

    async def suggest_hypothesis(self, observations: List[Observation]) -> Optional[str]:
        """
        偶尔提出自己的（可能错误的）推理

        Args:
            observations: 已有的观察列表

        Returns:
            华生的假设，可能为None（不是每次都说话）
        """
        logger.info(f"[WatsonAgent] 考虑是否提出假设 (已有 {len(observations)} 个观察)")
        # TODO: 实际调用LLM生成假设
        return None

    async def provide_knowledge(self, topic: str) -> Optional[str]:
        """
        提供医学、军事等方面的专业知识

        Args:
            topic: 知识主题

        Returns:
            华生的专业知识
        """
        logger.info(f"[WatsonAgent] 提供关于 '{topic}' 的知识")
        # TODO: 实际调用LLM生成知识
        return self._generate_mock_knowledge(topic)

    async def encourage(self) -> str:
        """
        在玩家困惑时给予鼓励

        Returns:
            鼓励的话语
        """
        logger.info("[WatsonAgent] 鼓励玩家")
        encouragements = [
            "别灰心，老朋友！我们会一起解开这个谜题的。",
            "记住，排除所有不可能的，剩下的无论多么不可思议，那就是真相！",
            "让我们再仔细看看这些线索，也许漏掉了什么。",
            "我相信你的推断能力，我们继续前进！",
        ]
        import random
        return random.choice(encouragements)

    def _generate_mock_observation_comment(self, observation: Observation) -> str:
        """生成模拟的观察评论（临时实现）"""
        comments = [
            f"嗯，{observation.description}——这很有意思。你怎么看？",
            f"我注意到{observation.description}。这让我想到了什么，但还不太确定...",
            f"好发现！{observation.description}可能是个重要的线索。",
            f"你看，{observation.description}。不知道这和案子有什么关系？",
        ]
        import random
        return random.choice(comments)

    def _generate_mock_reasoning_question(self, inference: Inference) -> str:
        """生成模拟的推理疑问（临时实现）"""
        questions = [
            f"关于 '{inference.content}'——你确定吗？有没有其他可能性？",
            f"有意思的推论。但有没有什么证据能支持这一点？",
            f"如果这是真的，那会如何影响我们对整个案件的看法？",
            f"我不是质疑你，只是想再确认一下——这个推理的依据是什么？",
        ]
        import random
        return random.choice(questions)

    def _generate_mock_knowledge(self, topic: str) -> Optional[str]:
        """生成模拟的专业知识（临时实现）"""
        knowledge_base = {
            "医学": "作为一名军医，我见过很多伤口。钝器伤通常会造成不规则的伤口边缘，而锐器伤则更干净利落。",
            "血迹": "血液干涸的时间可以告诉我们很多。一般来说，室温下血液在1-2小时内会完全干涸。",
            "火药": "我在阿富汗见过不少枪伤。火药灼伤通常会在皮肤上留下黑色的斑点，而且有明显的硫磺味。",
            "毒药": "不同的毒药有不同的症状。砷中毒通常会导致剧烈的胃痛和呕吐，而氰化物则几乎是立即致命的。",
        }
        for key, knowledge in knowledge_base.items():
            if key in topic:
                return knowledge
        return None


# 全局华生Agent实例
_watson_agent: Optional[WatsonAgent] = None


def get_watson_agent() -> WatsonAgent:
    """获取华生Agent单例"""
    global _watson_agent
    if _watson_agent is None:
        _watson_agent = WatsonAgent()
    return _watson_agent
