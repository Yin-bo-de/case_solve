"""
案件数据模型
"""
from datetime import datetime
from typing import List, Optional
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


class Clue(BaseModel):
    """线索模型"""
    id: str
    description: str
    clue_type: str  # "physical", "testimonial", "forensic"
    location: Optional[str] = None
    related_suspect_ids: List[str] = Field(default_factory=list)
    is_red_herring: bool = False


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


class DeductionNode(BaseModel):
    """推理节点"""
    id: str
    content: str
    parent_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.5


class DeductionChain(BaseModel):
    """推理链条"""
    id: str
    observations: List[str] = Field(default_factory=list)
    inferences: List[DeductionNode] = Field(default_factory=list)
    hypotheses: List[str] = Field(default_factory=list)
