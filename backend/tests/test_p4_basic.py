"""P4 基础功能测试"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime

from app.models.case import Case, Suspect, Clue, Inference
from app.models.game import GameState, GameDifficulty, GamePhase
from app.services.game_service import GameService


@pytest.fixture
def game_service():
    return GameService()


@pytest.fixture
def sample_case():
    return Case(
        id="c1",
        victim_name="Sir Henry",
        victim_background="维多利亚时代贵族",
        cause_of_death="poison",
        time_of_death="昨夜 11 点",
        location="书房",
        date=datetime.utcnow(),
        murder_method="在红酒中投毒",
        true_murderer_id="s1",
        suspects=[
            Suspect(id="s1", name="管家", age=50, background="服侍爵士二十年",
                    motive="债务纠纷", timeline="昨晚在酒窖逗留", is_guilty=True),
            Suspect(id="s2", name="侄子", age=30, background="外甥",
                    motive="遗产继承", timeline="昨晚在客厅", is_guilty=False),
        ],
        clues=[
            Clue(
                id="cl1", description="书房有未喝完的红酒", clue_type="physical",
                verification_status="verified", verification_notes="审讯时确认"
            ),
            Clue(
                id="cl2", description="管家昨晚出现在酒窖", clue_type="testimonial",
                verification_status="unverified"
            ),
        ],
    )


def test_check_conclusion_readiness_easy_mode(game_service, sample_case):
    """测试简单难度不需要推理类型门槛"""
    game = game_service.create_game(difficulty=GameDifficulty.EASY)
    game.case = sample_case
    game_service._games[game.game_id] = game

    # 添加一些观察记录（至少5条）
    chain = game_service.get_or_create_deduction_chain(game.game_id)
    for i in range(5):
        from app.models.case import Observation
        obs = Observation(
            id=f"obs{i}", description=f"观察 {i}",
            location="书房"
        )
        chain.observations.append(obs)

    # 添加一条推理
    inf = Inference(
        id="inf1", content="推理1", node_type="fact"
    )
    chain.inferences.append(inf)

    readiness = game_service.check_conclusion_readiness(game.game_id)

    assert readiness["is_ready"] is True
    assert readiness["threshold"] == 0


def test_check_conclusion_readiness_classic_mode(game_service, sample_case):
    """测试经典难度需要1个interrogation"""
    game = game_service.create_game(difficulty=GameDifficulty.CLASSIC)
    game.case = sample_case
    game_service._games[game.game_id] = game

    chain = game_service.get_or_create_deduction_chain(game.game_id)

    # 添加观察记录
    for i in range(5):
        from app.models.case import Observation
        obs = Observation(
            id=f"obs{i}", description=f"观察 {i}",
            location="书房"
        )
        chain.observations.append(obs)

    # 添加一条fact推理（不满足条件）
    inf1 = Inference(
        id="inf1", content="推理1", node_type="fact"
    )
    chain.inferences.append(inf1)

    readiness = game_service.check_conclusion_readiness(game.game_id)
    assert readiness["is_ready"] is False
    assert readiness["interrogation_count"] == 0
    assert readiness["threshold"] == 1

    # 添加一条interrogation推理（满足条件）
    inf2 = Inference(
        id="inf2", content="推理2", node_type="interrogation"
    )
    chain.inferences.append(inf2)

    readiness = game_service.check_conclusion_readiness(game.game_id)
    assert readiness["is_ready"] is True
    assert readiness["interrogation_count"] == 1


def test_clue_verification_status_output(sample_case):
    """测试线索验证状态在格式化输出中正确显示"""
    from app.agents.oracle_agent import _format_clues_block

    output = _format_clues_block(sample_case.clues)

    assert "[Status: verified]" in output
    assert "[Status: unverified]" in output
    assert "审讯时确认" in output  # verification_notes
