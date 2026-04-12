"""
华生NPC Agent - 主动的探案伙伴
"""
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.config import get_settings
from app.models.case import Observation, Inference, Hypothesis, Clue, DeductionChain


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

    async def analyze_deduction(
        self,
        deduction_chain: DeductionChain,
        logic_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析推理链条并给出反馈

        Args:
            deduction_chain: 当前的推理链条
            logic_gaps: 检测到的逻辑缺口

        Returns:
            包含分析和建议的字典
        """
        logger.info(f"[WatsonAgent] 分析推理链条 (推理: {len(deduction_chain.inferences)}, 假设: {len(deduction_chain.hypotheses)})")

        # 生成整体分析
        analysis = self._generate_deduction_analysis(deduction_chain, logic_gaps)

        # 生成具体建议
        suggestions = self._generate_deduction_suggestions(deduction_chain, logic_gaps)

        return {
            "analysis": analysis,
            "suggestions": suggestions
        }

    def _generate_deduction_analysis(
        self,
        deduction_chain: DeductionChain,
        logic_gaps: List[Dict[str, Any]]
    ) -> str:
        """生成推理分析"""
        if len(deduction_chain.inferences) == 0 and len(deduction_chain.hypotheses) == 0:
            return "我们才刚刚开始，老朋友。让我们先整理一下已有的观察记录，看看能得出什么推论。"

        # 检查逻辑缺口
        if len(logic_gaps) > 0:
            gap = logic_gaps[0]
            if gap["type"] == "unused_observations":
                return f"我注意到还有一些观察记录没有被用到。也许我们应该看看能不能把它们也纳入推理中？"
            elif gap["type"] == "insufficient_evidence":
                return "这个推论很有意思，但我觉得证据还不够充分。我们需要更多的支持。"
            elif gap["type"] == "insufficient_inferences":
                return "这个假设还需要更多的推理节点来支撑。让我们一步步来。"

        # 根据推理数量给出反馈
        if len(deduction_chain.hypotheses) > 0:
            hypothesis = deduction_chain.hypotheses[-1]
            if hypothesis.is_verified:
                return f"很好！我们已经验证了'{hypothesis.title}'这个假设。看来我们正朝着正确的方向前进。"
            else:
                return f"'{hypothesis.title}'是一个有趣的假设。你觉得我们应该如何验证它？"

        if len(deduction_chain.inferences) >= 3:
            return "我们已经有了几个可靠的推论。也许是时候开始形成一些假设了？"

        return "我们的推理正在逐步成型。继续把观察记录联系起来，看看能发现什么。"

    def _generate_deduction_suggestions(
        self,
        deduction_chain: DeductionChain,
        logic_gaps: List[Dict[str, Any]]
    ) -> List[str]:
        """生成推理建议"""
        suggestions = []

        # 基于逻辑缺口生成建议
        for gap in logic_gaps:
            if gap["type"] == "unused_observations":
                suggestions.append(f"考虑将未使用的观察记录整合到推理中")
            elif gap["type"] == "insufficient_evidence":
                suggestions.append(f"为推理寻找更多的支持证据")
            elif gap["type"] == "insufficient_inferences":
                suggestions.append(f"建立更多推理节点来支撑假设")
            elif gap["type"] == "no_suspect_linked":
                suggestions.append(f"考虑将假设与具体嫌疑人关联起来")

        # 通用建议
        if len(deduction_chain.inferences) > 0 and len(deduction_chain.hypotheses) == 0:
            suggestions.append("尝试基于现有的推理提出一个假设")

        if len(deduction_chain.hypotheses) > 0:
            unverified = [h for h in deduction_chain.hypotheses if not h.is_verified]
            if len(unverified) > 0:
                suggestions.append(f"考虑如何验证'{unverified[0].title}'这个假设")

        # 确保有一些建议
        if len(suggestions) == 0:
            suggestions.append("继续收集更多线索")
            suggestions.append("回顾已有的观察记录，看看有没有新的发现")
            suggestions.append("考虑与嫌疑人再次交谈")

        return suggestions[:3]  # 最多返回3个建议


# 全局华生Agent实例
_watson_agent: Optional[WatsonAgent] = None


def get_watson_agent() -> WatsonAgent:
    """获取华生Agent单例"""
    global _watson_agent
    if _watson_agent is None:
        _watson_agent = WatsonAgent()
    return _watson_agent
