"""
章节 8.2 - SceneAgent 单元测试
验证：search 方法 JSON schema 正确、fallback 降级、clue_candidates 解析
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.models.case import Case, Suspect, Clue, Scene, SceneObject
from app.agents.scene_agent import SceneAgent


@pytest.fixture
def fixture_scene():
    return Scene(
        id="scene_001",
        name="书房",
        description="高高的红木书架，壁炉中余烬未熄，案桌上散落着几封未拆的信件。",
        npc_persona="沉默的管家，对死者忠诚",
        objects=[
            SceneObject(
                id="obj_001",
                name="办公桌",
                description="胡桃木办公桌，抽屉半开",
                hidden_clue_ids=["cl1"],
                search_hints=["仔细查看抽屉", "翻动桌上的纸张"],
            ),
            SceneObject(
                id="obj_002",
                name="壁炉",
                description="壁炉旁有一把扶手椅，炉灰中似乎有残纸",
                hidden_clue_ids=[],
                search_hints=["检查炉灰"],
            ),
        ],
    )


@pytest.fixture
def fixture_case(fixture_scene):
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
        ],
        clues=[
            Clue(id="cl1", description="书房有未喝完的红酒", clue_type="physical"),
        ],
        scenes=[fixture_scene],
    )


@pytest.mark.asyncio
async def test_search_returns_correct_schema(fixture_scene, fixture_case):
    """验证 search 返回结构符合预期 schema"""
    agent = SceneAgent.__new__(SceneAgent)
    agent.temperature = 0.5
    agent.llm = MagicMock()

    mock_result = {
        "narrative": "管家缓缓走近，指着半开的抽屉低声说：'阁下若有兴趣，或许可以查看那封未完成的信。'",
        "matched_object_ids": ["obj_001"],
        "clue_candidates": [],
    }

    with patch("app.agents.scene_agent.invoke_with_retry", new=AsyncMock(return_value=mock_result)):
        result = await agent.search(
            scene=fixture_scene,
            case=fixture_case,
            query="查看办公桌",
            history=[],
        )

    assert "narrative" in result
    assert "matched_object_ids" in result
    assert "clue_candidates" in result
    assert result["matched_object_ids"] == ["obj_001"]


@pytest.mark.asyncio
async def test_search_with_clue_candidates(fixture_scene, fixture_case):
    """验证 clue_candidates 非空时正确解析"""
    agent = SceneAgent.__new__(SceneAgent)
    agent.temperature = 0.5
    agent.llm = MagicMock()

    mock_result = {
        "narrative": "抽屉里有一封措辞急迫的信件，落款日期是案发前夕。",
        "matched_object_ids": ["obj_001"],
        "clue_candidates": [
            {"object_id": "obj_001", "suggested_clue_id": "cl1", "hint": "信中提及一笔未偿还的债务"}
        ],
    }

    with patch("app.agents.scene_agent.invoke_with_retry", new=AsyncMock(return_value=mock_result)):
        result = await agent.search(
            scene=fixture_scene,
            case=fixture_case,
            query="仔细查看抽屉",
            history=[{"role": "user", "content": "查看办公桌"}, {"role": "assistant", "content": "桌上有几封信"}],
        )

    assert len(result["clue_candidates"]) == 1
    candidate = result["clue_candidates"][0]
    assert "object_id" in candidate
    assert "hint" in candidate


@pytest.mark.asyncio
async def test_search_fallback_on_error(fixture_scene, fixture_case):
    """invoke_with_retry 异常时 fallback 降级返回正确结构"""
    agent = SceneAgent.__new__(SceneAgent)
    agent.temperature = 0.5
    agent.llm = MagicMock()

    async def fake_invoke(chain, inputs, fallback_fn=None, **kwargs):
        return fallback_fn()

    with patch("app.agents.scene_agent.invoke_with_retry", side_effect=fake_invoke):
        result = await agent.search(
            scene=fixture_scene,
            case=fixture_case,
            query="查看壁炉",
            history=[],
        )

    assert result["narrative"] == "（场景陷入寂静，似乎暂时听不到任何回应）"
    assert result["matched_object_ids"] == []
    assert result["clue_candidates"] == []


@pytest.mark.asyncio
async def test_search_with_conversation_history(fixture_scene, fixture_case):
    """验证历史对话截取最近 6 轮正常工作"""
    agent = SceneAgent.__new__(SceneAgent)
    agent.temperature = 0.5
    agent.llm = MagicMock()

    history = [{"role": "user", "content": f"问题{i}"} for i in range(10)]

    mock_result = {
        "narrative": "管家点了点头。",
        "matched_object_ids": [],
        "clue_candidates": [],
    }

    captured_inputs = {}

    async def fake_invoke(chain, inputs, **kwargs):
        captured_inputs.update(inputs)
        return mock_result

    with patch("app.agents.scene_agent.invoke_with_retry", side_effect=fake_invoke):
        await agent.search(
            scene=fixture_scene,
            case=fixture_case,
            query="有什么异常吗",
            history=history,
        )

    # 历史对话应只保留最近 6 轮
    history_block = captured_inputs.get("history_block", "")
    assert history_block.count("问题") <= 6
