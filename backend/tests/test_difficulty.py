"""
T1.4 难度系统单元测试
覆盖: 案件生成线索分布、错误次数配置、华生触发频率
"""
import pytest
from unittest.mock import patch, MagicMock

from app.models.game import GameDifficulty
from app.services.game_service import GameService


# ─── 辅助函数 ───────────────────────────────────────────────

def _make_mock_case(difficulty: str):
    """调用 _generate_mock_case 生成测试用案件（绕过LLM初始化）"""
    from app.agents.case_generator_agent import CaseGeneratorAgent
    with patch.object(CaseGeneratorAgent, "__init__", lambda self: None):
        agent = CaseGeneratorAgent.__new__(CaseGeneratorAgent)
    return agent._generate_mock_case("test-case-id", difficulty)


# ─── T1.1 线索分布测试 ────────────────────────────────────────

class TestClueDifficultyDistribution:
    def test_easy_clues(self):
        case = _make_mock_case("easy")
        red_herrings = [c for c in case.clues if c.is_red_herring]
        real_clues = [c for c in case.clues if not c.is_red_herring]

        assert len(red_herrings) == 1, f"Easy 应有 1 个红鲱鱼，实际 {len(red_herrings)}"
        for c in real_clues:
            assert c.obviousness >= 0.7, (
                f"Easy 真实线索 obviousness 应 >= 0.7，{c.id}={c.obviousness}"
            )

    def test_classic_clues(self):
        case = _make_mock_case("classic")
        red_herrings = [c for c in case.clues if c.is_red_herring]
        real_clues = [c for c in case.clues if not c.is_red_herring]

        assert len(red_herrings) == 2, f"Classic 应有 2 个红鲱鱼，实际 {len(red_herrings)}"
        for c in real_clues:
            assert 0.4 <= c.obviousness <= 0.8, (
                f"Classic 真实线索 obviousness 应在 0.4~0.8，{c.id}={c.obviousness}"
            )

    def test_hardcore_clues(self):
        case = _make_mock_case("hardcore")
        red_herrings = [c for c in case.clues if c.is_red_herring]
        real_clues = [c for c in case.clues if not c.is_red_herring]

        assert len(red_herrings) == 3, f"Hardcore 应有 3 个红鲱鱼，实际 {len(red_herrings)}"
        for c in real_clues:
            assert c.obviousness <= 0.5, (
                f"Hardcore 真实线索 obviousness 应 <= 0.5，{c.id}={c.obviousness}"
            )

    def test_all_clues_have_obviousness_field(self):
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            for clue in case.clues:
                assert hasattr(clue, "obviousness"), f"{difficulty}: clue {clue.id} 缺少 obviousness 字段"
                assert 0.0 <= clue.obviousness <= 1.0


# ─── T1.1 错误次数测试 ────────────────────────────────────────

class TestMaxMistakesByDifficulty:
    def _create_game_service(self):
        with patch("app.agents.case_generator_agent.CaseGeneratorAgent.__init__", return_value=None):
            return GameService()

    def test_easy_max_mistakes(self):
        service = GameService()
        game = service.create_game(GameDifficulty.EASY)
        assert game.max_mistakes == 3

    def test_classic_max_mistakes(self):
        service = GameService()
        game = service.create_game(GameDifficulty.CLASSIC)
        assert game.max_mistakes == 2

    def test_hardcore_max_mistakes(self):
        service = GameService()
        game = service.create_game(GameDifficulty.HARDCORE)
        assert game.max_mistakes == 1


# ─── T1.2 华生主动频率测试 ────────────────────────────────────

class TestWatsonProactiveRate:
    def test_from_difficulty_easy(self):
        from app.agents.watson_agent import WatsonAgent
        with patch.object(WatsonAgent, "__init__", lambda self, proactive_rate=0.5: setattr(self, "proactive_rate", proactive_rate) or None):
            agent = WatsonAgent.from_difficulty("easy")
        assert agent.proactive_rate == 0.8

    def test_from_difficulty_classic(self):
        from app.agents.watson_agent import WatsonAgent
        with patch.object(WatsonAgent, "__init__", lambda self, proactive_rate=0.5: setattr(self, "proactive_rate", proactive_rate) or None):
            agent = WatsonAgent.from_difficulty("classic")
        assert agent.proactive_rate == 0.5

    def test_from_difficulty_hardcore(self):
        from app.agents.watson_agent import WatsonAgent
        with patch.object(WatsonAgent, "__init__", lambda self, proactive_rate=0.5: setattr(self, "proactive_rate", proactive_rate) or None):
            agent = WatsonAgent.from_difficulty("hardcore")
        assert agent.proactive_rate == 0.2

    def test_from_difficulty_unknown_falls_back_to_classic(self):
        from app.agents.watson_agent import WatsonAgent
        with patch.object(WatsonAgent, "__init__", lambda self, proactive_rate=0.5: setattr(self, "proactive_rate", proactive_rate) or None):
            agent = WatsonAgent.from_difficulty("unknown")
        assert agent.proactive_rate == 0.5

    @pytest.mark.asyncio
    async def test_share_observation_respects_proactive_rate_zero(self):
        """proactive_rate=0 时，share_observation 始终返回 None"""
        from app.agents.watson_agent import WatsonAgent
        from app.models.case import Observation
        from datetime import datetime

        with patch.object(WatsonAgent, "__init__", lambda self, proactive_rate=0.5: setattr(self, "proactive_rate", proactive_rate) or None):
            agent = WatsonAgent(proactive_rate=0.0)

        obs = Observation(id="obs-1", description="测试", location="书房", timestamp=datetime.utcnow())
        result = await agent.share_observation(obs)
        assert result is None

    @pytest.mark.asyncio
    async def test_share_observation_respects_proactive_rate_one(self):
        """proactive_rate=1 时，share_observation 始终返回非 None"""
        from app.agents.watson_agent import WatsonAgent
        from app.models.case import Observation
        from datetime import datetime

        with patch.object(WatsonAgent, "__init__", lambda self, proactive_rate=0.5: setattr(self, "proactive_rate", proactive_rate) or None):
            agent = WatsonAgent(proactive_rate=1.0)

        obs = Observation(id="obs-1", description="测试", location="书房", timestamp=datetime.utcnow())
        result = await agent.share_observation(obs)
        assert result is not None


# ─── 章节 8.4 Scene 生成测试 ────────────────────────────────────

class TestSceneGeneration:
    """验证案件生成包含有效的 scenes，满足章节 4 的结构约束"""

    def test_mock_case_has_at_least_3_scenes(self):
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            assert len(case.scenes) >= 3, (
                f"{difficulty}: 期望至少 3 个 scene，实际 {len(case.scenes)}"
            )

    def test_each_scene_has_3_to_6_objects(self):
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            for scene in case.scenes:
                assert 3 <= len(scene.objects) <= 6, (
                    f"{difficulty}: scene '{scene.name}' 对象数 {len(scene.objects)} 不在 3-6 范围内"
                )

    def test_non_red_herring_clues_covered_by_objects(self):
        """每个非红鲱鱼线索必须至少出现在某个 object.hidden_clue_ids 中"""
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            all_hidden_ids: set = set()
            for scene in case.scenes:
                for obj in scene.objects:
                    all_hidden_ids.update(obj.hidden_clue_ids)
            real_clues = [c for c in case.clues if not c.is_red_herring]
            for clue in real_clues:
                assert clue.id in all_hidden_ids, (
                    f"{difficulty}: 真实线索 '{clue.id}' 未被任何 object 引用"
                )

    def test_investigation_locations_mirrors_scene_names(self):
        """investigation_locations 应是 scene 名称的镜像"""
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            expected = [s.name for s in case.scenes]
            assert case.investigation_locations == expected, (
                f"{difficulty}: investigation_locations={case.investigation_locations} "
                f"与 scene 名称 {expected} 不一致"
            )
