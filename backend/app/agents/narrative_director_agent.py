"""
叙事导演 Agent（Narrative Director Agent）

核心职责：
1. 每次嫌疑人对话后，通过 LLM 提取压力信号（evasion, contradiction 等）
2. 确定性累积压力值（加权求和 + 衰减）
3. 检查故事节拍（Story Beat）触发条件
4. 评估嫌疑人状态转换（calm → pressured → broken）
5. 生成前端可渲染的叙事事件列表

设计原则：
- LLM 调用失败时优雅降级，不阻塞游戏流程
- 压力计算确定性部分不依赖 LLM（信号权重、阈值、衰减均为配置项）
- 单例模式，全局共享
"""
import asyncio
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from loguru import logger
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.models.case import (
    Suspect,
    Case,
    PressureSignal,
    PressureSignalType,
    StoryBeat,
    StoryBeatTrigger,
    NarrativeState,
    NarrativeEvent,
    NarrativeDirectorResult,
)
from app.agents.prompts.narrative_director_prompts import narrative_director_pressure_prompt
from app.agents._llm_helpers import invoke_with_retry, truncate_messages_by_token, estimate_token_count


class NarrativeDirectorAgent:
    """叙事导演 Agent"""

    # 压力信号类型 → 配置 key 后缀映射
    _SIGNAL_WEIGHT_MAP = {
        PressureSignalType.EVASION: "pressure_signal_weight_evasion",
        PressureSignalType.CONTRADICTION: "pressure_signal_weight_contradiction",
        PressureSignalType.OVER_EXPLANATION: "pressure_signal_weight_over_explanation",
        PressureSignalType.EMOTIONAL_LEAKAGE: "pressure_signal_weight_emotional_leakage",
        PressureSignalType.INCONSISTENCY: "pressure_signal_weight_inconsistency",
        PressureSignalType.DEFLECTION: "pressure_signal_weight_deflection",
    }

    def __init__(self):
        """初始化叙事导演 Agent"""
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=settings.narrative_director_temperature,
            extra_body={"enable_thinking": False},
        )
        logger.info(
            f"[NarrativeDirector] 初始化叙事导演 Agent "
            f"(model={settings.openai_model}, temperature={settings.narrative_director_temperature})"
        )

    # ── 主入口 ─────────────────────────────────────────────

    async def analyze_conversation_turn(
        self,
        suspect: Suspect,
        case: Case,
        user_question: str,
        suspect_response: str,
        recent_history: List[Dict[str, str]],
        narrative_state: NarrativeState,
        pending_beats: List[StoryBeat],
        suspect_state: str = "calm",
        discovered_clue_ids: Optional[List[str]] = None,
    ) -> NarrativeDirectorResult:
        """
        分析一轮对话，返回完整的 NarrativeDirectorResult。

        编排顺序：
        1. 提取压力信号（LLM）
        2. 累积压力（确定性）
        3. 检查故事节拍（确定性）
        4. 评估状态转换（确定性）
        5. 生成叙事事件（确定性）
        6. LLM 失败时返回空结果
        """
        turn_start = time.perf_counter()
        logger.info(
            f"[NarrativeDirector] 开始分析对话轮次: suspect={suspect.id}, "
            f"question={user_question[:40]}..., response={suspect_response[:40]}..."
        )

        try:
            # Step 1: Extract pressure signals (LLM)
            signals = await self._extract_pressure_signals(
                suspect=suspect,
                current_pressure=narrative_state.pressure,
                recent_history=recent_history,
                user_question=user_question,
                suspect_response=suspect_response,
            )
            logger.info(
                f"[NarrativeDirector] 压力信号提取完成: {len(signals)} 个信号 "
                f"({[s.signal_type.value for s in signals]})"
            )

            # Step 2: Accumulate pressure (deterministic)
            pressure_delta, new_pressure = self._accumulate_pressure(
                signals=signals,
                current_pressure=narrative_state.pressure,
            )
            logger.info(
                f"[NarrativeDirector] 压力累积: {narrative_state.pressure:.3f} "
                f"+ {pressure_delta:+.3f} = {new_pressure:.3f}"
            )

            # Step 3: Check story beats (deterministic)
            triggered_beats = self._check_story_beats(
                pending_beats=pending_beats,
                narrative_state=narrative_state,
                suspect_state=suspect_state,
                discovered_clue_ids=discovered_clue_ids or [],
                new_pressure=new_pressure,
            )
            if triggered_beats:
                logger.info(
                    f"[NarrativeDirector] 触发故事节拍: "
                    f"{[b.id for b in triggered_beats]}"
                )

            # Step 4: Evaluate state transition (deterministic)
            state_transition = self._evaluate_state_transition(
                new_pressure=new_pressure,
                current_suspect_state=suspect_state,
            )
            if state_transition:
                logger.info(
                    f"[NarrativeDirector] 状态转换: "
                    f"{state_transition['from']} → {state_transition['to']}"
                )

            # Step 5: Generate narrative events (deterministic)
            narrative_events = self._generate_narrative_events(
                signals=signals,
                triggered_beats=triggered_beats,
                state_transition=state_transition,
            )

            elapsed = time.perf_counter() - turn_start
            logger.info(
                f"[NarrativeDirector] 对话轮次分析完成 "
                f"(elapsed={elapsed:.2f}s, signals={len(signals)}, "
                f"pressure={new_pressure:.3f}, events={len(narrative_events)})"
            )

            return NarrativeDirectorResult(
                suspect_id=suspect.id,
                pressure_delta=pressure_delta,
                new_pressure=new_pressure,
                pressure_signals_detected=signals,
                triggered_beats=triggered_beats,
                state_transition=state_transition,
                narrative_events=narrative_events,
            )

        except Exception as e:
            elapsed = time.perf_counter() - turn_start
            logger.error(
                f"[NarrativeDirector] 对话轮次分析失败 "
                f"(elapsed={elapsed:.2f}s, err={e})",
                exc_info=True,
            )
            # Step 6: Graceful fallback — return empty result
            return NarrativeDirectorResult(
                suspect_id=suspect.id,
                pressure_delta=0.0,
                new_pressure=narrative_state.pressure,
                pressure_signals_detected=[],
                triggered_beats=[],
                state_transition=None,
                narrative_events=[],
            )

    # ── Step 1: 压力信号提取（LLM）─────────────────────────

    async def _extract_pressure_signals(
        self,
        suspect: Suspect,
        current_pressure: float,
        recent_history: List[Dict[str, str]],
        user_question: str,
        suspect_response: str,
    ) -> List[PressureSignal]:
        """
        调用 LLM 从嫌疑人回答中提取压力信号。

        Args:
            suspect: 嫌疑人模型
            current_pressure: 当前累积压力值
            recent_history: 近期对话历史
            user_question: 侦探提问
            suspect_response: 嫌疑人回答

        Returns:
            检测到的压力信号列表
        """
        settings = get_settings()

        # Token 预算管理：截断对话历史
        history_for_prompt = recent_history or []
        if history_for_prompt:
            max_tokens = settings.narrative_director_max_history_tokens
            history_tokens = sum(
                estimate_token_count(msg.get("content", ""), model=settings.openai_model)
                for msg in history_for_prompt
            )
            if history_tokens > max_tokens:
                history_for_prompt = truncate_messages_by_token(
                    history_for_prompt,
                    max_tokens=max_tokens,
                    model=settings.openai_model,
                )
                logger.info(
                    f"[NarrativeDirector] 历史消息截断: "
                    f"{len(recent_history)} → {len(history_for_prompt)}"
                )

        # 格式化对话历史为可读文本
        recent_history_text = self._format_history_for_prompt(history_for_prompt)

        chain = narrative_director_pressure_prompt | self.llm

        result = await invoke_with_retry(
            chain=chain,
            inputs={
                "suspect_name": suspect.name,
                "background": suspect.background,
                "personality_traits": "、".join(suspect.personality_traits),
                "is_guilty": "是" if suspect.is_guilty else "否",
                "current_pressure": f"{current_pressure:.2f}",
                "recent_history": recent_history_text,
                "user_question": user_question,
                "suspect_response": suspect_response,
            },
            fallback_fn=lambda: {"signals": []},
            parse_json=True,
        )

        if not isinstance(result, dict):
            logger.warning(f"[NarrativeDirector] LLM 返回非 dict 类型: {type(result)}")
            return []

        raw_signals = result.get("signals", [])
        if not isinstance(raw_signals, list):
            logger.warning(f"[NarrativeDirector] signals 字段非 list 类型")
            return []

        # 解析并校验每个信号
        parsed_signals: List[PressureSignal] = []
        for raw in raw_signals:
            try:
                signal_type_str = raw.get("signal_type", "")
                # 校验 signal_type
                try:
                    signal_type = PressureSignalType(signal_type_str)
                except ValueError:
                    logger.warning(
                        f"[NarrativeDirector] 未知压力信号类型: {signal_type_str}"
                    )
                    continue

                confidence = float(raw.get("confidence", 0.0))
                # 过滤低置信度信号
                if confidence < 0.3:
                    continue
                # Clamp to [0.0, 1.0]
                confidence = max(0.0, min(1.0, confidence))

                description = str(raw.get("description", ""))
                if not description:
                    continue

                signal = PressureSignal(
                    suspect_id=suspect.id,
                    signal_type=signal_type,
                    confidence=confidence,
                    description=description,
                    source_question_snippet=user_question[:100],
                    source_response_snippet=suspect_response[:100],
                )
                parsed_signals.append(signal)

            except (ValueError, TypeError) as e:
                logger.warning(
                    f"[NarrativeDirector] 解析压力信号失败: {raw}, err={e}"
                )
                continue

        return parsed_signals

    # ── Step 2: 压力累积（确定性）──────────────────────────

    def _accumulate_pressure(
        self,
        signals: List[PressureSignal],
        current_pressure: float,
    ) -> tuple[float, float]:
        """
        根据检测到的信号累积压力。

        公式：new_pressure = current_pressure + Σ (confidence × weight) - decay
        结果 clamp 到 [0.0, 1.0]。

        Args:
            signals: 本轮检测到的压力信号
            current_pressure: 当前累积压力值

        Returns:
            (pressure_delta, new_pressure) 元组
        """
        settings = get_settings()

        if not signals:
            # 无信号时应用衰减
            decay = settings.pressure_decay_per_turn
            new_pressure = max(0.0, current_pressure - decay)
            delta = new_pressure - current_pressure
            return (delta, new_pressure)

        # 加权求和
        total_delta = 0.0
        for signal in signals:
            weight_key = self._SIGNAL_WEIGHT_MAP.get(signal.signal_type)
            if weight_key is None:
                logger.warning(
                    f"[NarrativeDirector] 未找到信号权重配置: {signal.signal_type}"
                )
                continue
            weight = getattr(settings, weight_key, 0.0)
            contribution = signal.confidence * weight
            logger.debug(
                f"[NarrativeDirector] 压力信号: type={signal.signal_type.value}, "
                f"confidence={signal.confidence:.2f}, weight={weight:.2f}, "
                f"contribution={contribution:+.3f}"
            )
            total_delta += contribution

        new_pressure = current_pressure + total_delta

        # 应用衰减（有信号时也可以有轻微衰减，由配置决定）
        if settings.pressure_decay_per_turn > 0 and not signals:
            new_pressure -= settings.pressure_decay_per_turn

        # Clamp to [0.0, 1.0]
        new_pressure = max(0.0, min(1.0, new_pressure))
        delta = new_pressure - current_pressure

        return (delta, new_pressure)

    # ── Step 3: 故事节拍检测（确定性）──────────────────────

    def _check_story_beats(
        self,
        pending_beats: List[StoryBeat],
        narrative_state: NarrativeState,
        suspect_state: str,
        discovered_clue_ids: List[str],
        new_pressure: float,
    ) -> List[StoryBeat]:
        """
        检查待触发故事节拍的触发条件，返回满足条件的最多 1 个节拍。

        条件检查（全部满足才触发）：
        - min_pressure: 当前压力 >= 最低要求
        - min_state: 当前嫌疑人状态满足（None = 不限制）
        - required_clue_ids: 所有必需线索已发现
        - required_topics: 所有必需话题已讨论
        - min_contradiction_count: 已检测矛盾数 >= 最低要求
        - requires_any_signal_of: 历史中至少出现过指定信号类型之一

        多条符合时，按 priority 降序选择最高优先级的 1 条。

        Args:
            pending_beats: 待触发的故事节拍
            narrative_state: 当前叙事状态
            suspect_state: 当前嫌疑人状态（calm/pressured/broken）
            discovered_clue_ids: 已发现的线索 ID 列表
            new_pressure: 本轮更新后的压力值

        Returns:
            触发的故事节拍列表（最多 1 个）
        """
        settings = get_settings()
        if not settings.enable_story_beats:
            return []

        qualified: List[StoryBeat] = []

        for beat in pending_beats:
            if beat.triggered:
                continue

            trigger = beat.trigger

            # 检查压力阈值
            if new_pressure < trigger.min_pressure:
                continue

            # 检查状态阈值 (at-or-above: broken > pressured > calm)
            if trigger.min_state is not None:
                state_rank = {"calm": 0, "pressured": 1, "broken": 2}
                if state_rank.get(suspect_state, 0) < state_rank.get(trigger.min_state, 0):
                    continue

            # 检查必需线索
            if trigger.required_clue_ids:
                if not all(
                    clue_id in discovered_clue_ids
                    for clue_id in trigger.required_clue_ids
                ):
                    continue

            # 检查必需话题
            if trigger.required_topics:
                if not all(
                    topic in narrative_state.topics_discussed
                    for topic in trigger.required_topics
                ):
                    continue

            # 检查矛盾计数
            if narrative_state.contradictions_detected < trigger.min_contradiction_count:
                continue

            # 检查信号类型要求
            if trigger.requires_any_signal_of:
                historical_signal_types = {
                    ps.signal_type for ps in narrative_state.pressure_signals
                }
                if not any(
                    req_type in historical_signal_types
                    for req_type in trigger.requires_any_signal_of
                ):
                    continue

            qualified.append(beat)

        if not qualified:
            return []

        # 按 priority 降序排序，取最高优先级的 1 条
        qualified.sort(key=lambda b: b.priority, reverse=True)
        selected = qualified[0]
        logger.info(
            f"[NarrativeDirector] 选择故事节拍: {selected.id} "
            f"(priority={selected.priority}, title={selected.title})"
        )

        return [selected]

    # ── Step 4: 状态转换评估（确定性）───────────────────────

    def _evaluate_state_transition(
        self,
        new_pressure: float,
        current_suspect_state: str,
    ) -> Optional[Dict[str, str]]:
        """
        根据压力值判断嫌疑人状态是否应转换。

        规则：
        - pressure >= 0.75 → 转换为 broken
        - pressure >= 0.40 且当前为 calm → 转换为 pressured
        - broken 是终止态，不可逆
        - 同状态不返回转换

        Args:
            new_pressure: 更新后的压力值
            current_suspect_state: 当前嫌疑人状态

        Returns:
            {"from": "calm", "to": "pressured"} 或 None（无转换）
        """
        settings = get_settings()

        # broken 是终止态
        if current_suspect_state == "broken":
            return None

        if new_pressure >= settings.pressure_threshold_broken:
            return {"from": current_suspect_state, "to": "broken"}

        if (
            new_pressure >= settings.pressure_threshold_pressured
            and current_suspect_state == "calm"
        ):
            return {"from": "calm", "to": "pressured"}

        return None

    # ── Step 5: 叙事事件生成（确定性）───────────────────────

    def _generate_narrative_events(
        self,
        signals: List[PressureSignal],
        triggered_beats: List[StoryBeat],
        state_transition: Optional[Dict[str, str]],
    ) -> List[NarrativeEvent]:
        """
        构建前端可渲染的叙事事件列表。

        Args:
            signals: 本轮检测到的压力信号
            triggered_beats: 触发的故事节拍
            state_transition: 状态转换信息

        Returns:
            NarrativeEvent 列表
        """
        events: List[NarrativeEvent] = []

        # 压力信号事件（仅高置信度信号生成事件）
        for signal in signals:
            if signal.confidence >= 0.6:
                events.append(
                    NarrativeEvent(
                        type="pressure_warning",
                        message=f"检测到压力信号：{signal.description}",
                        data={
                            "signal_type": signal.signal_type.value,
                            "confidence": signal.confidence,
                            "suspect_id": signal.suspect_id,
                        },
                    )
                )

        # 故事节拍事件
        for beat in triggered_beats:
            events.append(
                NarrativeEvent(
                    type="beat_triggered",
                    message=f"叙事推进：{beat.title} — {beat.description}",
                    data={
                        "beat_id": beat.id,
                        "title": beat.title,
                        "effects": beat.effects.model_dump() if beat.effects else None,
                    },
                )
            )

            # 节拍可能附带揭秘
            if beat.effects and beat.effects.new_revelation:
                events.append(
                    NarrativeEvent(
                        type="revelation",
                        message=beat.effects.new_revelation,
                        data={"beat_id": beat.id},
                    )
                )

            # 节拍可能附带华生评论
            if beat.effects and beat.effects.watson_comment:
                events.append(
                    NarrativeEvent(
                        type="watson_interjection",
                        message=beat.effects.watson_comment,
                        data={"beat_id": beat.id},
                    )
                )

        # 状态转换事件
        if state_transition:
            from_state = state_transition["from"]
            to_state = state_transition["to"]

            if to_state == "broken":
                message = "嫌疑人心理防线崩溃，情绪极度不稳。"
            elif to_state == "pressured":
                message = "嫌疑人开始感受到明显压力，回答中透露出紧张迹象。"
            else:
                message = f"嫌疑人状态变化：{from_state} → {to_state}"

            events.append(
                NarrativeEvent(
                    type="state_change",
                    message=message,
                    data={
                        "from": from_state,
                        "to": to_state,
                    },
                )
            )

        return events

    # ── 辅助方法 ───────────────────────────────────────────

    @staticmethod
    def _format_history_for_prompt(history: List[Dict[str, str]]) -> str:
        """
        将对话历史格式化为可读文本供 prompt 使用。

        Args:
            history: 对话历史列表

        Returns:
            格式化后的文本
        """
        if not history:
            return "（尚无对话历史）"

        lines: List[str] = []
        for i, msg in enumerate(history):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            # 截断过长的消息
            if len(content) > 200:
                content = content[:200] + "……（截断）"
            if role == "user":
                lines.append(f"[侦探] {content}")
            elif role == "assistant":
                lines.append(f"[嫌疑人] {content}")
            else:
                lines.append(f"[{role}] {content}")

        return "\n".join(lines)


# ── 单例 ─────────────────────────────────────────────────

_narrative_director: Optional[NarrativeDirectorAgent] = None


def get_narrative_director() -> NarrativeDirectorAgent:
    """获取叙事导演 Agent 单例"""
    global _narrative_director
    if _narrative_director is None:
        _narrative_director = NarrativeDirectorAgent()
    return _narrative_director
