"""P4 端到端集成测试 - 完整的线索验证、推理类型、指认流程"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.models.case import Case, Suspect, Clue, Inference, Observation, SuspectStatement
from app.models.game import GameState, GameDifficulty, GamePhase
from app.services.game_service import GameService
from app.agents.oracle_agent import OracleAgent


@pytest.fixture
def game_service():
    return GameService()


@pytest.fixture
def comprehensive_case():
    """P4完整测试用例：包含验证状态、推理类型、难度阈值"""
    return Case(
        id="case_p4",
        victim_name="Sir Henry",
        victim_background="维多利亚时代贵族",
        cause_of_death="poison",
        time_of_death="昨夜 11 点",
        location="书房",
        date=datetime.utcnow(),
        murder_method="在红酒中投毒",
        true_murderer_id="suspect_1",
        suspects=[
            Suspect(
                id="suspect_1",
                name="管家",
                age=50,
                background="服侍爵士二十年",
                motive="债务纠纷",
                timeline="昨晚在酒窖逗留",
                is_guilty=True,
                statements=[
                    SuspectStatement(id="stmt_1", content="我昨晚一直在休息"),
                    SuspectStatement(id="stmt_2", content="我没有进过书房"),
                ]
            ),
            Suspect(
                id="suspect_2",
                name="侄子",
                age=30,
                background="外甥",
                motive="遗产继承",
                timeline="昨晚在客厅",
                is_guilty=False,
                statements=[
                    SuspectStatement(id="stmt_3", content="我整晚都在客厅读书"),
                ]
            ),
        ],
        clues=[
            # 已验证线索
            Clue(
                id="clue_1",
                description="书房有未喝完的红酒",
                clue_type="physical",
                verification_status="verified",
                verification_notes="审讯时管家承认",
                verified_by="suspect_1"
            ),
            # 未验证线索
            Clue(
                id="clue_2",
                description="管家昨晚出现在酒窖",
                clue_type="testimonial",
                verification_status="unverified"
            ),
            Clue(
                id="clue_3",
                description="书房门口有脚印",
                clue_type="forensic",
                verification_status="unverified"
            ),
            Clue(
                id="clue_4",
                description="爵士日记提到对管家不满",
                clue_type="testimonial",
                verification_status="unverified"
            ),
        ],
    )


@pytest.mark.asyncio
async def test_p4_complete_flow_easy_difficulty(game_service, comprehensive_case):
    """P4完整流程测试：简单难度（无推理类型门槛）"""
    # 1. 创建游戏
    game = game_service.create_game(difficulty=GameDifficulty.EASY)
    game.case = comprehensive_case
    game_service._games[game.game_id] = game

    # 2. 验证初始化
    chain = game_service.get_or_create_deduction_chain(game.game_id)

    # 3. 添加观察记录（模拟勘查阶段，至少5条）
    for i, clue in enumerate(comprehensive_case.clues):
        obs = Observation(
            id=f"obs_{i}",
            description=f"发现：{clue.description}",
            location=clue.location or "案发地",
            related_clue_ids=[clue.id]
        )
        chain.observations.append(obs)
    # 补充到5条
    chain.observations.append(Observation(id="obs_extra", description="额外观察", location="走廊"))

    # 4. 模拟审讯阶段：验证线索
    game_service.update_clue_verification(
        game.game_id,
        "clue_2",
        "verified",
        verified_by="suspect_1",
        notes="审讯中管家承认去过酒窖"
    )

    # 5. 添加推理（不同类型）
    fact_inf = Inference(
        id="inf_fact",
        content="根据已验证的红酒和酒窖证据，管家可能是凶手",
        clue_ids=["clue_1", "clue_2"],
        node_type="fact",
        verification_result="correct"
    )

    interrogation_inf = Inference(
        id="inf_interrogation",
        content="在对质中，管家承认在案发时段在酒窖",
        clue_ids=["clue_2"],
        node_type="interrogation",
        verification_result="correct"
    )

    chain.inferences.extend([fact_inf, interrogation_inf])

    # 6. 验证结案就绪（easy 难度无门槛）
    readiness = game_service.check_conclusion_readiness(game.game_id)

    assert readiness["is_ready"] is True
    assert readiness["fact_count"] == 1
    assert readiness["interrogation_count"] == 1
    assert readiness["threshold"] == 0


@pytest.mark.asyncio
async def test_p4_complete_flow_classic_difficulty(game_service, comprehensive_case):
    """P4完整流程测试：经典难度（需要1个interrogation）"""
    game = game_service.create_game(difficulty=GameDifficulty.CLASSIC)
    game.case = comprehensive_case
    game_service._games[game.game_id] = game

    chain = game_service.get_or_create_deduction_chain(game.game_id)

    # 添加观察记录（至少5条）
    for i, clue in enumerate(comprehensive_case.clues):
        obs = Observation(
            id=f"obs_{i}",
            description=f"发现：{clue.description}",
            location=clue.location or "案发地",
            related_clue_ids=[clue.id]
        )
        chain.observations.append(obs)
    chain.observations.append(Observation(id="obs_extra", description="额外观察", location="走廊"))

    # 仅添加 fact 推理（不满足条件）
    fact_inf = Inference(
        id="inf_fact_1",
        content="根据物证分析，管家可能是凶手",
        clue_ids=["clue_1"],
        node_type="fact",
        verification_result="correct"
    )
    chain.inferences.append(fact_inf)

    readiness = game_service.check_conclusion_readiness(game.game_id)
    assert readiness["is_ready"] is False  # 需要 1 个 interrogation，但只有 fact
    assert readiness["threshold"] == 1

    # 添加 interrogation 推理（满足条件）
    interrogation_inf = Inference(
        id="inf_int_1",
        content="在审讯中，管家承认有作案动机",
        clue_ids=["clue_4"],
        node_type="interrogation",
        verification_result="correct"
    )
    chain.inferences.append(interrogation_inf)

    readiness = game_service.check_conclusion_readiness(game.game_id)
    assert readiness["is_ready"] is True  # 现在满足条件


@pytest.mark.asyncio
async def test_p4_complete_flow_hardcore_difficulty(game_service, comprehensive_case):
    """P4完整流程测试：硬核难度（需要2个interrogation）"""
    game = game_service.create_game(difficulty=GameDifficulty.HARDCORE)
    game.case = comprehensive_case
    game_service._games[game.game_id] = game

    chain = game_service.get_or_create_deduction_chain(game.game_id)

    # 添加观察
    for i in range(5):
        obs = Observation(
            id=f"obs_{i}",
            description=f"观察 {i}",
            location="案发地"
        )
        chain.observations.append(obs)

    # 添加 1 fact + 1 interrogation（不满足条件）
    chain.inferences.extend([
        Inference(id="inf_1", content="事实推理", clue_ids=[], node_type="fact", verification_result="correct"),
        Inference(id="inf_2", content="对质推理", clue_ids=[], node_type="interrogation", verification_result="correct"),
    ])

    readiness = game_service.check_conclusion_readiness(game.game_id)
    assert readiness["is_ready"] is False  # 需要 2 个
    assert readiness["threshold"] == 2

    # 再添加 1 混合推理（mixed 计一半，所以现在有 1.5）
    chain.inferences.append(
        Inference(id="inf_3", content="混合推理", clue_ids=[], node_type="mixed", verification_result="correct")
    )

    readiness = game_service.check_conclusion_readiness(game.game_id)
    assert readiness["is_ready"] is False  # 1.5 < 2，仍不满足

    # 再添加 1 interrogation（现在有 2 个 + 0.5）
    chain.inferences.append(
        Inference(id="inf_4", content="对质推理2", clue_ids=[], node_type="interrogation", verification_result="correct")
    )

    readiness = game_service.check_conclusion_readiness(game.game_id)
    assert readiness["is_ready"] is True  # 现在满足条件


@pytest.mark.asyncio
async def test_p4_unverified_clue_verdict_downgrade(game_service, comprehensive_case):
    """P4严格模式测试：未验证线索导致verdict降级"""
    oracle = OracleAgent()

    # 仅使用未验证线索
    unverified_clues = [c for c in comprehensive_case.clues if c.verification_status == "unverified"]

    # 模拟 LLM 返回 correct，但严格模式下应该降级
    with patch('app.agents.oracle_agent.invoke_with_retry') as mock_invoke:
        mock_invoke.return_value = {
            "verdict": "correct",
            "confidence": 0.8,
            "explanation": "推理逻辑清晰",
            "node_type": "mixed"
        }

        # 严格模式：未验证线索应该导致降级
        result = await oracle.verify_inference(
            case=comprehensive_case,
            clues=unverified_clues,
            conclusion="根据未验证线索推断管家是凶手",
            enable_strict_oracle=True
        )

        assert result["verdict"] == "partial"  # 降级为 partial
        assert "验证" in result["explanation"]


@pytest.mark.asyncio
async def test_p4_verified_clue_full_credit(game_service, comprehensive_case):
    """P4正面测试：已验证线索获得正确评估"""
    oracle = OracleAgent()

    # 仅使用已验证线索
    verified_clues = [c for c in comprehensive_case.clues if c.verification_status == "verified"]

    with patch('app.agents.oracle_agent.invoke_with_retry') as mock_invoke:
        mock_invoke.return_value = {
            "verdict": "correct",
            "confidence": 0.9,
            "explanation": "基于已验证物证的可靠推理",
            "node_type": "fact"
        }

        # 严格模式：已验证线索保持 correct
        result = await oracle.verify_inference(
            case=comprehensive_case,
            clues=verified_clues,
            conclusion="根据已验证的红酒证据，推断管家投毒",
            enable_strict_oracle=True
        )

        assert result["verdict"] == "correct"  # 保持 correct
        assert result["node_type"] == "fact"


def test_p4_clue_verification_status_persistence(game_service, comprehensive_case):
    """P4数据一致性测试：验证状态持久化"""
    game = game_service.create_game(difficulty=GameDifficulty.CLASSIC)
    game.case = comprehensive_case
    game_service._games[game.game_id] = game

    # 检查初始状态
    initial_clue = game.case.clues[0]
    assert initial_clue.verification_status == "verified"

    # 更新验证状态
    game_service.update_clue_verification(
        game.game_id,
        "clue_2",
        "verified",
        verified_by="suspect_1",
        notes="审讯确认"
    )

    # 验证更新已持久化
    updated_clue = game.case.clues[1]
    assert updated_clue.verification_status == "verified"
    assert updated_clue.verification_notes == "审讯确认"
    assert updated_clue.verified_by == "suspect_1"


def test_p4_multiple_difficulty_thresholds(game_service, comprehensive_case):
    """P4难度系统测试：验证三种难度的阈值"""
    difficulties = [
        (GameDifficulty.EASY, 0),
        (GameDifficulty.CLASSIC, 1),
        (GameDifficulty.HARDCORE, 2),
    ]

    for difficulty, expected_threshold in difficulties:
        game = game_service.create_game(difficulty=difficulty)
        game.case = comprehensive_case
        game_service._games[game.game_id] = game

        readiness = game_service.check_conclusion_readiness(game.game_id)
        assert readiness["threshold"] == expected_threshold, f"Difficulty {difficulty} should have threshold {expected_threshold}"
