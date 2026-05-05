"""
案件数据模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SuspectStatement(BaseModel):
    """嫌疑人陈述 - 审讯中嫌疑人说出的内容，部分为谎言可被线索反驳"""
    id: str
    content: str
    is_lie: bool = Field(default=False, exclude=True)              # 服务端专用，不下发
    refutable_by_clue_ids: List[str] = Field(default_factory=list, exclude=True)  # 可反驳该陈述的线索id列表
    revealed_when_broken: bool = Field(default=False, exclude=True)  # 崩溃时是否揭露该陈述


class Witness(BaseModel):
    """证人模型 - 目击者/邻居/相关人员，可能因恐惧或利益隐瞒部分事实"""
    id: str                                                          # witness-{n}
    name: str
    age: int
    occupation: str                                                  # 职业，如「街角报童」
    relationship_to_case: str                                        # 与案件的关系
    timeline: str                                                    # 案发时段轨迹（应与某嫌疑人有交集）
    personality_traits: List[str] = Field(default_factory=list)
    secrets: List[str] = Field(default_factory=list, exclude=True)  # 服务端专用，不下发
    key_observations: List[str] = Field(default_factory=list)       # 真实目击事实（LLM 回答知识库）
    is_lying_for_someone: bool = Field(default=False, exclude=True)  # 服务端专用，不下发
    bribed_by_suspect_id: Optional[str] = Field(default=None, exclude=True)  # 服务端专用
    related_suspect_ids: List[str] = Field(default_factory=list)
    credibility: float = Field(default=0.7, ge=0.0, le=1.0)        # 基础可信度


class ExpertKeyFinding(BaseModel):
    """专家关键发现条目"""
    topic: str
    finding: str
    related_clue_ids: List[str] = Field(default_factory=list)


class Expert(BaseModel):
    """专家模型 - 皇家法医等技术专家，完全可信，基于物证提供客观分析"""
    id: str                                                          # expert-{n}
    name: str
    title: str                                                       # 职称，如「皇家法医」
    expertise: List[str] = Field(default_factory=list)
    preliminary_report: str = ""                                     # 首次开场报告，80-150 字
    key_findings: List[ExpertKeyFinding] = Field(default_factory=list)
    methodology_notes: List[str] = Field(default_factory=list)      # 技术不确定性说明（防过度自信）
    related_clue_ids: List[str] = Field(default_factory=list)       # 仅可基于这些线索发言（反幻觉约束）


class Suspect(BaseModel):
    """嫌疑人模型"""
    id: str
    name: str
    age: int
    background: str
    motive: str
    timeline: str
    is_guilty: bool = False
    personality_traits: List[str] = Field(default_factory=list)
    secrets: List[str] = Field(default_factory=list)
    statements: List[SuspectStatement] = Field(default_factory=list)  # P1: 嫌疑人陈述列表


class SceneObject(BaseModel):
    """场景中的可交互对象（如：办公桌、信件、保险柜）"""
    id: str
    name: str
    description: str
    hidden_clue_ids: List[str] = Field(default_factory=list)  # 该对象内藏的线索 id（可为空）
    search_hints: List[str] = Field(default_factory=list)     # 用户搜查时的引导提示


class Scene(BaseModel):
    """案件场景（如：被害人书房、贝克街客厅）"""
    id: str
    name: str
    description: str                                  # 场景文字描述
    atmosphere_image: Optional[str] = None            # 氛围图 URL 或占位符
    objects: List[SceneObject] = Field(default_factory=list)
    npc_persona: str = ""                             # 该场景 NPC 的人设（如"沉默的管家"）


class Clue(BaseModel):
    """线索模型"""
    id: str
    description: str
    clue_type: str  # "physical", "testimonial", "forensic"
    location: Optional[str] = None
    related_suspect_ids: List[str] = Field(default_factory=list)
    # 干扰线索标记：仅服务端使用，禁止下发至客户端 (运行时 API 中默认剥离)
    # conclusion/reveal 走 game_service.get_case_reveal() 手工构造 dict，不受 exclude 影响
    is_red_herring: bool = Field(default=False, exclude=True)
    discovered: bool = False
    discovery_notes: Optional[str] = None
    obviousness: float = Field(default=0.5, ge=0.0, le=1.0)  # 0.0=隐蔽, 1.0=明显
    user_label: Optional[str] = None                  # 用户自定义命名
    source_type: str = "initial"                      # initial | scene | interrogation | witness | expert
    source_ref: Optional[str] = None                  # scene_id 或 suspect_id
    quoted_text: Optional[str] = None                 # 来源原文（审讯片段）
    user_generated: bool = False                      # 是否用户主动创建
    investigation_hint: Optional[str] = None          # 发现此线索后的下一步调查方向（仅服务端使用，供华生提示）
    chain_next_clue_index: Optional[int] = None       # 调查链：指向下一条线索的数组下标（null=链条终点）
    # P1: 线索验证状态（三态：未验证 / 已验证 / 已被驳斥）
    verification_status: str = "unverified"           # unverified | verified | refuted
    verification_notes: Optional[str] = None          # 验证备注（如验证过程说明）
    verified_by: Optional[str] = None                 # 产生验证的 actor id：suspect/witness/expert


class Case(BaseModel):
    """案件模型"""
    id: str
    victim_name: str
    victim_background: str
    cause_of_death: str
    time_of_death: str
    location: str
    date: datetime
    suspects: List[Suspect] = Field(default_factory=list)
    clues: List[Clue] = Field(default_factory=list)
    summary: str = ""
    murder_method: str = ""
    true_murderer_id: Optional[str] = None
    investigation_locations: List[str] = Field(default_factory=list)
    scenes: List[Scene] = Field(default_factory=list)
    witnesses: List[Witness] = Field(default_factory=list)
    experts: List[Expert] = Field(default_factory=list)


class Observation(BaseModel):
    """观察记录 - 用户在现场发现的具体事实"""
    id: str
    description: str
    location: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    related_clue_ids: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class Inference(BaseModel):
    """推理节点 - 基于观察得出的推论"""
    id: str
    content: str
    observation_ids: List[str] = Field(default_factory=list)
    parent_inference_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.5  # 0.0 to 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    clue_ids: List[str] = Field(default_factory=list)
    verification_result: Optional[str] = None         # correct | wrong | partial
    oracle_explanation: Optional[str] = None
    user_marked_important: bool = False
    node_type: str = "mixed"                          # P1: fact | interrogation | mixed


class ReasoningRecord(Inference):
    """推理记录 = 已经过 Oracle 验证的 Inference"""
    pass


class Hypothesis(BaseModel):
    """假设 - 用户提出的关于案件的假设"""
    id: str
    title: str
    description: str
    inference_ids: List[str] = Field(default_factory=list)
    suspect_id: Optional[str] = None
    is_verified: bool = False
    verification_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    support_score: float = 0.0  # 支持度评分


class DeductionChain(BaseModel):
    """完整推理链条"""
    id: str
    observations: List[Observation] = Field(default_factory=list)
    inferences: List[Inference] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    conclusion: Optional[str] = None
    final_accusation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
