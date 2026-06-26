"""
Narrative Director 叙事导演系统单元测试

测试范围:
1. _accumulate_pressure()   — 确定性压力累积
2. _check_story_beats()     — 故事节拍触发检测
3. _evaluate_state_transition() — 状态转换评估
4. _generate_narrative_events() — 叙事事件生成
5. GameService 叙事方法
6. 向后兼容性
7. 集成测试 (mock LLM)
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from app.agents.narrative_director_agent import NarrativeDirectorAgent
from app.models.case import (
    Suspect, Case, PressureSignal, PressureSignalType,
    StoryBeat, StoryBeatTrigger, StoryBeatEffects,
    NarrativeState, NarrativeEvent, NarrativeDirectorResult,
)
from app.services.game_service import GameService
from app.models.game import GameDifficulty, GameState
from app.config import Settings


# ─────────────────────────────────────────────────────────
# 模块级夹具 — 可复用测试数据
# ─────────────────────────────────────────────────────────

@pytest.fixture
def test_settings() -> Settings:
    """可控的测试用配置对象，所有权重/阈值均为已知值。"""
    return Settings(
        enable_narrative_director=True,
        enable_pressure_accumulation=True,
        enable_story_beats=True,
        pressure_signal_weight_evasion=0.15,
        pressure_signal_weight_contradiction=0.30,
        pressure_signal_weight_over_explanation=0.10,
        pressure_signal_weight_emotional_leakage=0.20,
        pressure_signal_weight_inconsistency=0.25,
        pressure_signal_weight_deflection=0.10,
        pressure_decay_per_turn=0.0,
        pressure_threshold_pressured=0.40,
        pressure_threshold_broken=0.75,
        narrative_director_max_history_tokens=4000,
        narrative_director_temperature=0.3,
    )


def _make_agent(settings: Settings) -> NarrativeDirectorAgent:
    """在隔离的配置环境中创建 NarrativeDirectorAgent。

    ChatOpenAI 被 mock 掉以避免真实 API 调用；get_settings 返回
    指定的 settings 对象，确保所有确定性方法使用可控配置。
    """
    with patch(
        "app.agents.narrative_director_agent.get_settings", return_value=settings
    ):
        with patch("app.agents.narrative_director_agent.ChatOpenAI"):
            return NarrativeDirectorAgent()


@pytest.fixture
def agent(test_settings: Settings) -> NarrativeDirectorAgent:
    """每个测试提供一个在隔离 setting 下初始化的 agent。"""
    return _make_agent(test_settings)


@pytest.fixture
def sample_suspect() -> Suspect:
    return Suspect(
        id="suspect-1",
        name="哈罗德·史密斯",
        age=42,
        relationship_to_victim="商业伙伴",
        background="伦敦商人，与被害人有长期生意往来",
        motive="商业纠纷与债务",
        timeline="案发当晚声称在俱乐部",
        is_guilty=True,
        personality_traits=["精明", "易怒", "善于言辞"],
        secrets=["伪造了账本", "案发当晚实际去过被害人住宅"],
    )


@pytest.fixture
def sample_case(sample_suspect: Suspect) -> Case:
    return Case(
        id="case-test-1",
        victim_name="爱德华·布莱克",
        victim_background="富有的投资家",
        cause_of_death="中毒",
        time_of_death="晚上10点左右",
        location="布莱克庄园书房",
        date=datetime(1895, 10, 15, 22, 0),
        suspects=[sample_suspect],
        clues=[],
        summary="爱德华·布莱克被发现死于自己书房，初步判断为中毒。",
        murder_method="毒药",
        true_murderer_id="suspect-1",
        scenes=[],
        witnesses=[],
        experts=[],
    )


def _make_beat(
    beat_id: str,
    suspect_id: str = "suspect-1",
    title: str = "",
    description: str = "",
    min_pressure: float = 0.0,
    min_state: str | None = None,
    required_clue_ids: list | None = None,
    required_topics: list | None = None,
    min_contradiction_count: int = 0,
    requires_any_signal_of: list | None = None,
    new_revelation: str | None = None,
    watson_comment: str | None = None,
    priority: int = 1,
    triggered: bool = False,
) -> StoryBeat:
    """快捷构造 StoryBeat，避免样板代码。"""
    return StoryBeat(
        id=beat_id,
        suspect_id=suspect_id,
        title=title or beat_id,
        description=description or f"Description for {beat_id}",
        trigger=StoryBeatTrigger(
            min_pressure=min_pressure,
            min_state=min_state,
            required_clue_ids=required_clue_ids or [],
            required_topics=required_topics or [],
            min_contradiction_count=min_contradiction_count,
            requires_any_signal_of=requires_any_signal_of or [],
        ),
        effects=StoryBeatEffects(
            new_revelation=new_revelation,
            watson_comment=watson_comment,
        ),
        priority=priority,
        triggered=triggered,
    )


# ─────────────────────────────────────────────────────────
# 1. _accumulate_pressure 测试
# ─────────────────────────────────────────────────────────

class TestAccumulatePressure:
    """测试 _accumulate_pressure 确定性压力累积。"""

    def test_zero_signals_pressure_unchanged(self, agent):
        """无信号且衰减=0 → 压力不变。"""
        delta, new_pressure = agent._accumulate_pressure(
            signals=[],
            current_pressure=0.30,
        )
        assert delta == 0.0
        assert new_pressure == 0.30

    def test_single_evasion_signal(self, agent):
        """1 个 evasion, confidence=0.7 → 贡献 0.7 * 0.15 = 0.105。"""
        signal = PressureSignal(
            suspect_id="suspect-1",
            signal_type=PressureSignalType.EVASION,
            confidence=0.7,
            description="嫌疑人回避了关键问题",
        )
        delta, new_pressure = agent._accumulate_pressure(
            signals=[signal],
            current_pressure=0.0,
        )
        assert delta == pytest.approx(0.105)
        assert new_pressure == pytest.approx(0.105)

    def test_single_contradiction_signal(self, agent):
        """contradiction 权重=0.30, confidence=0.60 → 贡献 0.18。"""
        signal = PressureSignal(
            suspect_id="suspect-1",
            signal_type=PressureSignalType.CONTRADICTION,
            confidence=0.60,
            description="陈述前后矛盾",
        )
        delta, new_pressure = agent._accumulate_pressure(
            signals=[signal],
            current_pressure=0.10,
        )
        assert delta == pytest.approx(0.18)
        assert new_pressure == pytest.approx(0.28)

    def test_multiple_signals_weighted_sum(self, agent):
        """多信号 → evasion*0.15 + contradiction*0.30 + inconsistency*0.25。"""
        signals = [
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.EVASION,
                confidence=0.50,
                description="回避",
            ),
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.CONTRADICTION,
                confidence=0.60,
                description="矛盾",
            ),
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.INCONSISTENCY,
                confidence=0.80,
                description="不一致",
            ),
        ]
        # 0.50*0.15 + 0.60*0.30 + 0.80*0.25 = 0.075 + 0.180 + 0.200 = 0.455
        delta, new_pressure = agent._accumulate_pressure(
            signals=signals,
            current_pressure=0.05,
        )
        assert delta == pytest.approx(0.455)
        assert new_pressure == pytest.approx(0.505)

    def test_all_signal_types(self, agent, test_settings):
        """覆盖全部 6 种信号类型，验证权重映射正确。"""
        # 动态构造 agent 以确保最新 settings
        agent2 = _make_agent(test_settings)
        signals = [
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.EVASION,
                confidence=1.0,
                description="e",
            ),
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.CONTRADICTION,
                confidence=1.0,
                description="c",
            ),
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.OVER_EXPLANATION,
                confidence=1.0,
                description="o",
            ),
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.EMOTIONAL_LEAKAGE,
                confidence=1.0,
                description="el",
            ),
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.INCONSISTENCY,
                confidence=1.0,
                description="i",
            ),
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.DEFLECTION,
                confidence=1.0,
                description="d",
            ),
        ]
        delta, new = agent2._accumulate_pressure(signals, 0.0)
        # 0.15 + 0.30 + 0.10 + 0.20 + 0.25 + 0.10 = 1.10 → clamped to 1.0
        assert new == 1.0
        assert delta == pytest.approx(1.0)

    def test_clamps_at_maximum_1_0(self, agent):
        """压力不可超过 1.0。"""
        signal = PressureSignal(
            suspect_id="suspect-1",
            signal_type=PressureSignalType.CONTRADICTION,
            confidence=1.0,
            description="重大矛盾",
        )
        delta, new_pressure = agent._accumulate_pressure(
            signals=[signal],
            current_pressure=0.95,
        )
        # 0.95 + 0.30 = 1.25 → clamp to 1.0
        assert new_pressure == 1.0
        assert delta == pytest.approx(0.05)

    def test_clamps_exactly_at_one(self, agent):
        """恰好到达 1.0 不被截断。"""
        signal = PressureSignal(
            suspect_id="suspect-1",
            signal_type=PressureSignalType.CONTRADICTION,
            confidence=1.0,
            description="重大矛盾",
        )
        delta, new_pressure = agent._accumulate_pressure(
            signals=[signal],
            current_pressure=0.70,
        )
        assert new_pressure == 1.0
        assert delta == pytest.approx(0.30)

    def test_stays_at_zero_with_decay(self, test_settings):
        """压力不可低于 0.0 — 衰减后 clamping。"""
        test_settings.pressure_decay_per_turn = 0.05
        agent2 = _make_agent(test_settings)

        # 无信号时应用衰减: 0.02 - 0.05 = -0.03 → clamp to 0.0
        with patch(
            "app.agents.narrative_director_agent.get_settings",
            return_value=test_settings,
        ):
            delta, new_pressure = agent2._accumulate_pressure(
                signals=[],
                current_pressure=0.02,
            )
        assert new_pressure == 0.0
        # delta = 0.0 - 0.02 = -0.02
        assert delta == pytest.approx(-0.02)

    def test_delta_equals_new_minus_old(self, agent):
        """delta 始终等于 new_pressure - current_pressure。"""
        signal = PressureSignal(
            suspect_id="suspect-1",
            signal_type=PressureSignalType.EVASION,
            confidence=0.40,
            description="回避",
        )
        current = 0.33
        delta, new_pressure = agent._accumulate_pressure(
            signals=[signal],
            current_pressure=current,
        )
        assert delta == pytest.approx(new_pressure - current)


# ─────────────────────────────────────────────────────────
# 2. _check_story_beats 测试
# ─────────────────────────────────────────────────────────

class TestCheckStoryBeats:
    """测试 _check_story_beats 故事节拍触发检测。"""

    def test_empty_pending_beats_returns_empty(self, agent):
        result = agent._check_story_beats(
            pending_beats=[],
            narrative_state=NarrativeState(suspect_id="suspect-1"),
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.5,
        )
        assert result == []

    def test_below_pressure_threshold_not_triggered(self, agent):
        """节拍要求 min_pressure=0.30, 当前=0.10 → 不触发。"""
        beat = _make_beat("beat-low", min_pressure=0.30)
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(suspect_id="suspect-1"),
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.10,
        )
        assert result == []

    def test_meets_all_conditions_beat_fires(self, agent):
        """所有条件满足 → 触发。"""
        beat = _make_beat("beat-ok", min_pressure=0.20)
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(suspect_id="suspect-1"),
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.35,
        )
        assert len(result) == 1
        assert result[0].id == "beat-ok"

    def test_missing_required_clue_not_triggered(self, agent):
        """required_clue_ids 中有未发现的线索 → 不触发。"""
        beat = _make_beat(
            "beat-clue",
            min_pressure=0.20,
            required_clue_ids=["clue-missing"],
        )
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(suspect_id="suspect-1"),
            suspect_state="calm",
            discovered_clue_ids=["clue-other"],  # missing not found
            new_pressure=0.50,
        )
        assert result == []

    def test_required_clue_found_triggers(self, agent):
        """所有 required_clue_ids 都发现 → 触发。"""
        beat = _make_beat(
            "beat-clue-ok",
            min_pressure=0.10,
            required_clue_ids=["clue-a", "clue-b"],
        )
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(suspect_id="suspect-1"),
            suspect_state="calm",
            discovered_clue_ids=["clue-x", "clue-a", "clue-b"],
            new_pressure=0.30,
        )
        assert len(result) == 1
        assert result[0].id == "beat-clue-ok"

    def test_multiple_qualified_returns_highest_priority(self, agent):
        """多条合格 → 只返回 priority 最高的 1 条。"""
        b1 = _make_beat("b1", min_pressure=0.20, priority=1)
        b2 = _make_beat("b2", min_pressure=0.20, priority=10)
        b3 = _make_beat("b3", min_pressure=0.20, priority=5)
        result = agent._check_story_beats(
            pending_beats=[b1, b2, b3],
            narrative_state=NarrativeState(suspect_id="suspect-1"),
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.50,
        )
        assert len(result) == 1
        assert result[0].id == "b2"
        assert result[0].priority == 10

    def test_already_triggered_beat_skipped(self, agent):
        """triggered=True 的节拍直接跳过。"""
        beat = _make_beat("beat-ignored", min_pressure=0.10, triggered=True)
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(suspect_id="suspect-1"),
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.50,
        )
        assert result == []

    def test_requires_signal_type_met_in_history(self, agent):
        """历史信号中存在 required 类型 → 触发。"""
        beat = _make_beat(
            "beat-signal",
            min_pressure=0.20,
            requires_any_signal_of=[PressureSignalType.EVASION],
        )
        state = NarrativeState(
            suspect_id="suspect-1",
            pressure_signals=[
                PressureSignal(
                    suspect_id="suspect-1",
                    signal_type=PressureSignalType.EVASION,
                    confidence=0.60,
                    description="之前检测到回避",
                ),
            ],
        )
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=state,
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.30,
        )
        assert len(result) == 1
        assert result[0].id == "beat-signal"

    def test_requires_signal_type_not_met(self, agent):
        """历史信号中无 required 类型 → 不触发。"""
        beat = _make_beat(
            "beat-no-signal",
            min_pressure=0.20,
            requires_any_signal_of=[PressureSignalType.DEFLECTION],
        )
        state = NarrativeState(
            suspect_id="suspect-1",
            pressure_signals=[
                PressureSignal(
                    suspect_id="suspect-1",
                    signal_type=PressureSignalType.EVASION,
                    confidence=0.60,
                    description="只有 evasion",
                ),
            ],
        )
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=state,
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.30,
        )
        assert result == []

    def test_state_requirement_not_met(self, agent):
        """当前状态低于 min_state 要求 → 不触发。"""
        beat = _make_beat(
            "beat-state",
            min_pressure=0.30,
            min_state="pressured",
        )
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(suspect_id="suspect-1"),
            suspect_state="calm",  # calm < pressured
            discovered_clue_ids=[],
            new_pressure=0.50,
        )
        assert result == []

    def test_state_requirement_broken_above_pressured(self, agent):
        """broken 状态 >= broken min_state → 触发。"""
        # broken 状态下的节拍要求 min_state="broken"，当前 relaxed 但仍满足
        beat = _make_beat(
            "beat-broken-only",
            min_pressure=0.50,
            min_state="pressured",  # broken >= pressured
        )
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(suspect_id="suspect-1"),
            suspect_state="broken",
            discovered_clue_ids=[],
            new_pressure=0.60,
        )
        assert len(result) == 1

    def test_contradiction_count_requirement(self, agent):
        """narrative_state 矛盾数不足 → 不触发。"""
        beat = _make_beat(
            "beat-contra",
            min_pressure=0.10,
            min_contradiction_count=3,
        )
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(
                suspect_id="suspect-1",
                contradictions_detected=1,  # < 3
            ),
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.50,
        )
        assert result == []

    def test_contradiction_count_met(self, agent):
        """narrative_state 矛盾数达到要求 → 触发。"""
        beat = _make_beat(
            "beat-contra-ok",
            min_pressure=0.10,
            min_contradiction_count=2,
        )
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(
                suspect_id="suspect-1",
                contradictions_detected=3,
            ),
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.50,
        )
        assert len(result) == 1

    def test_required_topics_met(self, agent):
        """所有 required_topics 都讨论过 → 触发。"""
        beat = _make_beat(
            "beat-topic",
            min_pressure=0.10,
            required_topics=["alibi", "weapon"],
        )
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(
                suspect_id="suspect-1",
                topics_discussed=["alibi", "weapon", "motive"],
            ),
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.30,
        )
        assert len(result) == 1

    def test_required_topics_partial_not_triggered(self, agent):
        """required_topics 只部分满足 → 不触发。"""
        beat = _make_beat(
            "beat-topic-half",
            min_pressure=0.10,
            required_topics=["alibi", "weapon"],
        )
        result = agent._check_story_beats(
            pending_beats=[beat],
            narrative_state=NarrativeState(
                suspect_id="suspect-1",
                topics_discussed=["alibi"],  # missing "weapon"
            ),
            suspect_state="calm",
            discovered_clue_ids=[],
            new_pressure=0.30,
        )
        assert result == []

    def test_feature_flag_disabled_returns_empty(self, test_settings):
        """enable_story_beats=False → 永远返回空。"""
        test_settings.enable_story_beats = False
        agent2 = _make_agent(test_settings)
        beat = _make_beat("beat-off", min_pressure=0.10)

        with patch(
            "app.agents.narrative_director_agent.get_settings",
            return_value=test_settings,
        ):
            result = agent2._check_story_beats(
                pending_beats=[beat],
                narrative_state=NarrativeState(suspect_id="suspect-1"),
                suspect_state="calm",
                discovered_clue_ids=[],
                new_pressure=0.90,
            )
        assert result == []


# ─────────────────────────────────────────────────────────
# 3. _evaluate_state_transition 测试
# ─────────────────────────────────────────────────────────

class TestEvaluateStateTransition:
    """测试 _evaluate_state_transition 状态转换评估。"""

    def test_calm_to_pressured(self, agent):
        result = agent._evaluate_state_transition(0.45, "calm")
        assert result is not None
        assert result["from"] == "calm"
        assert result["to"] == "pressured"

    def test_calm_to_broken_direct(self, agent):
        """pressure=0.80 >= 0.75 → 直接 broken, 跳过 pressured。"""
        result = agent._evaluate_state_transition(0.80, "calm")
        assert result is not None
        assert result["from"] == "calm"
        assert result["to"] == "broken"

    def test_pressured_to_broken(self, agent):
        result = agent._evaluate_state_transition(0.80, "pressured")
        assert result is not None
        assert result["from"] == "pressured"
        assert result["to"] == "broken"

    def test_broken_terminal(self, agent):
        """broken 终态 → 无论 pressure 多少都返回 None。"""
        assert agent._evaluate_state_transition(0.99, "broken") is None
        assert agent._evaluate_state_transition(0.00, "broken") is None

    def test_below_threshold_stays_calm(self, agent):
        assert agent._evaluate_state_transition(0.20, "calm") is None

    def test_boundary_pressured_exact(self, agent):
        """pressure=0.40 恰好等于阈值 → 触发 pressured。"""
        result = agent._evaluate_state_transition(0.40, "calm")
        assert result is not None
        assert result["to"] == "pressured"

    def test_boundary_broken_exact(self, agent):
        """pressure=0.75 恰好等于阈值 → 触发 broken。"""
        result = agent._evaluate_state_transition(0.75, "pressured")
        assert result is not None
        assert result["to"] == "broken"

    def test_pressured_stays_pressured(self, agent):
        """已经在 pressured, pressure 不够 broken → 不变。"""
        assert agent._evaluate_state_transition(0.50, "pressured") is None

    def test_calm_high_but_below_broken(self, agent):
        """pressure=0.74 (< 0.75), calm → pressured (不是 broken)。"""
        result = agent._evaluate_state_transition(0.74, "calm")
        assert result is not None
        assert result["to"] == "pressured"  # not broken

    def test_custom_thresholds(self, test_settings):
        """验证阈值从配置读取（非硬编码）。"""
        test_settings.pressure_threshold_pressured = 0.50
        test_settings.pressure_threshold_broken = 0.85
        agent2 = _make_agent(test_settings)

        # patch must be active during method calls since get_settings()
        # is called at method time (not just at init)
        with patch(
            "app.agents.narrative_director_agent.get_settings",
            return_value=test_settings,
        ):
            # 0.45 < 0.50 → 不触发
            assert agent2._evaluate_state_transition(0.45, "calm") is None
            # 0.55 >= 0.50 → pressured
            result = agent2._evaluate_state_transition(0.55, "calm")
            assert result is not None and result["to"] == "pressured"
            # 0.90 >= 0.85 → broken
            result = agent2._evaluate_state_transition(0.90, "calm")
            assert result is not None and result["to"] == "broken"

    def test_zero_pressure(self, agent):
        """pressure=0 → 不转换。"""
        assert agent._evaluate_state_transition(0.0, "calm") is None
        assert agent._evaluate_state_transition(0.0, "pressured") is None
        assert agent._evaluate_state_transition(0.0, "broken") is None


# ─────────────────────────────────────────────────────────
# 4. _generate_narrative_events 测试
# ─────────────────────────────────────────────────────────

class TestGenerateNarrativeEvents:
    """测试 _generate_narrative_events 叙事事件生成。"""

    def test_empty_inputs_yields_empty(self, agent):
        events = agent._generate_narrative_events([], [], None)
        assert events == []

    def test_low_confidence_signal_no_event(self, agent):
        """confidence < 0.6 不生成事件。"""
        signal = PressureSignal(
            suspect_id="suspect-1",
            signal_type=PressureSignalType.EVASION,
            confidence=0.50,
            description="微弱回避",
        )
        events = agent._generate_narrative_events([signal], [], None)
        assert events == []

    def test_high_confidence_signal_generates_warning(self, agent):
        """confidence >= 0.6 生成 pressure_warning 事件。"""
        signal = PressureSignal(
            suspect_id="suspect-1",
            signal_type=PressureSignalType.CONTRADICTION,
            confidence=0.75,
            description="明显自相矛盾",
        )
        events = agent._generate_narrative_events([signal], [], None)
        assert len(events) == 1
        assert events[0].type == "pressure_warning"
        assert "自相矛盾" in events[0].message
        assert events[0].data["signal_type"] == "contradiction"
        assert events[0].data["confidence"] == 0.75

    def test_beat_without_effects_generates_only_beat_event(self, agent):
        """仅节拍本体事件。"""
        beat = StoryBeat(
            id="beat-bare",
            suspect_id="suspect-1",
            title="简单节拍",
            description="没什么特殊效果",
            trigger=StoryBeatTrigger(),
            effects=StoryBeatEffects(),  # no revelation, no watson
        )
        events = agent._generate_narrative_events([], [beat], None)
        assert len(events) == 1
        assert events[0].type == "beat_triggered"
        assert events[0].data["beat_id"] == "beat-bare"

    def test_beat_with_revelation_and_watson(self, agent):
        """节拍携带 revelation + watson_comment → 3 个事件。"""
        beat = StoryBeat(
            id="beat-rich",
            suspect_id="suspect-1",
            title="丰收节拍",
            description="描述",
            trigger=StoryBeatTrigger(),
            effects=StoryBeatEffects(
                new_revelation="发现了关键线索！",
                watson_comment="福尔摩斯，这是决定性的！",
            ),
        )
        events = agent._generate_narrative_events([], [beat], None)
        assert len(events) == 3
        types = {e.type for e in events}
        assert types == {"beat_triggered", "revelation", "watson_interjection"}

    def test_state_transition_to_pressured(self, agent):
        events = agent._generate_narrative_events(
            [], [],
            {"from": "calm", "to": "pressured"},
        )
        assert len(events) == 1
        e = events[0]
        assert e.type == "state_change"
        assert e.data["from"] == "calm"
        assert e.data["to"] == "pressured"
        assert "压力" in e.message

    def test_state_transition_to_broken(self, agent):
        events = agent._generate_narrative_events(
            [], [],
            {"from": "pressured", "to": "broken"},
        )
        assert len(events) == 1
        e = events[0]
        assert e.type == "state_change"
        assert e.data["to"] == "broken"
        assert "崩溃" in e.message

    def test_combined_signal_beat_and_transition(self, agent):
        """同时有信号、节拍、转换 → 所有事件均生成。"""
        signal = PressureSignal(
            suspect_id="suspect-1",
            signal_type=PressureSignalType.EMOTIONAL_LEAKAGE,
            confidence=0.90,
            description="情绪失控",
        )
        beat = StoryBeat(
            id="beat-combo",
            suspect_id="suspect-1",
            title="组合测试",
            description="组合",
            trigger=StoryBeatTrigger(),
            effects=StoryBeatEffects(watson_comment="注意！"),
        )
        events = agent._generate_narrative_events(
            [signal],
            [beat],
            {"from": "calm", "to": "pressured"},
        )
        # 1 pressure_warning + 1 beat_triggered + 1 watson + 1 state_change = 4
        assert len(events) == 4

    def test_mixed_high_and_low_confidence_signals(self, agent):
        """只高置信度信号生成事件，低置信度被忽略。"""
        signals = [
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.EVASION,
                confidence=0.55,  # < 0.6 → ignored
                description="轻微回避",
            ),
            PressureSignal(
                suspect_id="suspect-1",
                signal_type=PressureSignalType.CONTRADICTION,
                confidence=0.85,  # >= 0.6 → event
                description="严重矛盾",
            ),
        ]
        events = agent._generate_narrative_events(signals, [], None)
        assert len(events) == 1
        assert "矛盾" in events[0].message


# ─────────────────────────────────────────────────────────
# 5. GameService 叙事方法测试
# ─────────────────────────────────────────────────────────

class TestGameServiceNarrativeMethods:
    """测试 GameService 的 P6 叙事相关方法。"""

    @pytest.fixture
    def service(self) -> GameService:
        return GameService()

    @pytest.fixture
    def game_with_case(self, service: GameService, sample_suspect, sample_case):
        game = service.create_game(GameDifficulty.CLASSIC)
        service.set_case(game.game_id, sample_case)
        return game

    # ── init_narrative_state ──────────────────────────────

    def test_init_narrative_state_creates_new(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect = game_with_case.case.suspects[0]
        suspect_id = suspect.id

        state = service.init_narrative_state(game_id, suspect_id)
        assert state["suspect_id"] == suspect_id
        assert state["pressure"] == 0.0
        assert state["pressure_signals"] == []
        assert state["triggered_beat_ids"] == []
        assert state["conversation_turn_count"] == 0
        assert state["pending_beat_ids"] == []

    def test_init_narrative_state_idempotent(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        first = service.init_narrative_state(game_id, suspect_id)
        first["pressure"] = 0.42
        second = service.init_narrative_state(game_id, suspect_id)
        # 第二次调用返回已有状态
        assert second["pressure"] == 0.42

    def test_init_narrative_state_nonexistent_game(self, service):
        with pytest.raises(ValueError, match="游戏不存在"):
            service.init_narrative_state("no-such-game", "suspect-1")

    def test_init_narrative_state_nonexistent_suspect(self, service, game_with_case):
        game_id = game_with_case.game_id
        with pytest.raises(ValueError, match="嫌疑人不存在"):
            service.init_narrative_state(game_id, "no-such-suspect")

    # ── get_narrative_state ───────────────────────────────

    def test_get_narrative_state_returns_state(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id
        service.init_narrative_state(game_id, suspect_id)

        state = service.get_narrative_state(game_id, suspect_id)
        assert state is not None
        assert state["suspect_id"] == suspect_id

    def test_get_narrative_state_missing_suspect(self, service, game_with_case):
        game_id = game_with_case.game_id
        assert service.get_narrative_state(game_id, "absent-suspect") is None

    def test_get_narrative_state_missing_game(self, service):
        assert service.get_narrative_state("no-game", "suspect-1") is None

    # ── update_narrative_state ────────────────────────────

    def test_update_applies_result(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id
        service.init_narrative_state(game_id, suspect_id)

        signal = PressureSignal(
            suspect_id=suspect_id,
            signal_type=PressureSignalType.EVASION,
            confidence=0.80,
            description="回避",
        )
        beat = StoryBeat(
            id="beat-update",
            suspect_id=suspect_id,
            title="测试",
            description="测试节拍",
            trigger=StoryBeatTrigger(min_pressure=0.10),
            effects=StoryBeatEffects(),
            priority=1,
        )
        result = NarrativeDirectorResult(
            suspect_id=suspect_id,
            pressure_delta=0.12,
            new_pressure=0.12,
            pressure_signals_detected=[signal],
            triggered_beats=[beat],
        )
        service.update_narrative_state(game_id, suspect_id, result)

        state = service.get_narrative_state(game_id, suspect_id)
        assert state["pressure"] == 0.12
        assert len(state["pressure_signals"]) == 1
        assert "beat-update" in state["triggered_beat_ids"]
        assert state["conversation_turn_count"] == 1
        assert state["last_analysis_at"] is not None

    def test_update_with_state_transition(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id
        service.init_narrative_state(game_id, suspect_id)

        result = NarrativeDirectorResult(
            suspect_id=suspect_id,
            pressure_delta=0.50,
            new_pressure=0.50,
            pressure_signals_detected=[],
            triggered_beats=[],
            state_transition={"from": "calm", "to": "pressured"},
        )
        service.update_narrative_state(game_id, suspect_id, result)
        assert game_with_case.suspect_states[suspect_id] == "pressured"

    def test_update_no_state_no_crash(self, service, game_with_case):
        """叙事状态不存在时 update 不抛异常。"""
        result = NarrativeDirectorResult(
            suspect_id="nobody",
            pressure_delta=0.10,
            new_pressure=0.10,
        )
        # 不应 raise
        service.update_narrative_state(game_with_case.game_id, "nobody", result)

    def test_update_no_game_no_crash(self, service):
        """游戏不存在时 update 不抛异常。"""
        result = NarrativeDirectorResult(suspect_id="s")
        service.update_narrative_state("no-game", "s", result)

    def test_update_result_as_dict(self, service, game_with_case):
        """result 以纯 dict 形式传入也能正常工作。"""
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id
        service.init_narrative_state(game_id, suspect_id)

        result_dict = {
            "suspect_id": suspect_id,
            "new_pressure": 0.35,
            "pressure_signals_detected": [
                {
                    "suspect_id": suspect_id,
                    "signal_type": "evasion",
                    "confidence": 0.70,
                    "description": "回避测试",
                    "source_question_snippet": "",
                    "source_response_snippet": "",
                }
            ],
            "triggered_beats": [],
            "state_transition": None,
        }
        service.update_narrative_state(game_id, suspect_id, result_dict)

        state = service.get_narrative_state(game_id, suspect_id)
        assert state["pressure"] == 0.35
        assert len(state["pressure_signals"]) == 1

    # ── transition_suspect_state_by_pressure ──────────────

    def test_transition_calm_to_pressured(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        old, new, changed = service.transition_suspect_state_by_pressure(
            game_id, suspect_id, 0.50
        )
        assert old == "calm"
        assert new == "pressured"
        assert changed is True
        assert game_with_case.suspect_states[suspect_id] == "pressured"

    def test_transition_calm_to_broken(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        old, new, changed = service.transition_suspect_state_by_pressure(
            game_id, suspect_id, 0.80
        )
        assert old == "calm"
        assert new == "broken"
        assert changed is True

    def test_transition_broken_terminal(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        # 先到 broken
        service.transition_suspect_state_by_pressure(game_id, suspect_id, 0.80)
        # 尝试降低
        old, new, changed = service.transition_suspect_state_by_pressure(
            game_id, suspect_id, 0.10
        )
        assert old == "broken"
        assert new == "broken"
        assert changed is False

    def test_transition_no_change_same_level(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        old, new, changed = service.transition_suspect_state_by_pressure(
            game_id, suspect_id, 0.20  # calm range
        )
        assert old == "calm"
        assert new == "calm"
        assert changed is False

    def test_transition_pressured_to_calm(self, service, game_with_case):
        """pressured 下降回 calm 范围 → 可回退。"""
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        # 先到 pressured
        service.transition_suspect_state_by_pressure(game_id, suspect_id, 0.50)
        # 再回到 calm
        old, new, changed = service.transition_suspect_state_by_pressure(
            game_id, suspect_id, 0.10
        )
        assert old == "pressured"
        assert new == "calm"
        assert changed is True

    def test_transition_missing_game(self, service):
        old, new, changed = service.transition_suspect_state_by_pressure(
            "no-game", "s", 0.80
        )
        assert old == "calm"
        assert new == "calm"
        assert changed is False

    # ── store_story_beats & get_pending_beats ──────────────

    def test_store_and_get_pending_beats(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        service.init_narrative_state(game_id, suspect_id)

        beats = [
            _make_beat("beat-a", suspect_id, priority=1),
            _make_beat("beat-b", suspect_id, priority=2),
        ]
        service.store_story_beats(game_id, suspect_id, beats)

        pending = service.get_pending_beats(game_id, suspect_id)
        assert len(pending) == 2
        ids = {b["id"] if isinstance(b, dict) else b.id for b in pending}
        assert ids == {"beat-a", "beat-b"}

    def test_pending_beats_filters_triggered(self, service, game_with_case):
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        service.init_narrative_state(game_id, suspect_id)

        beats = [
            _make_beat("beat-x", suspect_id, min_pressure=0.20),
        ]
        service.store_story_beats(game_id, suspect_id, beats)

        # 模拟触发该节拍
        beat_triggered = _make_beat("beat-x", suspect_id, min_pressure=0.20)
        result = NarrativeDirectorResult(
            suspect_id=suspect_id,
            triggered_beats=[beat_triggered],
        )
        service.update_narrative_state(game_id, suspect_id, result)

        # 已触发 → pending 为空
        pending = service.get_pending_beats(game_id, suspect_id)
        assert len(pending) == 0

    def test_get_pending_beats_no_state_returns_all(self, service, game_with_case):
        """叙事状态未初始化时返回全部节拍。"""
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        beats = [
            _make_beat("beat-all", suspect_id),
        ]
        service.store_story_beats(game_id, suspect_id, beats)

        pending = service.get_pending_beats(game_id, suspect_id)
        assert len(pending) == 1

    def test_store_beats_model_dump_conversion(self, service, game_with_case):
        """验证 StoryBeat Pydantic 模型被转为 dict 存储。"""
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        service.init_narrative_state(game_id, suspect_id)

        # 使用纯 Pydantic 模型
        beat = _make_beat("beat-model", suspect_id)
        service.store_story_beats(game_id, suspect_id, [beat])

        # 内部存储应为 dict
        stored = game_with_case.story_beats[suspect_id]
        assert isinstance(stored, list)
        assert isinstance(stored[0], dict)
        assert stored[0]["id"] == "beat-model"

    def test_store_beats_dict_input(self, service, game_with_case):
        """dict 格式输入同样被正确处理。"""
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        service.init_narrative_state(game_id, suspect_id)

        beat_dict = {
            "id": "beat-dict",
            "suspect_id": suspect_id,
            "title": "Dict Beat",
            "description": "From dict",
            "trigger": {"min_pressure": 0.10},
            "effects": {},
            "priority": 1,
            "triggered": False,
            "triggered_at": None,
        }
        service.store_story_beats(game_id, suspect_id, [beat_dict])

        pending = service.get_pending_beats(game_id, suspect_id)
        assert len(pending) == 1
        assert pending[0]["id"] == "beat-dict"

    def test_store_beats_mixed_model_and_dict(self, service, game_with_case):
        """model + dict 混合输入。"""
        game_id = game_with_case.game_id
        suspect_id = game_with_case.case.suspects[0].id

        service.init_narrative_state(game_id, suspect_id)

        beat_model = _make_beat("beat-model", suspect_id)
        beat_dict = {
            "id": "beat-dict",
            "suspect_id": suspect_id,
            "title": "Dict Beat",
            "description": "From dict",
            "trigger": {"min_pressure": 0.10},
            "effects": {},
            "priority": 1,
            "triggered": False,
            "triggered_at": None,
        }
        service.store_story_beats(game_id, suspect_id, [beat_model, beat_dict])

        pending = service.get_pending_beats(game_id, suspect_id)
        assert len(pending) == 2


# ─────────────────────────────────────────────────────────
# 6. 向后兼容性测试
# ─────────────────────────────────────────────────────────

class TestBackwardCompatibility:
    """P6 模型与 GameState 向后兼容性测试。"""

    def test_game_state_default_narrative_fields(self):
        """旧 GameState JSON (无 narrative 字段) 使用默认空 dict。"""
        gs = GameState(
            game_id="test-backward",
            difficulty=GameDifficulty.CLASSIC,
        )
        assert gs.narrative_states == {}
        assert gs.story_beats == {}

    def test_narrative_state_all_defaults(self):
        """NarrativeState 新模型所有字段默认值正确。"""
        ns = NarrativeState(suspect_id="suspect-1")
        assert ns.pressure == 0.0
        assert ns.pressure_signals == []
        assert ns.triggered_beat_ids == []
        assert ns.pending_beat_ids == []
        assert ns.contradictions_detected == 0
        assert ns.topics_discussed == []
        assert ns.conversation_turn_count == 0
        assert ns.last_analysis_at is None

    def test_narrative_director_result_defaults(self):
        result = NarrativeDirectorResult(suspect_id="s")
        assert result.pressure_delta == 0.0
        assert result.new_pressure == 0.0
        assert result.pressure_signals_detected == []
        assert result.triggered_beats == []
        assert result.state_transition is None
        assert result.narrative_events == []
        assert result.watson_interjection is None

    def test_pressure_signal_timestamp_auto_set(self):
        signal = PressureSignal(
            suspect_id="s",
            signal_type=PressureSignalType.EVASION,
            confidence=0.75,
            description="测试",
        )
        assert signal.timestamp is not None
        assert isinstance(signal.timestamp, datetime)

    def test_pressure_signal_confidence_clamped(self):
        """confidence 通过 Field(ge=0, le=1) 约束, 创建时验证。"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            PressureSignal(
                suspect_id="s",
                signal_type=PressureSignalType.EVASION,
                confidence=1.5,
                description="bad confidence",
            )

    def test_story_beat_trigger_defaults(self):
        t = StoryBeatTrigger()
        assert t.min_pressure == 0.0
        assert t.min_state is None
        assert t.required_clue_ids == []
        assert t.required_topics == []
        assert t.min_contradiction_count == 0
        assert t.requires_any_signal_of == []

    def test_story_beat_effects_defaults(self):
        e = StoryBeatEffects()
        assert e.new_revelation is None
        assert e.state_transition is None
        assert e.reveals_secret_index is None
        assert e.new_clue_hint is None
        assert e.unlocks_scene_id is None
        assert e.watson_comment is None
        assert e.suspect_voluntary_statement is None

    def test_story_beat_defaults(self):
        beat = StoryBeat(
            id="beat-default",
            suspect_id="suspect-1",
            title="Test",
            description="Test",
            trigger=StoryBeatTrigger(),
            effects=StoryBeatEffects(),
        )
        assert beat.triggered is False
        assert beat.triggered_at is None
        assert beat.priority == 0

    def test_narrative_event_data_field(self):
        """NarrativeEvent.data 为 optional dict。"""
        e = NarrativeEvent(type="test", message="hello")
        assert e.data is None
        e2 = NarrativeEvent(type="test", message="hello", data={"key": "val"})
        assert e2.data == {"key": "val"}

    def test_game_state_serialization_includes_narrative(self):
        """GameState 序列化后包含 narrative 字段。"""
        gs = GameState(
            game_id="serialize-test",
            difficulty=GameDifficulty.CLASSIC,
            narrative_states={"suspect-1": {"pressure": 0.5}},
            story_beats={"suspect-1": [{"id": "beat-1"}]},
        )
        d = gs.model_dump()
        assert "narrative_states" in d
        assert "story_beats" in d
        assert d["narrative_states"]["suspect-1"]["pressure"] == 0.5


# ─────────────────────────────────────────────────────────
# 7. 集成测试 (mock LLM)
# ─────────────────────────────────────────────────────────

class TestAnalyzeConversationTurnIntegration:
    """analyze_conversation_turn 集成测试。"""

    @pytest.fixture
    def int_settings(self) -> Settings:
        return Settings(
            enable_narrative_director=True,
            enable_pressure_accumulation=True,
            enable_story_beats=True,
            pressure_signal_weight_evasion=0.15,
            pressure_signal_weight_contradiction=0.30,
            pressure_signal_weight_over_explanation=0.10,
            pressure_signal_weight_emotional_leakage=0.20,
            pressure_signal_weight_inconsistency=0.25,
            pressure_signal_weight_deflection=0.10,
            pressure_decay_per_turn=0.0,
            pressure_threshold_pressured=0.40,
            pressure_threshold_broken=0.75,
            narrative_director_max_history_tokens=4000,
            narrative_director_temperature=0.3,
        )

    @pytest.mark.asyncio
    async def test_analyze_conversation_turn_full_flow(self, int_settings):
        """mock LLM 返回两个信号 → 验证全链路结果。"""
        mock_llm_response = {
            "signals": [
                {
                    "signal_type": "evasion",
                    "confidence": 0.80,
                    "description": "嫌疑人刻意回避不在场证明问题",
                },
                {
                    "signal_type": "contradiction",
                    "confidence": 0.60,
                    "description": "时间线前后矛盾",
                },
            ]
        }

        with patch(
            "app.agents.narrative_director_agent.get_settings",
            return_value=int_settings,
        ):
            with patch("app.agents.narrative_director_agent.ChatOpenAI"):
                agent = NarrativeDirectorAgent()

        with patch(
            "app.agents.narrative_director_agent.invoke_with_retry",
            new=AsyncMock(return_value=mock_llm_response),
        ):
            suspect = Suspect(
                id="suspect-int-1",
                name="查尔斯·莫里亚蒂",
                age=38,
                relationship_to_victim="商业对手",
                background="经营地下钱庄，与被害人有长期恩怨",
                motive="利益冲突与复仇",
                timeline="声称案发时在剧院",
                is_guilty=True,
                personality_traits=["冷酷", "狡猾"],
                secrets=["真正身份是犯罪集团头目"],
            )

            case = Case(
                id="case-int-1",
                victim_name="测试受害者",
                victim_background="背景",
                cause_of_death="未知",
                time_of_death="未知",
                location="未知",
                date=datetime(1895, 10, 15),
                suspects=[suspect],
            )

            narrative_state = NarrativeState(suspect_id="suspect-int-1")

            pending_beats = [
                _make_beat(
                    "beat-int-1",
                    suspect_id="suspect-int-1",
                    min_pressure=0.15,
                    watson_comment="福尔摩斯，他看起来有些不安。",
                    priority=1,
                ),
                _make_beat(
                    "beat-int-2",
                    suspect_id="suspect-int-1",
                    min_pressure=0.50,
                    min_state="pressured",
                    new_revelation="不在场证明存在重大漏洞",
                    priority=5,
                ),
            ]

            result = await agent.analyze_conversation_turn(
                suspect=suspect,
                case=case,
                user_question="案发当晚你在哪里？",
                suspect_response="我...我在剧院看戏，对，就是剧院。很多人都看到我了。",
                recent_history=[],
                narrative_state=narrative_state,
                pending_beats=pending_beats,
            )

            # 验证基本字段
            assert result.suspect_id == "suspect-int-1"
            assert len(result.pressure_signals_detected) == 2

            # 压力: 0.80*0.15 + 0.60*0.30 = 0.12 + 0.18 = 0.30
            assert result.new_pressure == pytest.approx(0.30)
            assert result.pressure_delta == pytest.approx(0.30)

            # 节拍: beat-int-1 (min=0.15, pressure=0.30 => qualify)
            assert len(result.triggered_beats) == 1
            assert result.triggered_beats[0].id == "beat-int-1"

            # 状态转换: 0.30 < 0.40 => None
            assert result.state_transition is None

            # 事件: 2 signals + 1 beat + 1 watson = 4
            event_types = {e.type for e in result.narrative_events}
            assert "pressure_warning" in event_types
            assert "beat_triggered" in event_types
            assert "watson_interjection" in event_types

    @pytest.mark.asyncio
    async def test_analyze_with_state_transition(self, int_settings):
        """高压力输入触发状态转换。"""
        mock_llm_response = {
            "signals": [
                {
                    "signal_type": "contradiction",
                    "confidence": 1.0,
                    "description": "重大矛盾暴露",
                },
            ]
        }

        with patch(
            "app.agents.narrative_director_agent.get_settings",
            return_value=int_settings,
        ):
            with patch("app.agents.narrative_director_agent.ChatOpenAI"):
                agent = NarrativeDirectorAgent()

        with patch(
            "app.agents.narrative_director_agent.invoke_with_retry",
            new=AsyncMock(return_value=mock_llm_response),
        ):
            suspect = Suspect(
                id="suspect-trans",
                name="嫌疑人转态",
                age=30,
                background="背景",
                motive="动机",
                timeline="时间线",
                is_guilty=True,
                personality_traits=["紧张"],
                secrets=[],
            )
            case = Case(
                id="case-trans",
                victim_name="受害者",
                victim_background="背景",
                cause_of_death="未知",
                time_of_death="未知",
                location="未知",
                date=datetime(1895, 10, 15),
                suspects=[suspect],
            )

            # 已有压力的状态
            narrative_state = NarrativeState(
                suspect_id="suspect-trans",
                pressure=0.55,
            )

            result = await agent.analyze_conversation_turn(
                suspect=suspect,
                case=case,
                user_question="说实话！",
                suspect_response="我...我...",
                recent_history=[],
                narrative_state=narrative_state,
                pending_beats=[],
            )

            # 0.55 + 1.0*0.30 = 0.85
            assert result.new_pressure == pytest.approx(0.85)
            # state: 0.85 >= 0.75 → broken
            assert result.state_transition is not None
            assert result.state_transition["to"] == "broken"

    @pytest.mark.asyncio
    async def test_llm_failure_graceful_degradation(self, int_settings):
        """LLM 抛出异常 → 返回空结果，压力不变。"""
        with patch(
            "app.agents.narrative_director_agent.get_settings",
            return_value=int_settings,
        ):
            with patch("app.agents.narrative_director_agent.ChatOpenAI"):
                agent = NarrativeDirectorAgent()

        with patch(
            "app.agents.narrative_director_agent.invoke_with_retry",
            new=AsyncMock(side_effect=Exception("LLM API error")),
        ):
            suspect = Suspect(
                id="suspect-fail",
                name="失败嫌疑人",
                age=30,
                background="背景",
                motive="动机",
                timeline="时间线",
                is_guilty=False,
                personality_traits=["冷静"],
                secrets=[],
            )
            case = Case(
                id="case-fail",
                victim_name="受害者",
                victim_background="背景",
                cause_of_death="未知",
                time_of_death="未知",
                location="未知",
                date=datetime(1895, 10, 15),
                suspects=[suspect],
            )

            narrative_state = NarrativeState(
                suspect_id="suspect-fail",
                pressure=0.35,
            )

            result = await agent.analyze_conversation_turn(
                suspect=suspect,
                case=case,
                user_question="你在哪里？",
                suspect_response="我不知道。",
                recent_history=[],
                narrative_state=narrative_state,
                pending_beats=[],
            )

            # 失败降级 → 空结果，压力不变
            assert result.pressure_delta == 0.0
            assert result.new_pressure == 0.35
            assert result.pressure_signals_detected == []
            assert result.triggered_beats == []
            assert result.state_transition is None

    @pytest.mark.asyncio
    async def test_with_conversation_history(self, int_settings):
        """带对话历史的场景 — 验证 history 截断不崩溃。"""
        mock_llm_response = {"signals": []}

        with patch(
            "app.agents.narrative_director_agent.get_settings",
            return_value=int_settings,
        ):
            with patch("app.agents.narrative_director_agent.ChatOpenAI"):
                agent = NarrativeDirectorAgent()

        with patch(
            "app.agents.narrative_director_agent.invoke_with_retry",
            new=AsyncMock(return_value=mock_llm_response),
        ):
            suspect = Suspect(
                id="suspect-hist",
                name="历史嫌疑人",
                age=30,
                background="背景",
                motive="动机",
                timeline="时间线",
                is_guilty=False,
                personality_traits=["健谈"],
                secrets=[],
            )
            case = Case(
                id="case-hist",
                victim_name="受害者",
                victim_background="背景",
                cause_of_death="未知",
                time_of_death="未知",
                location="未知",
                date=datetime(1895, 10, 15),
                suspects=[suspect],
            )

            # 构造较长的对话历史
            history = []
            for i in range(20):
                history.append({"role": "user", "content": f"问题{i}"})
                history.append({"role": "assistant", "content": f"回答{i}"})

            narrative_state = NarrativeState(suspect_id="suspect-hist")

            result = await agent.analyze_conversation_turn(
                suspect=suspect,
                case=case,
                user_question="最新的问题",
                suspect_response="最新的回答",
                recent_history=history,
                narrative_state=narrative_state,
                pending_beats=[],
            )

            # 无信号时压力不变 (decay=0)
            assert result.new_pressure == 0.0
            assert result.pressure_signals_detected == []


# ─────────────────────────────────────────────────────────
# 8. 单例 & _format_history_for_prompt
# ─────────────────────────────────────────────────────────

class TestSingletonAndHelpers:
    """测试单例获取和辅助方法。"""

    def test_get_narrative_director_returns_agent(self, test_settings):
        from app.agents.narrative_director_agent import get_narrative_director

        with patch(
            "app.agents.narrative_director_agent.get_settings",
            return_value=test_settings,
        ):
            with patch("app.agents.narrative_director_agent.ChatOpenAI"):
                nd = get_narrative_director()
                assert isinstance(nd, NarrativeDirectorAgent)

    def test_format_history_empty(self, agent):
        result = agent._format_history_for_prompt([])
        assert "尚无对话历史" in result

    def test_format_history_single_turn(self, agent):
        history = [
            {"role": "user", "content": "你在哪里？"},
            {"role": "assistant", "content": "我在剧院。"},
        ]
        result = agent._format_history_for_prompt(history)
        assert "[侦探]" in result
        assert "[嫌疑人]" in result
        assert "你在哪里" in result
        assert "我在剧院" in result

    def test_format_history_truncates_long_messages(self, agent):
        history = [
            {"role": "user", "content": "A" * 300},
        ]
        result = agent._format_history_for_prompt(history)
        # 超过 200 字符会被截断
        assert "（截断）" in result
        assert len(result) < 350  # 格式开销 + 截断内容

    def test_format_history_with_system_role(self, agent):
        history = [
            {"role": "system", "content": "系统消息"},
        ]
        result = agent._format_history_for_prompt(history)
        assert "[system]" in result
