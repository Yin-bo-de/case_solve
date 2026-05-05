"""
测试嫌疑人状态机规则

覆盖 P3 阶段状态迁移：
- calm + critical → broken
- calm + related（累计≥1）→ pressured
- pressured + critical → broken
- pressured + related → pressured（保持）
- broken → broken（终态）
- irrelevant 不触发任何迁移
"""

import pytest
from app.services.game_service import GameService
from app.models.game import GameState, GameDifficulty, GamePhase
from app.models.case import Case


@pytest.fixture
def game_service():
    """提供独立的 GameService 实例"""
    return GameService()


@pytest.fixture
def game_id(game_service):
    """创建一个测试游戏并返回 game_id"""
    game = game_service.create_game(difficulty=GameDifficulty.CLASSIC)
    # 给游戏设置一个简单案件，确保 case 存在
    from datetime import datetime
    case = Case(
        id="test-case-001",
        victim_name="测试受害者",
        victim_background="测试背景",
        cause_of_death="中毒",
        time_of_death="昨晚10点",
        location="测试地点",
        date=datetime.utcnow(),
    )
    game.case = case
    return game.game_id


class TestSuspectStateMachine:
    """嫌疑人状态机规则测试"""

    def test_calm_to_broken_on_critical(self, game_service, game_id):
        """calm + critical → broken"""
        old, new, changed = game_service.transition_suspect_state(
            game_id, "suspect-1", "critical"
        )
        assert old == "calm"
        assert new == "broken"
        assert changed is True

    def test_calm_to_pressured_on_related(self, game_service, game_id):
        """calm + related（第1次）→ pressured"""
        old, new, changed = game_service.transition_suspect_state(
            game_id, "suspect-2", "related"
        )
        assert old == "calm"
        assert new == "pressured"
        assert changed is True

    def test_pressured_stays_on_second_related(self, game_service, game_id):
        """pressured + related（第2次）→ pressured（保持）"""
        # 先升级到 pressured
        game_service.transition_suspect_state(game_id, "suspect-3", "related")
        game = game_service.get_game(game_id)
        assert game.suspect_states["suspect-3"] == "pressured"

        # 第二次 related，应保持 pressured
        old, new, changed = game_service.transition_suspect_state(
            game_id, "suspect-3", "related"
        )
        assert old == "pressured"
        assert new == "pressured"
        assert changed is False

    def test_pressured_to_broken_on_critical(self, game_service, game_id):
        """pressured + critical → broken"""
        # 先升级到 pressured
        game_service.transition_suspect_state(game_id, "suspect-4", "related")
        assert game_service.get_game(game_id).suspect_states["suspect-4"] == "pressured"

        # critical 直接升级到 broken
        old, new, changed = game_service.transition_suspect_state(
            game_id, "suspect-4", "critical"
        )
        assert old == "pressured"
        assert new == "broken"
        assert changed is True

    def test_broken_remains_terminal_on_related(self, game_service, game_id):
        """broken + related → broken（终态不回退）"""
        game_service.get_game(game_id).suspect_states["suspect-5"] = "broken"

        old, new, changed = game_service.transition_suspect_state(
            game_id, "suspect-5", "related"
        )
        assert old == "broken"
        assert new == "broken"
        assert changed is False

    def test_broken_remains_terminal_on_critical(self, game_service, game_id):
        """broken + critical → broken（终态不回退）"""
        game_service.get_game(game_id).suspect_states["suspect-6"] = "broken"

        old, new, changed = game_service.transition_suspect_state(
            game_id, "suspect-6", "critical"
        )
        assert old == "broken"
        assert new == "broken"
        assert changed is False

    def test_irrelevant_does_not_trigger_any_transition(self, game_service, game_id):
        """irrelevant 在任何状态下都不触发迁移"""
        # calm + irrelevant
        old, new, changed = game_service.transition_suspect_state(
            game_id, "suspect-7", "irrelevant"
        )
        assert old == "calm"
        assert new == "calm"
        assert changed is False

        # pressured + irrelevant
        game_service.get_game(game_id).suspect_states["suspect-8"] = "pressured"
        old, new, changed = game_service.transition_suspect_state(
            game_id, "suspect-8", "irrelevant"
        )
        assert old == "pressured"
        assert new == "pressured"
        assert changed is False

        # broken + irrelevant
        game_service.get_game(game_id).suspect_states["suspect-9"] = "broken"
        old, new, changed = game_service.transition_suspect_state(
            game_id, "suspect-9", "irrelevant"
        )
        assert old == "broken"
        assert new == "broken"
        assert changed is False

    def test_counter_increments_on_related(self, game_service, game_id):
        """related 累计计数器正确递增"""
        key = f"{game_id}:suspect-counter"
        assert game_service._suspect_relevance_counter.get(key, 0) == 0

        game_service.transition_suspect_state(game_id, "suspect-counter", "related")
        assert game_service._suspect_relevance_counter.get(key, 0) == 1

        game_service.transition_suspect_state(game_id, "suspect-counter", "related")
        assert game_service._suspect_relevance_counter.get(key, 0) == 2

    def test_game_not_found_returns_calm(self, game_service):
        """游戏不存在时返回默认值 calm，不报错"""
        old, new, changed = game_service.transition_suspect_state(
            "non-existent-game", "suspect-x", "critical"
        )
        assert old == "calm"
        assert new == "calm"
        assert changed is False
