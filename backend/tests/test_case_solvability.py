"""
测试案件可解性校验与 statements 生成逻辑

覆盖 P5 阶段：
- 可解性校验通过/失败场景
- 弱绑定约束校验
- fallback statements 结构
"""

import pytest
from datetime import datetime
from app.agents.case_generator_agent import CaseGeneratorAgent
from app.models.case import Case, Suspect, Clue, SuspectStatement


@pytest.fixture
def agent():
    """提供 CaseGeneratorAgent 实例"""
    return CaseGeneratorAgent()


@pytest.fixture(autouse=True)
def enable_solvability_validation(monkeypatch):
    """所有测试中默认启用可解性校验开关，并清空 api_key 确保走 mock 路径"""
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), "enable_solvability_validation", True)
    monkeypatch.setattr(get_settings(), "openai_api_key", "")


def _make_valid_case() -> Case:
    """构造一个满足可解性约束的测试案件"""
    clues = [
        Clue(id="clue-1", description="信件残片", clue_type="physical", related_suspect_ids=["suspect-1"]),
        Clue(id="clue-2", description="抽屉撬痕", clue_type="physical", related_suspect_ids=["suspect-1", "suspect-2"]),
        Clue(id="clue-3", description="泥渍", clue_type="physical", related_suspect_ids=["suspect-2"]),
        Clue(id="clue-4", description="拖拽痕迹", clue_type="physical", related_suspect_ids=["suspect-1"]),
        Clue(id="clue-5", description="烛台", clue_type="physical", related_suspect_ids=["suspect-1", "suspect-2", "suspect-3"]),
    ]
    suspects = [
        Suspect(
            id="suspect-1",
            name="真凶",
            age=40,
            background="背景",
            motive="动机",
            timeline="时间线",
            is_guilty=True,
            statements=[
                SuspectStatement(id="s1-1", content="谎言1", is_lie=True, refutable_by_clue_ids=["clue-1"]),
                SuspectStatement(id="s1-2", content="谎言2", is_lie=True, refutable_by_clue_ids=["clue-4"]),
                SuspectStatement(id="s1-3", content="真话", is_lie=False, refutable_by_clue_ids=[]),
            ],
        ),
        Suspect(
            id="suspect-2",
            name="无辜A",
            age=30,
            background="背景",
            motive="动机",
            timeline="时间线",
            is_guilty=False,
            statements=[
                SuspectStatement(id="s2-1", content="真话", is_lie=False, refutable_by_clue_ids=[]),
                SuspectStatement(id="s2-2", content="真话", is_lie=False, refutable_by_clue_ids=[]),
            ],
        ),
        Suspect(
            id="suspect-3",
            name="无辜B",
            age=25,
            background="背景",
            motive="动机",
            timeline="时间线",
            is_guilty=False,
            statements=[
                SuspectStatement(id="s3-1", content="真话", is_lie=False, refutable_by_clue_ids=[]),
                SuspectStatement(id="s3-2", content="真话", is_lie=False, refutable_by_clue_ids=[]),
            ],
        ),
    ]
    return Case(
        id="test-case",
        victim_name="受害者",
        victim_background="背景",
        cause_of_death="中毒",
        time_of_death="昨晚10点",
        location="测试地点",
        date=datetime.utcnow(),
        suspects=suspects,
        clues=clues,
    )


class TestValidateSolvability:
    """可解性校验测试"""

    def test_validate_solvability_pass(self, agent):
        """合法案件：校验通过，返回空列表"""
        case = _make_valid_case()
        errors = agent._validate_solvability(case)
        assert errors == []

    def test_validate_solvability_fails_no_lie_chain(self, agent):
        """没有嫌疑人持有 ≥2 条可反驳谎言：校验失败"""
        case = _make_valid_case()
        # 把真凶的谎言减少到 1 条
        guilty = case.suspects[0]
        guilty.statements = [
            SuspectStatement(id="s1-1", content="谎言1", is_lie=True, refutable_by_clue_ids=["clue-1"]),
            SuspectStatement(id="s1-2", content="真话", is_lie=False, refutable_by_clue_ids=[]),
        ]
        errors = agent._validate_solvability(case)
        assert any("没有嫌疑人持有 ≥2 条可反驳的谎言链" in e for e in errors)

    def test_validate_solvability_fails_guilty_no_lie(self, agent):
        """真凶没有可反驳的谎言：校验失败"""
        case = _make_valid_case()
        guilty = case.suspects[0]
        guilty.statements = [
            SuspectStatement(id="s1-1", content="真话", is_lie=False, refutable_by_clue_ids=[]),
            SuspectStatement(id="s1-2", content="真话", is_lie=False, refutable_by_clue_ids=[]),
        ]
        errors = agent._validate_solvability(case)
        assert any("真凶" in e and "没有可反驳的谎言" in e for e in errors)

    def test_validate_solvability_fails_insufficient_clues(self, agent):
        """被引用的线索不足 2 条：校验失败"""
        case = _make_valid_case()
        # 只保留 1 条被引用的线索
        guilty = case.suspects[0]
        guilty.statements = [
            SuspectStatement(id="s1-1", content="谎言1", is_lie=True, refutable_by_clue_ids=["clue-1"]),
            SuspectStatement(id="s1-2", content="谎言2", is_lie=True, refutable_by_clue_ids=["clue-1"]),
        ]
        errors = agent._validate_solvability(case)
        assert any("被 statements 引用的线索不足 2 条" in e for e in errors)

    def test_validate_solvability_fails_weak_binding_nonexistent_clue(self, agent):
        """refutable_by_clue_ids 指向不存在的 clue：校验失败"""
        case = _make_valid_case()
        guilty = case.suspects[0]
        guilty.statements[0].refutable_by_clue_ids = ["clue-nonexistent"]
        errors = agent._validate_solvability(case)
        assert any("引用了不存在的 clue_id" in e for e in errors)

    def test_validate_solvability_fails_weak_binding_clue_not_related(self, agent):
        """refutable_by_clue_ids 指向的 clue 未关联该嫌疑人：校验失败"""
        case = _make_valid_case()
        guilty = case.suspects[0]
        # clue-3 的 related_suspect_ids 不包含 suspect-1
        guilty.statements[0].refutable_by_clue_ids = ["clue-3"]
        errors = agent._validate_solvability(case)
        assert any("未关联该嫌疑人" in e for e in errors)

    def test_validate_solvability_disabled_flag(self, agent, monkeypatch):
        """enable_solvability_validation=False 时跳过校验"""
        from app.config import get_settings
        monkeypatch.setattr(get_settings(), "enable_solvability_validation", False)
        case = _make_valid_case()
        # 故意破坏案件使其不满足约束
        case.suspects[0].statements = []
        errors = agent._validate_solvability(case)
        assert errors == []


class TestStatementBindings:
    """弱绑定约束校验测试"""

    def test_validate_bindings_pass(self, agent):
        """refutable_by_clue_ids 关联正确"""
        clue_related_map = {
            "clue-1": {"suspect-1"},
            "clue-2": {"suspect-1", "suspect-2"},
        }
        stmt = SuspectStatement(
            id="s1", content="陈述", is_lie=True, refutable_by_clue_ids=["clue-1"]
        )
        assert agent._validate_statement_bindings(stmt, "suspect-1", clue_related_map) is True

    def test_validate_bindings_clue_not_exist(self, agent):
        """clue_id 不存在"""
        clue_related_map = {"clue-1": {"suspect-1"}}
        stmt = SuspectStatement(
            id="s1", content="陈述", is_lie=True, refutable_by_clue_ids=["clue-missing"]
        )
        assert agent._validate_statement_bindings(stmt, "suspect-1", clue_related_map) is False

    def test_validate_bindings_clue_not_related(self, agent):
        """clue 存在但未关联该嫌疑人"""
        clue_related_map = {"clue-1": {"suspect-2"}}
        stmt = SuspectStatement(
            id="s1", content="陈述", is_lie=True, refutable_by_clue_ids=["clue-1"]
        )
        assert agent._validate_statement_bindings(stmt, "suspect-1", clue_related_map) is False

    def test_validate_bindings_empty_refutable(self, agent):
        """refutable_by_clue_ids 为空（真话）"""
        clue_related_map = {"clue-1": {"suspect-1"}}
        stmt = SuspectStatement(
            id="s1", content="陈述", is_lie=False, refutable_by_clue_ids=[]
        )
        assert agent._validate_statement_bindings(stmt, "suspect-1", clue_related_map) is True


class TestFallbackStatements:
    """fallback statements 生成测试"""

    def test_fallback_statements_guilty_has_lies(self, agent):
        """mock fallback：真凶至少有 2 条谎言"""
        case = _make_valid_case()
        suspects = agent._build_fallback_statements(case.suspects, case.clues)
        guilty = next(s for s in suspects if s.is_guilty)
        lie_count = sum(1 for stmt in guilty.statements if stmt.is_lie)
        assert lie_count >= 2, f"真凶谎言数={lie_count}，期望 >=2"

    def test_fallback_statements_weak_binding_valid(self, agent):
        """mock fallback：所有 refutable_by_clue_ids 关联正确"""
        case = _make_valid_case()
        suspects = agent._build_fallback_statements(case.suspects, case.clues)
        clue_related_map = {c.id: set(c.related_suspect_ids) for c in case.clues}
        for s in suspects:
            for stmt in s.statements:
                assert agent._validate_statement_bindings(stmt, s.id, clue_related_map) is True

    def test_fallback_statements_structure(self, agent):
        """mock fallback：每位嫌疑人 2-4 条陈述"""
        case = _make_valid_case()
        suspects = agent._build_fallback_statements(case.suspects, case.clues)
        for s in suspects:
            assert 2 <= len(s.statements) <= 4, f"{s.id} 陈述数={len(s.statements)}"

    def test_fallback_statements_all_suspects_covered(self, agent):
        """mock fallback：所有嫌疑人都被覆盖"""
        case = _make_valid_case()
        suspects = agent._build_fallback_statements(case.suspects, case.clues)
        assert len(suspects) == len(case.suspects)

    def test_fallback_statements_satisfies_solvability(self, agent):
        """mock fallback：生成的 case 满足可解性校验"""
        case = _make_valid_case()
        suspects = agent._build_fallback_statements(case.suspects, case.clues)
        new_case = case.model_copy(update={"suspects": suspects})
        errors = agent._validate_solvability(new_case)
        assert errors == [], f"可解性校验失败: {errors}"


class TestGenerateCaseStatements:
    """generate_case 集成测试（mock 路径）"""

    @pytest.mark.asyncio
    async def test_generate_case_mock_has_statements(self, agent):
        """api_key 缺失时 generate_case 返回的 case 包含 statements"""
        case = await agent.generate_case(difficulty="classic")
        for s in case.suspects:
            assert len(s.statements) >= 2, f"{s.id} 缺少 statements"

    @pytest.mark.asyncio
    async def test_generate_case_mock_satisfies_solvability(self, agent):
        """api_key 缺失时 generate_case 返回的 case 满足可解性"""
        case = await agent.generate_case(difficulty="classic")
        errors = agent._validate_solvability(case)
        assert errors == [], f"可解性校验失败: {errors}"
