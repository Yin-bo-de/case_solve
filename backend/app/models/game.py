"""
游戏状态数据模型
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

from app.models.case import Case, DeductionChain


class GameDifficulty(str, Enum):
    """游戏难度"""
    EASY = "easy"
    CLASSIC = "classic"
    HARDCORE = "hardcore"


class GamePhase(str, Enum):
    """游戏阶段"""
    START = "start"
    INVESTIGATION = "investigation"
    INTERROGATION = "interrogation"
    DEDUCTION = "deduction"
    CONCLUSION = "conclusion"


class WatsonChatMessage(BaseModel):
    """华生对话消息"""
    id: str
    role: Literal["user", "watson"]
    content: str
    message_type: Literal[
        "guidance",
        "clue_discussion",
        "suspect_analysis",
        "deduction_review",
        "knowledge",
        "encouragement",
        "general"
    ]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WatsonChatContext(BaseModel):
    """华生对话上下文"""
    game_phase: GamePhase
    observations_count: int
    clues_collected: int
    suspects_interviewed: List[str]
    inferences_count: int
    hypotheses_count: int
    current_clue_ids: List[str] = []
    current_suspect_ids: List[str] = []
    recent_conversation_summary: Optional[str] = None
    current_clues: List[Dict[str, str]] = Field(default_factory=list)
    available_scenes: List[Dict[str, str]] = Field(default_factory=list)
    suspects: List[Dict[str, str]] = Field(default_factory=list)
    witnesses: List[Dict[str, str]] = Field(default_factory=list)  # id/name/occupation
    experts: List[Dict[str, str]] = Field(default_factory=list)    # id/name/title


class GameState(BaseModel):
    """游戏状态"""
    game_id: str
    difficulty: GameDifficulty = GameDifficulty.CLASSIC
    phase: GamePhase = GamePhase.START
    case: Optional[Case] = None
    deduction_chain: Optional[DeductionChain] = None
    interviewed_suspect_ids: List[str] = []
    mistakes_made: int = 0
    max_mistakes: int = 2
    start_time: Optional[datetime] = None
    time_limit_minutes: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # 兑换码绑定快照（apikey 不对外暴露，通过 response_model_exclude 过滤）
    openai_api_key: Optional[str] = Field(default=None, exclude=True)
    openai_base_url: Optional[str] = None
    redemption_code: Optional[str] = None


class CreateGameRequest(BaseModel):
    """创建游戏请求"""
    difficulty: GameDifficulty = GameDifficulty.CLASSIC
    redemption_code: Optional[str] = None
