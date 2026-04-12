"""
游戏服务
"""
from typing import Dict, Optional
from loguru import logger
from datetime import datetime

from app.models.game import GameState, GameDifficulty, GamePhase
from app.models.case import Case


class GameService:
    """游戏服务类"""

    def __init__(self):
        self._games: Dict[str, GameState] = {}
        logger.info("[GameService] 初始化游戏服务")

    def create_game(self, difficulty: GameDifficulty = GameDifficulty.CLASSIC) -> GameState:
        """创建新游戏"""
        import uuid

        game_id = str(uuid.uuid4())

        # 根据难度设置参数
        max_mistakes = {
            GameDifficulty.EASY: 3,
            GameDifficulty.CLASSIC: 2,
            GameDifficulty.HARDCORE: 1,
        }[difficulty]

        time_limit = {
            GameDifficulty.EASY: 60,
            GameDifficulty.CLASSIC: 90,
            GameDifficulty.HARDCORE: None,
        }[difficulty]

        game_state = GameState(
            game_id=game_id,
            difficulty=difficulty,
            phase=GamePhase.START,
            max_mistakes=max_mistakes,
            time_limit_minutes=time_limit,
            start_time=datetime.utcnow(),
        )

        self._games[game_id] = game_state
        logger.info(f"[GameService] 创建游戏: {game_id}, 难度: {difficulty}")
        return game_state

    def get_game(self, game_id: str) -> Optional[GameState]:
        """获取游戏状态"""
        return self._games.get(game_id)

    def set_case(self, game_id: str, case: Case) -> bool:
        """设置案件"""
        game = self.get_game(game_id)
        if not game:
            logger.warning(f"[GameService] 游戏不存在: {game_id}")
            return False

        game.case = case
        game.phase = GamePhase.INVESTIGATION
        game.updated_at = datetime.utcnow()
        logger.info(f"[GameService] 设置案件: {game_id} -> {case.id}")
        return True


# 全局游戏服务实例
_game_service: Optional[GameService] = None


def get_game_service() -> GameService:
    """获取游戏服务单例"""
    global _game_service
    if _game_service is None:
        _game_service = GameService()
    return _game_service
