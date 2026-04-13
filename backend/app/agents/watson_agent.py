"""
华生NPC Agent - 主动的探案伙伴
"""
import random
from typing import List, Optional, Dict, Any, Tuple
from loguru import logger
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.models.case import Observation, Inference, Hypothesis, Clue, DeductionChain
from app.models.game import WatsonChatContext


class WatsonAgent:
    """华生NPC Agent类"""

    def __init__(self):
        """初始化华生Agent"""
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
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
        return random.choice(encouragements)

    def _generate_mock_observation_comment(self, observation: Observation) -> str:
        """生成模拟的观察评论（临时实现）"""
        comments = [
            f"嗯，{observation.description}——这很有意思。你怎么看？",
            f"我注意到{observation.description}。这让我想到了什么，但还不太确定...",
            f"好发现！{observation.description}可能是个重要的线索。",
            f"你看，{observation.description}。不知道这和案子有什么关系？",
        ]
        return random.choice(comments)

    def _generate_mock_reasoning_question(self, inference: Inference) -> str:
        """生成模拟的推理疑问（临时实现）"""
        questions = [
            f"关于 '{inference.content}'——你确定吗？有没有其他可能性？",
            f"有意思的推论。但有没有什么证据能支持这一点？",
            f"如果这是真的，那会如何影响我们对整个案件的看法？",
            f"我不是质疑你，只是想再确认一下——这个推理的依据是什么？",
        ]
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

    async def chat(
        self,
        user_message: str,
        context: WatsonChatContext
    ) -> Tuple[str, str]:
        """
        与华生进行自由对话

        Args:
            user_message: 用户的消息
            context: 对话上下文（当前游戏状态）

        Returns:
            (response, message_type) - 华生的回复和消息类型
        """
        logger.info(f"[WatsonAgent] 收到用户消息: {user_message[:50]}...")

        # 分析消息类型
        message_type = self._classify_message(user_message, context)
        logger.info(f"[WatsonAgent] 消息类型: {message_type}")

        # 根据类型生成回复
        response = await self._generate_response(user_message, message_type, context)

        return response, message_type

    def _classify_message(self, message: str, context: WatsonChatContext) -> str:
        """分类用户消息类型"""
        message_lower = message.lower()

        # 阶段指导关键词
        guidance_keywords = [
            "下一步", "该做什么", "接下来", "应该", "去哪", "哪里",
            "how", "what", "next", "where", "should"
        ]
        if any(keyword in message_lower for keyword in guidance_keywords):
            return "guidance"

        # 线索讨论关键词
        clue_keywords = [
            "线索", "这个", "意味着", "意思", "觉得", "看",
            "clue", "mean", "think", "look"
        ]
        if any(keyword in message_lower for keyword in clue_keywords) and context.clues_collected > 0:
            return "clue_discussion"

        # 嫌疑人分析关键词
        suspect_keywords = [
            "嫌疑人", "他", "她", "说谎", "动机", "觉得",
            "suspect", "he", "she", "lie", "motive"
        ]
        if any(keyword in message_lower for keyword in suspect_keywords):
            return "suspect_analysis"

        # 推理梳理关键词
        deduction_keywords = [
            "推理", "完整", "逻辑", "缺口", "假设",
            "deduction", "logic", "gap", "hypothesis"
        ]
        if any(keyword in message_lower for keyword in deduction_keywords):
            return "deduction_review"

        # 知识咨询关键词
        knowledge_keywords = [
            "医学", "军事", "毒药", "伤口", "火药", "血迹",
            "medical", "military", "poison", "wound", "gunpowder", "blood"
        ]
        if any(keyword in message_lower for keyword in knowledge_keywords):
            return "knowledge"

        # 情感支持关键词
        encouragement_keywords = [
            "累", "难", "困惑", "毫无头绪", "不知道", "放弃",
            "tired", "hard", "confused", "stuck", "give up"
        ]
        if any(keyword in message_lower for keyword in encouragement_keywords):
            return "encouragement"

        # 默认类型
        return "general"

    async def _generate_response(
        self,
        message: str,
        message_type: str,
        context: WatsonChatContext
    ) -> str:
        """根据消息类型生成回复"""

        # TODO: 实际调用LLM生成回复，当前使用mock实现

        if message_type == "guidance":
            return self._generate_guidance_response(context)
        elif message_type == "clue_discussion":
            return self._generate_clue_discussion_response(context)
        elif message_type == "suspect_analysis":
            return self._generate_suspect_analysis_response(context)
        elif message_type == "deduction_review":
            return self._generate_deduction_review_response(context)
        elif message_type == "knowledge":
            return await self._generate_knowledge_response(message)
        elif message_type == "encouragement":
            return await self.encourage()
        else:
            return self._generate_general_response(context)

    def _generate_guidance_response(self, context: WatsonChatContext) -> str:
        """生成阶段指导回复"""

        phase_guidance = {
            "start": [
                "让我们先看看这个案子的基本情况，然后前往案发现场。",
                "老朋友，我们先了解一下受害者和嫌疑人，然后开始调查吧！",
                "这个案子看起来很有意思。准备好去现场了吗？"
            ],
            "investigation": [
                f"我们已经收集了 {context.observations_count} 条观察记录。也许再仔细看看现场的其他区域？",
                "让我想想...我们应该继续勘查现场，或者去审问嫌疑人？你觉得呢？",
                f"还有一些地方没看过。我们已经检查了 {context.clues_collected} 个线索，继续吧！"
            ],
            "interrogation": [
                f"我们已经询问了 {len(context.suspects_interviewed)} 个嫌疑人。也许应该再和其他人谈谈？",
                "审问进行得怎么样？有没有发现什么矛盾的证词？",
                "注意观察他们的表情和语气，有时候肢体语言比语言更能说明问题。"
            ],
            "deduction": [
                f"我们有 {context.inferences_count} 个推理和 {context.hypotheses_count} 个假设。让我们把它们串起来！",
                "看看我们的推理链条，有没有什么逻辑缺口？",
                "试着把线索和嫌疑人关联起来，看看能不能发现什么。"
            ],
            "conclusion": [
                "是时候做出决定了。你觉得谁是凶手？",
                "让我们回顾一下所有的证据，确保我们没有漏掉什么。",
                "准备好了吗？是时候揭示真相了！"
            ]
        }

        phase = context.game_phase.value if hasattr(context.game_phase, 'value') else context.game_phase
        responses = phase_guidance.get(phase, [
            "让我们继续调查吧！",
            "你觉得我们下一步该怎么做？"
        ])
        return random.choice(responses)

    def _generate_clue_discussion_response(self, context: WatsonChatContext) -> str:
        """生成线索讨论回复"""
        responses = [
            "这条线索很有意思。你觉得它和案子有什么关系？",
            "嗯...让我仔细看看。这可能是关键证据，也可能是个红鲱鱼。",
            "你注意到了吗？这条线索可能指向某个人，但我们需要更多证据。",
            "很有趣的发现！让我们把它记下来，看看能不能和其他线索关联起来。"
        ]
        return random.choice(responses)

    def _generate_suspect_analysis_response(self, context: WatsonChatContext) -> str:
        """生成嫌疑人分析回复"""
        responses = [
            "这个人的证词有些地方值得怀疑。你觉得呢？",
            "我注意到他说话时有些紧张。可能在隐瞒什么？",
            "我们需要更多证据来证实或排除他的嫌疑。",
            "动机是有的，但有没有作案时间呢？这是个关键问题。"
        ]
        return random.choice(responses)

    def _generate_deduction_review_response(self, context: WatsonChatContext) -> str:
        """生成推理梳理回复"""

        if context.hypotheses_count == 0:
            return "我们还没有形成任何假设。先试着把一些观察关联起来形成推理吧！"
        elif context.inferences_count < 3:
            return "我们有了一些推理，但还需要更多。让我们继续把线索关联起来。"
        else:
            responses = [
                "我们的推理正在成型。看看能不能把它们组合成一个完整的假设？",
                "很好！现在让我们验证一下这些假设，看看哪个最合理。",
                "逻辑链条正在形成。你觉得哪个方向最有希望？"
            ]
            return random.choice(responses)

    async def _generate_knowledge_response(self, message: str) -> str:
        """生成知识咨询回复"""
        # 先尝试用现有的知识库
        knowledge = await self.provide_knowledge(message)
        if knowledge:
            return knowledge

        responses = [
            "作为一名军医，我见过不少类似的情况。让我想想...",
            "这让我想起在阿富汗时见过的一些事情。根据我的经验...",
            "我读过一些关于这方面的书籍。从医学角度来看...",
            "这个问题很专业。让我尽力给你一些有用的信息。"
        ]
        return random.choice(responses)

    def _generate_general_response(self, context: WatsonChatContext) -> str:
        """生成通用回复"""
        responses = [
            "有意思，你继续说。",
            "我在听，老朋友。",
            "嗯，这确实值得思考。",
            "好的，让我们仔细想想。",
            "你有什么想法？我很想听听。"
        ]
        return random.choice(responses)


# 全局华生Agent实例
_watson_agent: Optional[WatsonAgent] = None


def get_watson_agent() -> WatsonAgent:
    """获取华生Agent单例"""
    global _watson_agent
    if _watson_agent is None:
        _watson_agent = WatsonAgent()
    return _watson_agent
