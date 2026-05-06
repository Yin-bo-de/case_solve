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
        for c in case.clues:
            assert c.obviousness >= 0.7, (
                f"Easy 线索 obviousness 应 >= 0.7，{c.id}={c.obviousness}"
            )

    def test_classic_clues(self):
        case = _make_mock_case("classic")
        for c in case.clues:
            assert 0.4 <= c.obviousness <= 0.8, (
                f"Classic 线索 obviousness 应在 0.4~0.8，{c.id}={c.obviousness}"
            )

    def test_hardcore_clues(self):
        case = _make_mock_case("hardcore")
        for c in case.clues:
            assert c.obviousness <= 0.5, (
                f"Hardcore 线索 obviousness 应 <= 0.5，{c.id}={c.obviousness}"
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

        with patch("app.agents.watson_agent.get_settings") as mock_settings:
            settings = MagicMock()
            settings.openai_api_key = None
            mock_settings.return_value = settings

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

    def test_all_clues_covered_by_objects(self):
        """每个线索必须至少出现在某个 object.hidden_clue_ids 中"""
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            all_hidden_ids: set = set()
            for scene in case.scenes:
                for obj in scene.objects:
                    all_hidden_ids.update(obj.hidden_clue_ids)
            for clue in case.clues:
                assert clue.id in all_hidden_ids, (
                    f"{difficulty}: 线索 '{clue.id}' 未被任何 object 引用"
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


# ─── 证人难度分布测试 ──────────────────────────────────────────

class TestWitnessDifficultyDistribution:
    """验证不同难度下证人的可信度与撒谎分布"""

    def test_easy_no_lying_witnesses(self):
        case = _make_mock_case("easy")
        lying = [w for w in case.witnesses if w.is_lying_for_someone]
        assert len(lying) == 0, f"Easy 难度不应有撒谎证人，实际 {len(lying)}"

    def test_easy_witness_credibility_high(self):
        case = _make_mock_case("easy")
        for w in case.witnesses:
            assert w.credibility >= 0.8, (
                f"Easy 证人可信度应 >= 0.8，{w.id}={w.credibility}"
            )

    def test_classic_at_most_one_lying_witness(self):
        case = _make_mock_case("classic")
        lying = [w for w in case.witnesses if w.is_lying_for_someone]
        assert len(lying) <= 1, f"Classic 难度至多 1 名撒谎证人，实际 {len(lying)}"

    def test_classic_witness_credibility_range(self):
        case = _make_mock_case("classic")
        for w in case.witnesses:
            assert 0.5 <= w.credibility <= 0.8, (
                f"Classic 证人可信度应在 0.5~0.8，{w.id}={w.credibility}"
            )

    def test_hardcore_at_most_two_lying_witnesses(self):
        case = _make_mock_case("hardcore")
        lying = [w for w in case.witnesses if w.is_lying_for_someone]
        assert len(lying) <= 2, f"Hardcore 难度至多 2 名撒谎证人，实际 {len(lying)}"

    def test_hardcore_witness_credibility_low(self):
        case = _make_mock_case("hardcore")
        for w in case.witnesses:
            assert 0.3 <= w.credibility <= 0.6, (
                f"Hardcore 证人可信度应在 0.3~0.6，{w.id}={w.credibility}"
            )


# ─── P4 推理类型门槛阈值测试 ────────────────────────────────────

class TestAccusationThresholdByDifficulty:
    """验证不同难度下的指认门槛配置生效"""

    def _setup_game(self, difficulty: GameDifficulty):
        """辅助：创建指定难度游戏并填充最低观察记录"""
        from app.models.case import Case, Suspect, Clue, Observation
        from datetime import datetime
        service = GameService()
        game = service.create_game(difficulty=difficulty)
        game.case = Case(
            id="c1",
            victim_name="Test",
            victim_background="test",
            cause_of_death="test",
            time_of_death="test",
            location="test",
            date=datetime.utcnow(),
            suspects=[Suspect(id="s1", name="A", age=30, background="test", motive="test", timeline="test")],
            clues=[Clue(id="cl1", description="test", clue_type="physical")],
        )
        service._games[game.game_id] = game
        chain = service.get_or_create_deduction_chain(game.game_id)
        for i in range(5):
            chain.observations.append(Observation(id=f"obs{i}", description=f"观察{i}", location="书房"))
        return service, game

    def test_easy_threshold_is_zero(self):
        """Easy 难度门槛为 0，无需 interrogation 即可指认"""
        from app.models.case import Inference
        service, game = self._setup_game(GameDifficulty.EASY)
        chain = service.get_or_create_deduction_chain(game.game_id)
        chain.inferences.append(Inference(id="inf1", content="推理1", node_type="fact"))

        readiness = service.check_conclusion_readiness(game.game_id)
        assert readiness["threshold"] == 0
        assert readiness["is_ready"] is True

    def test_classic_threshold_is_one(self):
        """Classic 难度门槛为 1，需要至少 1 个 interrogation"""
        from app.models.case import Inference
        service, game = self._setup_game(GameDifficulty.CLASSIC)
        chain = service.get_or_create_deduction_chain(game.game_id)

        # 只有 fact，不满足
        chain.inferences.append(Inference(id="inf1", content="推理1", node_type="fact"))
        readiness = service.check_conclusion_readiness(game.game_id)
        assert readiness["threshold"] == 1
        assert readiness["is_ready"] is False

        # 添加 interrogation，满足
        chain.inferences.append(Inference(id="inf2", content="推理2", node_type="interrogation"))
        readiness = service.check_conclusion_readiness(game.game_id)
        assert readiness["is_ready"] is True

    def test_hardcore_threshold_is_two(self):
        """Hardcore 难度门槛为 2，需要至少 2 个 interrogation"""
        from app.models.case import Inference
        service, game = self._setup_game(GameDifficulty.HARDCORE)
        chain = service.get_or_create_deduction_chain(game.game_id)

        # 1 个 interrogation 不够
        chain.inferences.append(Inference(id="inf1", content="推理1", node_type="interrogation"))
        readiness = service.check_conclusion_readiness(game.game_id)
        assert readiness["threshold"] == 2
        assert readiness["is_ready"] is False

        # 再加 1 个，满足
        chain.inferences.append(Inference(id="inf2", content="推理2", node_type="interrogation"))
        readiness = service.check_conclusion_readiness(game.game_id)
        assert readiness["is_ready"] is True

    def test_mixed_counts_as_half(self):
        """mixed 推理计为 0.5 个 interrogation"""
        from app.models.case import Inference
        service, game = self._setup_game(GameDifficulty.HARDCORE)
        chain = service.get_or_create_deduction_chain(game.game_id)

        # 1 个 interrogation + 1 个 mixed = 1.5 < 2，不满足
        chain.inferences.extend([
            Inference(id="inf1", content="推理1", node_type="interrogation"),
            Inference(id="inf2", content="推理2", node_type="mixed"),
        ])
        readiness = service.check_conclusion_readiness(game.game_id)
        assert readiness["is_ready"] is False

        # 再加 1 个 mixed = 1.5 + 0.5 = 2.0，满足
        chain.inferences.append(Inference(id="inf3", content="推理3", node_type="mixed"))
        readiness = service.check_conclusion_readiness(game.game_id)
        assert readiness["is_ready"] is True
