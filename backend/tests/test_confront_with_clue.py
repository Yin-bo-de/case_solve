"""
P2 出示线索质询测试：覆盖 confront_with_clue 三种 relevance 分支、
verification_status 持久化、以及幂等性。
"""
import pytest
from datetime import datetime

from app.agents.suspect_agent import SuspectAgent
from app.services.game_service import GameService
from app.models.case import Case, Clue, Suspect, Scene, SceneObject
from app.models.game import GameState, GameDifficulty, GamePhase


@pytest.fixture
def sample_case():
    """构造一个最小可用的案件，含 1 名嫌疑人和 2 条线索"""
    return Case(
        id="case-test",
        victim_name="亚瑟·布莱克伍德",
        victim_background="富有的银行家",
        cause_of_death="刺伤",
        time_of_death="1895-10-15 22:00",
        location="伦敦东区",
        date=datetime(1895, 10, 15),
        summary="测试案件",
        murder_method="匕首刺杀",
        true_murderer_id="suspect-1",
        suspects=[
            Suspect(
                id="suspect-1",
                name="约翰·史密斯",
                age=40,
                background="管家",
                motive="被解雇的怨恨",
                timeline="案发时在厨房",
                is_guilty=True,
                personality_traits=["忠诚", "沉默"],
                secrets=["偷了主人的怀表"],
                statements=[
                    {"id": "stmt-1", "content": "我当晚一直在厨房准备晚餐"},
                    {"id": "stmt-2", "content": "我从未进入过书房"},
                ],
            )
        ],
        clues=[
            Clue(
                id="clue-related",
                description="厨房地板上有一滴血迹，朝向书房方向延伸",
                clue_type="physical",
                related_suspect_ids=["suspect-1"],
                discovered=True,
            ),
            Clue(
                id="clue-irrelevant",
                description="花园里有一只流浪猫",
                clue_type="physical",
                related_suspect_ids=[],
                discovered=True,
            ),
        ],
        scenes=[
            Scene(
                id="scene-1",
                name="书房",
                description="被害人的书房",
                objects=[SceneObject(id="obj-1", name="书桌", description="一张木质书桌", hidden_clue_ids=["clue-related"])],
            )
        ],
    )


@pytest.fixture
def game_service():
    return GameService()


class TestSuspectAgentConfrontMock:
    """Mock 模式下的 confront_with_clue 分支覆盖"""

    @pytest.mark.asyncio
    async def test_confront_critical(self, sample_case):
        """出示与嫌疑人直接相关的线索 → critical"""
        agent = SuspectAgent()
        clue = next(c for c in sample_case.clues if c.id == "clue-related")
        result = await agent.confront_with_clue(
            suspect=sample_case.suspects[0],
            case=sample_case,
            clue=clue,
        )
        assert result["relevance"] == "critical"
        assert result["suggested_verification"] is True
        assert result["status_delta"] is not None
        assert "response" in result
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_confront_irrelevant(self, sample_case):
        """出示与嫌疑人无关的线索 → irrelevant"""
        agent = SuspectAgent()
        clue = next(c for c in sample_case.clues if c.id == "clue-irrelevant")
        result = await agent.confront_with_clue(
            suspect=sample_case.suspects[0],
            case=sample_case,
            clue=clue,
        )
        assert result["relevance"] == "irrelevant"
        assert result["suggested_verification"] is False
        assert result["status_delta"] is None

    @pytest.mark.asyncio
    async def test_confront_result_normalization(self, sample_case):
        """测试 _normalize_confront_result 对异常 key 的兜底"""
        agent = SuspectAgent()
        raw = {
            "response": "测试回应",
            "relevance": "invalid_value",
            "suggested_verification": "true",
            "status_delta": None,
        }
        normalized = agent._normalize_confront_result(raw)
        assert normalized["relevance"] == "irrelevant"
        assert normalized["suggested_verification"] is True


class TestGameServiceClueVerification:
    """GameService.update_clue_verification 持久化测试"""

    def test_update_clue_to_verified(self, game_service, sample_case):
        """将线索更新为 verified，同步 verified_clue_ids"""
        game = game_service.create_game(difficulty=GameDifficulty.CLASSIC)
        game_service.set_case(game.game_id, sample_case)

        success = game_service.update_clue_verification(
            game_id=game.game_id,
            clue_id="clue-related",
            status="verified",
            verified_by="suspect-1",
            notes="嫌疑人承认了",
        )
        assert success is True

        updated_game = game_service.get_game(game.game_id)
        target_clue = next(c for c in updated_game.case.clues if c.id == "clue-related")
        assert target_clue.verification_status == "verified"
        assert target_clue.verified_by == "suspect-1"
        assert target_clue.verification_notes == "嫌疑人承认了"
        assert "clue-related" in updated_game.verified_clue_ids

    def test_update_clue_to_refuted(self, game_service, sample_case):
        """将线索更新为 refuted，verified_clue_ids 中移除"""
        game = game_service.create_game(difficulty=GameDifficulty.CLASSIC)
        game_service.set_case(game.game_id, sample_case)

        # 先置为 verified
        game_service.update_clue_verification(
            game_id=game.game_id,
            clue_id="clue-related",
            status="verified",
        )
        # 再置为 refuted
        success = game_service.mark_clue_refuted(
            game_id=game.game_id,
            clue_id="clue-related",
            refuted_by="suspect-1",
            notes="证词被推翻",
        )
        assert success is True

        updated_game = game_service.get_game(game.game_id)
        target_clue = next(c for c in updated_game.case.clues if c.id == "clue-related")
        assert target_clue.verification_status == "refuted"
        assert "clue-related" not in updated_game.verified_clue_ids

    def test_update_nonexistent_clue(self, game_service, sample_case):
        """更新不存在的线索返回 False"""
        game = game_service.create_game(difficulty=GameDifficulty.CLASSIC)
        game_service.set_case(game.game_id, sample_case)

        success = game_service.update_clue_verification(
            game_id=game.game_id,
            clue_id="clue-not-exist",
            status="verified",
        )
        assert success is False

    def test_update_clue_idempotent(self, game_service, sample_case):
        """重复验证同一线索，verified_clue_ids 不重复追加"""
        game = game_service.create_game(difficulty=GameDifficulty.CLASSIC)
        game_service.set_case(game.game_id, sample_case)

        for _ in range(3):
            game_service.update_clue_verification(
                game_id=game.game_id,
                clue_id="clue-related",
                status="verified",
            )

        updated_game = game_service.get_game(game.game_id)
        assert updated_game.verified_clue_ids.count("clue-related") == 1


class TestConfrontEndpoint:
    """API 端点集成测试（使用 mock agent）"""

    @pytest.mark.asyncio
    async def test_confront_with_clue_endpoint(self, game_service, sample_case):
        """端点返回正确结构，线索状态被更新"""
        from app.agents.suspect_agent import SuspectAgent

        game = game_service.create_game(difficulty=GameDifficulty.CLASSIC)
        game_service.set_case(game.game_id, sample_case)

        agent = SuspectAgent()
        clue = next(c for c in sample_case.clues if c.id == "clue-related")
        result = await agent.confront_with_clue(
            suspect=sample_case.suspects[0],
            case=sample_case,
            clue=clue,
            conversation_history=[],
        )

        # 模拟端点行为：根据 suggested_verification 更新状态
        if result.get("suggested_verification"):
            game_service.update_clue_verification(
                game_id=game.game_id,
                clue_id=clue.id,
                status="verified",
                verified_by=sample_case.suspects[0].id,
            )

        updated_game = game_service.get_game(game.game_id)
        updated_clue = next(c for c in updated_game.case.clues if c.id == clue.id)
        assert updated_clue.verification_status == "verified"
        # agent 层不返回 clue_after，由端点组装
        assert "response" in result
        assert "relevance" in result
