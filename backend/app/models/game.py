"""
游戏状态数据模型
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
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


class CreateGameRequest(BaseModel):
    """创建游戏请求"""
    difficulty: GameDifficulty = GameDifficulty.CLASSIC
