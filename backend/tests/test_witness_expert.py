"""
证人/专家角色单元测试
覆盖: mock 案件结构、交叉引用一致性、Agent mock 回退、线索提取兼容性
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


# ─── 案件结构测试 ────────────────────────────────────────────

class TestMockCaseWitnessExpertPresence:
    """验证 mock 案件包含证人和专家"""

    def test_easy_has_witnesses_and_expert(self):
        case = _make_mock_case("easy")
        assert len(case.witnesses) >= 1, f"Easy 应至少 1 名证人，实际 {len(case.witnesses)}"
        assert len(case.experts) == 1, f"应恰好 1 名专家，实际 {len(case.experts)}"

    def test_classic_has_witnesses_and_expert(self):
        case = _make_mock_case("classic")
        assert len(case.witnesses) >= 1, f"Classic 应至少 1 名证人，实际 {len(case.witnesses)}"
        assert len(case.experts) == 1, f"应恰好 1 名专家，实际 {len(case.experts)}"

    def test_hardcore_has_witnesses_and_expert(self):
        case = _make_mock_case("hardcore")
        assert len(case.witnesses) >= 1, f"Hardcore 应至少 1 名证人，实际 {len(case.witnesses)}"
        assert len(case.experts) == 1, f"应恰好 1 名专家，实际 {len(case.experts)}"

    def test_expert_preliminary_report_not_empty(self):
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            expert = case.experts[0]
            assert expert.preliminary_report and expert.preliminary_report.strip(), (
                f"{difficulty}: 专家 preliminary_report 不应为空"
            )


class TestMockCaseRelationshipConsistency:
    """验证证人/专家与其他案件元素的交叉引用一致性"""

    def test_witness_related_suspect_ids_valid(self):
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            suspect_ids = {s.id for s in case.suspects}
            for witness in case.witnesses:
                for sid in witness.related_suspect_ids:
                    assert sid in suspect_ids, (
                        f"{difficulty}: 证人 {witness.id} 引用了不存在的嫌疑人 {sid}"
                    )

    def test_witness_related_suspect_ids_not_empty(self):
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            for witness in case.witnesses:
                assert len(witness.related_suspect_ids) >= 1, (
                    f"{difficulty}: 证人 {witness.id} 应至少关联 1 名嫌疑人"
                )

    def test_expert_related_clue_ids_valid(self):
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            clue_ids = {c.id for c in case.clues}
            for expert in case.experts:
                for cid in expert.related_clue_ids:
                    assert cid in clue_ids, (
                        f"{difficulty}: 专家 {expert.id} 引用了不存在的线索 {cid}"
                    )

    def test_expert_key_findings_related_clue_ids_valid(self):
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            clue_ids = {c.id for c in case.clues}
            for expert in case.experts:
                for finding in expert.key_findings:
                    for cid in finding.related_clue_ids:
                        assert cid in clue_ids, (
                            f"{difficulty}: 专家发现 {finding.topic} 引用了不存在的线索 {cid}"
                        )

    def test_expert_covers_at_least_one_non_red_herring_physical_clue(self):
        for difficulty in ["easy", "classic", "hardcore"]:
            case = _make_mock_case(difficulty)
            physical_clue_ids = {
                c.id for c in case.clues
                if not c.is_red_herring and c.clue_type in ("physical", "forensic")
            }
            for expert in case.experts:
                covered = set(expert.related_clue_ids) & physical_clue_ids
                assert len(covered) >= 1, (
                    f"{difficulty}: 专家 {expert.id} 应覆盖至少 1 条非红鲱鱼物证线索"
                )


# ─── Service 层测试 ──────────────────────────────────────────

class TestAddUserClueActorSourceType:
    """验证 add_user_clue 支持 witness/expert source_type"""

    def test_add_clue_with_witness_source_type(self):
        service = GameService()
        game = service.create_game(GameDifficulty.CLASSIC)
        case = _make_mock_case("classic")
        service.set_case(game.game_id, case)

        clue = service.add_user_clue(
            game_id=game.game_id,
            user_label="证人证词片段",
            description="我当晚确实看到了一个人影。",
            source_type="witness",
            source_ref="witness-1",
            quoted_text="我当晚确实看到了一个人影。",
        )
        assert clue.source_type == "witness"
        assert clue.source_ref == "witness-1"
        assert clue.user_generated is True

    def test_add_clue_with_expert_source_type(self):
        service = GameService()
        game = service.create_game(GameDifficulty.CLASSIC)
        case = _make_mock_case("classic")
        service.set_case(game.game_id, case)

        clue = service.add_user_clue(
            game_id=game.game_id,
            user_label="法医报告摘录",
            description="死者体内检出微量砷化物。",
            source_type="expert",
            source_ref="expert-1",
            quoted_text="死者体内检出微量砷化物。",
        )
        assert clue.source_type == "expert"
        assert clue.source_ref == "expert-1"


# ─── Agent mock 回退测试 ─────────────────────────────────────

class TestWitnessAgentMockFallback:
    """验证 WitnessAgent mock 模式正确回退"""

    @pytest.fixture
    def mock_witness(self):
        witness = MagicMock()
        witness.name = "莉莉·哈丁"
        witness.occupation = "洗衣女工"
        witness.relationship_to_case = "隔壁邻居"
        witness.timeline = "案发当晚在家"
        witness.personality_traits = ["胆小", "诚实"]
        witness.key_observations = ["昨晚9:30看见有人从后门离开"]
        witness.is_lying_for_someone = False
        witness.bribed_by_suspect_id = None
        witness.credibility = 0.75
        return witness

    @pytest.fixture
    def mock_case(self):
        case = MagicMock()
        case.victim_name = "受害者"
        case.clues = []
        case.suspects = []
        return case

    @pytest.mark.asyncio
    async def test_generate_response_mock_fallback(self, mock_witness, mock_case):
        from app.agents.witness_agent import WitnessAgent
        agent = WitnessAgent()

        with patch("app.agents.witness_agent.get_settings") as mock_settings:
            settings = MagicMock()
            settings.openai_api_key = None
            settings.witness_agent_max_history_messages = 8
            mock_settings.return_value = settings

            response = await agent.generate_response(
                witness=mock_witness,
                case=mock_case,
                user_question="你看到了什么？",
            )
            assert response and len(response) > 0
            assert "昨晚" in response or "看见" in response or "看到" in response

    @pytest.mark.asyncio
    async def test_detect_credibility_mock_fallback(self, mock_witness, mock_case):
        from app.agents.witness_agent import WitnessAgent
        agent = WitnessAgent()

        with patch("app.agents.witness_agent.get_settings") as mock_settings:
            settings = MagicMock()
            settings.openai_api_key = None
            mock_settings.return_value = settings

            result = await agent.detect_credibility(
                witness=mock_witness,
                response="我什么都没看到。",
                case=mock_case,
            )
            assert isinstance(result, dict)
            assert "credibility_concern" in result
            assert result["credibility_concern"] is False  # 诚实证人

    @pytest.mark.asyncio
    async def test_detect_credibility_lying_mock(self, mock_witness, mock_case):
        from app.agents.witness_agent import WitnessAgent
        agent = WitnessAgent()

        mock_witness.is_lying_for_someone = True
        mock_witness.bribed_by_suspect_id = "suspect-1"

        with patch("app.agents.witness_agent.get_settings") as mock_settings:
            settings = MagicMock()
            settings.openai_api_key = None
            mock_settings.return_value = settings

            result = await agent.detect_credibility(
                witness=mock_witness,
                response="我真的不知道。",
                case=mock_case,
            )
            assert result["credibility_concern"] is True
            assert result["concern_type"] == "bribery"


class TestExpertAgentMockFallback:
    """验证 ExpertAgent mock 模式正确回退"""

    @pytest.fixture
    def mock_expert(self):
        expert = MagicMock()
        expert.name = "塞西尔·哈罗德医生"
        expert.title = "皇家法医"
        expert.expertise = ["法医病理", "毒物分析"]
        expert.preliminary_report = "死者死于钝器外伤。"
        expert.key_findings = []
        expert.methodology_notes = ["时间推断误差 ±30 分钟"]
        expert.related_clue_ids = ["clue-1"]
        return expert

    @pytest.fixture
    def mock_case(self):
        case = MagicMock()
        case.victim_name = "受害者"
        case.cause_of_death = "钝器伤"
        case.time_of_death = "昨晚10点前后"
        case.clues = []
        return case

    @pytest.mark.asyncio
    async def test_get_preliminary_report_uses_pre_generated(self, mock_expert, mock_case):
        from app.agents.expert_agent import ExpertAgent
        agent = ExpertAgent()

        report = await agent.get_preliminary_report(expert=mock_expert, case=mock_case)
        assert report == "死者死于钝器外伤。"

    @pytest.mark.asyncio
    async def test_answer_question_mock_fallback(self, mock_expert, mock_case):
        from app.agents.expert_agent import ExpertAgent
        agent = ExpertAgent()

        with patch("app.agents.expert_agent.get_settings") as mock_settings:
            settings = MagicMock()
            settings.openai_api_key = None
            settings.expert_agent_max_history_messages = 6
            mock_settings.return_value = settings

            response = await agent.answer_question(
                expert=mock_expert,
                case=mock_case,
                user_question="死亡时间是什么时候？",
            )
            assert response and len(response) > 0
            assert "时间" in response

    @pytest.mark.asyncio
    async def test_answer_question_refuses_motive_out_of_scope(self, mock_expert, mock_case):
        from app.agents.expert_agent import ExpertAgent
        agent = ExpertAgent()

        with patch("app.agents.expert_agent.get_settings") as mock_settings:
            settings = MagicMock()
            settings.openai_api_key = None
            settings.expert_agent_max_history_messages = 6
            mock_settings.return_value = settings

            response = await agent.answer_question(
                expert=mock_expert,
                case=mock_case,
                user_question="凶手是谁？",
            )
            # mock 回退或 prompt 拒绝均可接受
            assert "超出" in response or "范围" in response or "非法医" in response or "尚无法" in response or "不支持" in response


# ─── WatsonChatContext 测试 ──────────────────────────────────

class TestWatsonChatContextIncludesWitnessesExperts:
    """验证 build_watson_chat_context 包含证人和专家摘要"""

    def test_context_includes_witnesses_and_experts(self):
        service = GameService()
        game = service.create_game(GameDifficulty.CLASSIC)
        case = _make_mock_case("classic")
        service.set_case(game.game_id, case)

        context = service.build_watson_chat_context(game.game_id)
        assert context is not None
        assert len(context.witnesses) == len(case.witnesses)
        assert len(context.experts) == len(case.experts)

        if context.witnesses:
            w = context.witnesses[0]
            assert "id" in w
            assert "name" in w
            assert "occupation" in w

        if context.experts:
            e = context.experts[0]
            assert "id" in e
            assert "name" in e
            assert "title" in e
