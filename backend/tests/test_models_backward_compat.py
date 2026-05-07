"""
P1 向后兼容测试：验证旧 JSON（不含新字段）能正常反序列化、默认值正确。
"""
import json
from datetime import datetime

from app.models.case import Case, Clue, Suspect, Inference, SuspectStatement
from app.models.game import GameState, GameDifficulty, GamePhase


class TestClueBackwardCompat:
    """Clue 模型旧 JSON 反序列化兼容"""

    def test_old_clue_without_verification_fields(self):
        """旧 JSON 不含 verification_status / verification_notes / verified_by"""
        old_json = {
            "id": "clue-1",
            "description": "一把沾血的匕首",
            "clue_type": "physical",
            "location": "书房",
            "related_suspect_ids": ["suspect-1"],
            "discovered": True,
            "discovery_notes": None,
            "obviousness": 0.7,
            "user_label": None,
            "source_type": "scene",
            "source_ref": "scene-1",
            "quoted_text": None,
            "user_generated": False,
            "investigation_hint": None,
            "chain_next_clue_index": None,
        }
        clue = Clue(**old_json)
        assert clue.verification_status == "unverified"
        assert clue.verification_notes is None
        assert clue.verified_by is None

    def test_clue_with_new_fields(self):
        """新 JSON 含全部字段"""
        new_json = {
            "id": "clue-2",
            "description": "一封威胁信",
            "clue_type": "testimonial",
            "verification_status": "verified",
            "verification_notes": "嫌疑人承认了信件的真实性",
            "verified_by": "suspect-1",
        }
        clue = Clue(**new_json)
        assert clue.verification_status == "verified"
        assert clue.verification_notes == "嫌疑人承认了信件的真实性"
        assert clue.verified_by == "suspect-1"


class TestSuspectBackwardCompat:
    """Suspect 模型旧 JSON 反序列化兼容"""

    def test_old_suspect_without_statements(self):
        """旧 JSON 不含 statements 字段"""
        old_json = {
            "id": "suspect-1",
            "name": "约翰·史密斯",
            "age": 35,
            "background": "被害人的商业伙伴",
            "motive": "债务纠纷",
            "timeline": "案发当晚在俱乐部",
            "is_guilty": False,
            "personality_traits": ["冷静", "精明"],
            "secrets": [],
        }
        suspect = Suspect(**old_json)
        assert suspect.statements == []

    def test_suspect_with_statements(self):
        """新 JSON 含 statements"""
        new_json = {
            "id": "suspect-1",
            "name": "约翰·史密斯",
            "age": 35,
            "background": "被害人的商业伙伴",
            "motive": "债务纠纷",
            "timeline": "案发当晚在俱乐部",
            "is_guilty": False,
            "personality_traits": ["冷静", "精明"],
            "secrets": [],
            "statements": [
                {"id": "stmt-1", "content": "我当晚一直在俱乐部"},
                {"id": "stmt-2", "content": "我和被害人关系很好"},
            ],
        }
        suspect = Suspect(**new_json)
        assert len(suspect.statements) == 2
        assert suspect.statements[0].id == "stmt-1"
        assert suspect.statements[0].content == "我当晚一直在俱乐部"
        # 敏感字段默认 exclude，仅服务端可见
        assert suspect.statements[0].is_lie is False
        assert suspect.statements[0].refutable_by_clue_ids == []


class TestInferenceBackwardCompat:
    """Inference 模型旧 JSON 反序列化兼容"""

    def test_old_inference_without_node_type(self):
        """旧 JSON 不含 node_type"""
        old_json = {
            "id": "inf-1",
            "content": "匕首上的血迹表明凶手与被害人有近距离接触",
            "observation_ids": ["obs-1"],
            "parent_inference_ids": [],
            "confidence": 0.8,
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "clue_ids": ["clue-1"],
            "verification_result": None,
            "oracle_explanation": None,
            "user_marked_important": False,
        }
        inference = Inference(**old_json)
        assert inference.node_type == "mixed"

    def test_inference_with_node_type(self):
        """新 JSON 含 node_type"""
        new_json = {
            "id": "inf-2",
            "content": "嫌疑人的不在场证明被推翻",
            "observation_ids": [],
            "parent_inference_ids": [],
            "confidence": 0.9,
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "clue_ids": ["clue-2"],
            "node_type": "interrogation",
        }
        inference = Inference(**new_json)
        assert inference.node_type == "interrogation"


class TestGameStateBackwardCompat:
    """GameState 模型旧 JSON 反序列化兼容"""

    def test_old_game_state_without_new_fields(self):
        """旧 JSON 不含 suspect_states / verified_clue_ids"""
        old_json = {
            "game_id": "game-abc123",
            "difficulty": "classic",
            "phase": "investigation",
            "case": None,
            "deduction_chain": None,
            "interviewed_suspect_ids": [],
            "mistakes_made": 0,
            "max_mistakes": 2,
            "start_time": None,
            "time_limit_minutes": None,
        }
        gs = GameState(**old_json)
        assert gs.suspect_states == {}
        assert gs.verified_clue_ids == []

    def test_game_state_with_new_fields(self):
        """新 JSON 含全部新字段"""
        new_json = {
            "game_id": "game-xyz789",
            "difficulty": "hardcore",
            "phase": "interrogation",
            "suspect_states": {"suspect-1": "pressured", "suspect-2": "calm"},
            "verified_clue_ids": ["clue-1", "clue-3"],
        }
        gs = GameState(**new_json)
        assert gs.suspect_states["suspect-1"] == "pressured"
        assert gs.verified_clue_ids == ["clue-1", "clue-3"]


class TestSuspectStatementModel:
    """SuspectStatement 独立模型测试"""

    def test_statement_defaults(self):
        stmt = SuspectStatement(id="stmt-1", content="我什么都不知道")
        assert stmt.is_lie is False
        assert stmt.refutable_by_clue_ids == []
        assert stmt.revealed_when_broken is False

    def test_statement_exclude_fields(self):
        """验证 exclude=True 字段在 model_dump 中不出现"""
        stmt = SuspectStatement(
            id="stmt-2",
            content="我是无辜的",
            is_lie=True,
            refutable_by_clue_ids=["clue-1"],
            revealed_when_broken=True,
        )
        dumped = stmt.model_dump()
        assert "is_lie" not in dumped
        assert "refutable_by_clue_ids" not in dumped
        assert "revealed_when_broken" not in dumped
        assert dumped["id"] == "stmt-2"
        assert dumped["content"] == "我是无辜的"


class TestCaseBackwardCompat:
    """Case 模型整体旧 JSON 反序列化兼容"""

    def test_old_case_json(self):
        """模拟旧案件 JSON 完整反序列化"""
        old_case_json = {
            "id": "case-1",
            "victim_name": "亚瑟·布莱克伍德",
            "victim_background": "富有的银行家",
            "cause_of_death": " stab wounds",
            "time_of_death": "1895年10月15日 22:00",
            "location": "伦敦东区",
            "date": "1895-10-15T22:00:00",
            "suspects": [
                {
                    "id": "suspect-1",
                    "name": "约翰",
                    "age": 40,
                    "background": "管家",
                    "motive": "被解雇的怨恨",
                    "timeline": "案发时在厨房",
                    "is_guilty": True,
                    "personality_traits": ["忠诚", "沉默"],
                    "secrets": [],
                }
            ],
            "clues": [
                {
                    "id": "clue-1",
                    "description": "一把匕首",
                    "clue_type": "physical",
                    "related_suspect_ids": ["suspect-1"],
                    "discovered": False,
                    "obviousness": 0.5,
                }
            ],
            "summary": "",
            "murder_method": "",
            "true_murderer_id": "suspect-1",
            "scenes": [],
            "witnesses": [],
            "experts": [],
        }
        case = Case(**old_case_json)
        assert case.clues[0].verification_status == "unverified"
        assert case.suspects[0].statements == []
