"""
案件数据模型
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


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
    is_red_herring: bool = False
    discovered: bool = False
    discovery_notes: Optional[str] = None
    obviousness: float = Field(default=0.5, ge=0.0, le=1.0)  # 0.0=隐蔽, 1.0=明显
    user_label: Optional[str] = None                  # 用户自定义命名
    source_type: str = "initial"                      # initial | scene | interrogation
    source_ref: Optional[str] = None                  # scene_id 或 suspect_id
    quoted_text: Optional[str] = None                 # 来源原文（审讯片段）
    user_generated: bool = False                      # 是否用户主动创建


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
