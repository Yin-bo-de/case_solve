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
from app.models.case import Observation, Inference, Hypothesis, Clue, DeductionChain, Case, Suspect
from app.models.game import WatsonChatContext
from app.agents.prompts.watson_prompts import (
    watson_observation_prompt,
    watson_question_reasoning_prompt,
    watson_knowledge_prompt,
    watson_suggest_hypothesis_prompt,
    watson_chat_prompt,
    watson_scene_hint_prompt,
    watson_interrogation_tips_prompt,
    watson_deduction_hint_prompt,
    watson_contradiction_prompt,
)
from app.agents._llm_helpers import invoke_with_retry


class WatsonAgent:
    """华生NPC Agent类"""

    # 各难度对应的主动触发概率
    _PROACTIVE_RATE_MAP = {
        "easy": 0.8,
        "classic": 0.5,
        "hardcore": 0.2,
    }

    def __init__(self, proactive_rate: float = 0.5):
        """
        初始化华生Agent

        Args:
            proactive_rate: 主动触发概率 (0.0~1.0)，影响 share_observation/question_reasoning
        """
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7,
        )
        self.proactive_rate = proactive_rate
        logger.info(f"[WatsonAgent] 初始化华生NPC Agent (proactive_rate={proactive_rate})")

    def _get_case_context(self, case=None) -> dict:
        """从 case 对象提取 prompt 所需字段，case 为 None 时返回占位符"""
        if case:
            return {
                "victim_name": case.victim_name,
                "case_location": case.location,
                "case_summary": case.summary,
            }
        return {"victim_name": "受害者", "case_location": "案发现场", "case_summary": "维多利亚时代谋杀案"}

    @classmethod
    def from_difficulty(cls, difficulty: str) -> "WatsonAgent":
        """根据游戏难度创建对应主动性的 WatsonAgent 实例"""
        rate = cls._PROACTIVE_RATE_MAP.get(difficulty, 0.5)
        return cls(proactive_rate=rate)

    async def share_observation(self, observation: Observation) -> Optional[str]:
        """
        分享观察到的细节（受 proactive_rate 控制，Hardcore 模式下大概率沉默）

        Args:
            observation: 用户刚刚发现的观察

        Returns:
            华生的评论，或 None（不主动介入时）
        """
        logger.info(f"[WatsonAgent] 分享观察: {observation.id} (rate={self.proactive_rate})")
        if random.random() > self.proactive_rate:
            logger.debug(f"[WatsonAgent] 本次不主动评论（概率门控）")
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

    async def question_reasoning(self, inference: Inference) -> Optional[str]:
        """
        对推理提出疑问（受 proactive_rate 控制）

        Args:
            inference: 用户刚刚做出的推理

        Returns:
            华生的疑问或评论，或 None
        """
        logger.info(f"[WatsonAgent] 质疑推理: {inference.id} (rate={self.proactive_rate})")
        if random.random() > self.proactive_rate:
            logger.debug(f"[WatsonAgent] 本次不主动质疑（概率门控）")
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

    async def suggest_hypothesis(self, observations: List[Observation]) -> Optional[str]:
        """
        偶尔提出自己的（可能错误的）推理

        Args:
            observations: 已有的观察列表

        Returns:
            华生的假设，可能为None（不是每次都说话）
        """
        logger.info(f"[WatsonAgent] 考虑是否提出假设 (已有 {len(observations)} 个观察)")
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

    async def provide_knowledge(self, topic: str) -> Optional[str]:
        """
        提供医学、军事等方面的专业知识

        Args:
            topic: 知识主题

        Returns:
            华生的专业知识
        """
        logger.info(f"[WatsonAgent] 提供关于 '{topic}' 的知识")
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
        settings = get_settings()
        if not settings.openai_api_key:
            # 走原有 mock 分支
            return await self._mock_generate_response(message, message_type, context)

        # 格式化线索、场景、嫌疑人信息块
        clues_block = "\n".join(
            f"- {c['label']}：{c['description']}" for c in context.current_clues
        ) if context.current_clues else "（尚无线索）"

        scenes_block = "\n".join(
            f"- {s['name']}：{s['description']}" for s in context.available_scenes
        ) if context.available_scenes else "（暂无场景信息）"

        suspects_block = "\n".join(
            f"- {s['name']}" for s in context.suspects
        ) if context.suspects else "（暂无嫌疑人信息）"

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
                "current_clues_block": clues_block,
                "available_scenes_block": scenes_block,
                "suspects_block": suspects_block,
                "case_summary": "正在进行中的谋杀案调查",
                "user_message": message,
            },
            fallback_fn=lambda: self._generate_general_response(context),
        )
        return result.content if hasattr(result, "content") else str(result)

    async def _mock_generate_response(
        self,
        message: str,
        message_type: str,
        context: WatsonChatContext
    ) -> str:
        """根据消息类型生成 mock 回复（原有逻辑）"""
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

    # ──────────────────────────────────────────────
    # 章节 6：新增方法
    # ──────────────────────────────────────────────

    async def offer_scene_hint(self, scene_name: str, recent_actions: List[str]) -> str:
        """
        给出当前场景的下一步勘查建议（一句话，维多利亚口吻）。

        Args:
            scene_name: 当前场景名称
            recent_actions: 玩家最近的搜查动作列表
        Returns:
            华生的一句话建议
        """
        logger.info(f"[WatsonAgent] offer_scene_hint scene={scene_name} actions={len(recent_actions)}")
        actions_str = "、".join(recent_actions[-3:]) if recent_actions else "（尚未开始搜查）"

        settings = get_settings()
        if not settings.openai_api_key:
            hints = [
                f"老朋友，我觉得{scene_name}的角落里可能藏着什么不寻常的东西。",
                f"既然您已经{actions_str}，不妨再仔细检查一下那些不起眼的细节。",
                f"在{scene_name}中，有时候最显眼的地方反而藏着关键线索。",
            ]
            return random.choice(hints)

        chain = watson_scene_hint_prompt | self.llm
        result = await invoke_with_retry(
            chain=chain,
            inputs={"scene_name": scene_name, "recent_actions": actions_str},
            fallback_fn=lambda: type("R", (), {"content": f"老朋友，不妨再仔细检查一下{scene_name}中的每一个角落。"})(),
        )
        return result.content if hasattr(result, "content") else str(result)

    async def offer_interrogation_tips(
        self,
        case: Case,
        suspect: Suspect,
        conversation_history: List[Dict[str, str]],
        clues: List[Clue],
    ) -> List[Dict[str, Any]]:
        """
        在审讯过程中实时给出话术建议和矛盾提示（JSON 模式）。

        Args:
            case: 当前案件
            suspect: 被审讯的嫌疑人
            conversation_history: 审讯对话历史
            clues: 已发现的线索列表
        Returns:
            tips 数组，每项含 type / text / related_clue_ids
        """
        logger.info(f"[WatsonAgent] offer_interrogation_tips suspect={suspect.id} clues={len(clues)}")

        fallback_tips = [
            {"type": "suggestion", "text": "不妨直接询问嫌疑人案发当晚的行踪。", "related_clue_ids": []},
        ]

        settings = get_settings()
        if not settings.openai_api_key:
            return fallback_tips

        clues_block = "\n".join([f"  - id={c.id} {c.user_label or c.description[:40]}" for c in clues]) or "（尚无线索）"
        recent_history = conversation_history[-8:]
        conversation_block = "\n".join([f"{m['role']}: {m['content']}" for m in recent_history]) or "（尚未开始）"

        from langchain_core.output_parsers import StrOutputParser
        chain = watson_interrogation_tips_prompt | self.llm | StrOutputParser()
        result = await invoke_with_retry(
            chain=chain,
            inputs={
                "clues_block": clues_block,
                "suspect_name": suspect.name,
                "suspect_id": suspect.id,
                "conversation_block": conversation_block,
            },
            fallback_fn=lambda: f'{{"tips": {fallback_tips}}}',
            parse_json=True,
        )
        if isinstance(result, dict) and "tips" in result:
            logger.info(f"[WatsonAgent] offer_interrogation_tips 完成 tips={len(result['tips'])}")
            return result["tips"]
        return fallback_tips

    async def offer_deduction_hint(
        self,
        clues: List[Clue],
        inferences: List[Inference],
    ) -> str:
        """
        在推理板给出一句关联提示，指出可能被忽略的关联。

        Args:
            clues: 已发现线索列表
            inferences: 现有推理记录列表
        Returns:
            一句话提示
        """
        logger.info(f"[WatsonAgent] offer_deduction_hint clues={len(clues)} inferences={len(inferences)}")

        settings = get_settings()
        if not settings.openai_api_key:
            return "老朋友，也许那几条线索之间有某种时间上的关联值得深究。"

        clues_block = "\n".join([f"  - id={c.id} {c.user_label or c.description[:40]}" for c in clues]) or "（无）"
        inferences_block = "\n".join([f"  - {inf.content[:60]}" for inf in inferences]) or "（无）"

        chain = watson_deduction_hint_prompt | self.llm
        result = await invoke_with_retry(
            chain=chain,
            inputs={"clues_block": clues_block, "inferences_block": inferences_block},
            fallback_fn=lambda: type("R", (), {"content": "老朋友，也许有几条线索之间的关联还未被发现。"})(),
        )
        return result.content if hasattr(result, "content") else str(result)

    async def detect_contradictions(
        self,
        case: Case,
        conversation_history: List[Dict[str, str]],
        suspect_statements: Dict[str, List[str]],
    ) -> List[Dict[str, Any]]:
        """
        基于 LLM 检测嫌疑人陈述中的矛盾（替代旧关键词启发式）。

        Args:
            case: 当前案件（用于获取线索列表）
            conversation_history: 整体对话历史（备用上下文）
            suspect_statements: {suspect_id: [statement1, statement2, ...]}
        Returns:
            contradictions 数组，每项含 type / topic / suspect_1 / suspect_2 / description / confidence
        """
        logger.info(f"[WatsonAgent] detect_contradictions suspects={len(suspect_statements)}")

        if not suspect_statements or len(suspect_statements) < 2:
            logger.debug("[WatsonAgent] detect_contradictions 嫌疑人不足 2 人，跳过")
            return []

        fallback: List[Dict[str, Any]] = []

        settings = get_settings()
        if not settings.openai_api_key:
            return fallback

        clues_block = "\n".join(
            [f"  - {c.description[:50]}" for c in case.clues if not c.is_red_herring]
        ) or "（无）"

        # 构建嫌疑人陈述 block，附上 name 便于 LLM 引用
        suspect_name_map = {s.id: s.name for s in case.suspects}
        statements_lines = []
        for sid, stmts in suspect_statements.items():
            name = suspect_name_map.get(sid, sid)
            for stmt in stmts[:3]:  # 每人最多 3 条，避免 token 过多
                statements_lines.append(f"  [{sid}] {name}: {stmt[:80]}")
        statements_block = "\n".join(statements_lines) or "（无）"

        from langchain_core.output_parsers import StrOutputParser
        chain = watson_contradiction_prompt | self.llm | StrOutputParser()
        result = await invoke_with_retry(
            chain=chain,
            inputs={"clues_block": clues_block, "statements_block": statements_block},
            fallback_fn=lambda: '{"contradictions": []}',
            parse_json=True,
        )
        if isinstance(result, dict) and "contradictions" in result:
            contras = result["contradictions"]
            logger.info(f"[WatsonAgent] detect_contradictions 完成 count={len(contras)}")
            return contras
        return fallback


# 全局华生Agent实例
_watson_agent: Optional[WatsonAgent] = None


def get_watson_agent() -> WatsonAgent:
    """获取华生Agent单例"""
    global _watson_agent
    if _watson_agent is None:
        _watson_agent = WatsonAgent()
    return _watson_agent
