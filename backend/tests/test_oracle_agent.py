"""
章节 8.1 - OracleAgent 单元测试
验证：JSON schema 正确、fallback 降级路径、指控判定逻辑、P4 严格模式
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.models.case import Case, Suspect, Clue, Inference
from app.agents.oracle_agent import OracleAgent


@pytest.fixture
def fixture_case():
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
            Suspect(id="s1", name="管家", age=50, background="服侍爵士二十年", motive="债务纠纷", timeline="昨晚在酒窖逗留", is_guilty=True),
            Suspect(id="s2", name="侄子", age=30, background="外甥", motive="遗产继承", timeline="昨晚在客厅", is_guilty=False),
        ],
        clues=[
            Clue(id="cl1", description="书房有未喝完的红酒", clue_type="physical"),
            Clue(id="cl2", description="管家昨晚出现在酒窖", clue_type="testimonial"),
        ],
    )


@pytest.mark.asyncio
async def test_verify_inference_returns_schema(fixture_case):
    """验证 verify_inference 使用 fallback 时返回正确的 schema"""
    oracle = OracleAgent.__new__(OracleAgent)
    oracle.temperature = 0.2
    oracle.llm = MagicMock()

    fallback_result = {
        "verdict": "partial",
        "score": 0.5,
        "explanation": "裁决官暂时不在，请稍后再试。",
        "missing_links": [],
        "misused_clues": [],
    }

    with patch("app.agents.oracle_agent.invoke_with_retry", new=AsyncMock(return_value=fallback_result)):
        result = await oracle.verify_inference(
            case=fixture_case,
            clues=fixture_case.clues,
            conclusion="管家在红酒中下毒",
        )

    assert "verdict" in result
    assert result["verdict"] in ("correct", "wrong", "partial")
    assert "score" in result
    assert "explanation" in result
    assert "missing_links" in result
    assert "misused_clues" in result


@pytest.mark.asyncio
async def test_verify_accusation_fallback_correct_suspect(fixture_case):
    """fallback 路径下，指认正确真凶时 is_correct 应为 True"""
    oracle = OracleAgent.__new__(OracleAgent)
    oracle.temperature = 0.2
    oracle.llm = MagicMock()

    # 模拟 invoke_with_retry 直接返回 fallback_fn() 的结果
    async def fake_invoke(chain, inputs, fallback_fn=None, **kwargs):
        return fallback_fn()

    with patch("app.agents.oracle_agent.invoke_with_retry", side_effect=fake_invoke):
        result = await oracle.verify_accusation(
            case=fixture_case,
            suspect_id="s1",  # 正确真凶
            reasoning_records=[],
        )

    assert result["is_correct"] is True


@pytest.mark.asyncio
async def test_verify_accusation_fallback_wrong_suspect(fixture_case):
    """fallback 路径下，指认错误嫌疑人时 is_correct 应为 False"""
    oracle = OracleAgent.__new__(OracleAgent)
    oracle.temperature = 0.2
    oracle.llm = MagicMock()

    async def fake_invoke(chain, inputs, fallback_fn=None, **kwargs):
        return fallback_fn()

    with patch("app.agents.oracle_agent.invoke_with_retry", side_effect=fake_invoke):
        result = await oracle.verify_accusation(
            case=fixture_case,
            suspect_id="s2",  # 错误嫌疑人
            reasoning_records=[],
        )

    assert result["is_correct"] is False


@pytest.mark.asyncio
async def test_verify_inference_with_reasoning_records(fixture_case):
    """传入含 verification_result 的推理记录时，verify_accusation schema 正确"""
    oracle = OracleAgent.__new__(OracleAgent)
    oracle.temperature = 0.2
    oracle.llm = MagicMock()

    record = Inference(
        id="inf1",
        content="管家在红酒中下毒",
        verification_result="correct",
        confidence=0.9,
    )

    expected = {
        "is_correct": True,
        "score": 0.9,
        "verdict_explanation": "正确指认了凶手",
        "key_evidence_used": ["cl1", "cl2"],
        "missing_critical_evidence": [],
    }

    with patch("app.agents.oracle_agent.invoke_with_retry", new=AsyncMock(return_value=expected)):
        result = await oracle.verify_accusation(
            case=fixture_case,
            suspect_id="s1",
            reasoning_records=[record],
        )

    assert "is_correct" in result
    assert "verdict_explanation" in result
    assert "key_evidence_used" in result
    assert "missing_critical_evidence" in result


@pytest.mark.asyncio
async def test_verify_inference_unverified_clue_downgrade(fixture_case):
    """P4: 严格模式下，使用未验证线索的推理 verdict 降级为 partial"""
    oracle = OracleAgent.__new__(OracleAgent)
    oracle.temperature = 0.2
    oracle.llm = MagicMock()

    # 所有线索都是 unverified
    for c in fixture_case.clues:
        c.verification_status = "unverified"

    with patch("app.agents.oracle_agent.invoke_with_retry", new=AsyncMock(return_value={
        "verdict": "correct",
        "score": 0.9,
        "explanation": "推理逻辑清晰",
        "node_type": "mixed",
    })):
        result = await oracle.verify_inference(
            case=fixture_case,
            clues=fixture_case.clues,
            conclusion="管家在红酒中下毒",
            enable_strict_oracle=True,
        )

    assert result["verdict"] == "partial"
    assert "验证" in result["explanation"]


@pytest.mark.asyncio
async def test_verify_inference_verified_clue_keeps_correct(fixture_case):
    """P4: 严格模式下，使用已验证线索的推理保持 correct"""
    oracle = OracleAgent.__new__(OracleAgent)
    oracle.temperature = 0.2
    oracle.llm = MagicMock()

    # 所有线索都是 verified
    for c in fixture_case.clues:
        c.verification_status = "verified"

    with patch("app.agents.oracle_agent.invoke_with_retry", new=AsyncMock(return_value={
        "verdict": "correct",
        "score": 0.9,
        "explanation": "基于已验证物证的可靠推理",
        "node_type": "fact",
    })):
        result = await oracle.verify_inference(
            case=fixture_case,
            clues=fixture_case.clues,
            conclusion="管家在红酒中下毒",
            enable_strict_oracle=True,
        )

    assert result["verdict"] == "correct"
    assert result["node_type"] == "fact"
