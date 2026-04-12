"""
游戏相关 API 路由
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter()


@router.post("/new")
async def create_new_game():
    """创建新案件"""
    logger.info("[API] 创建新游戏请求")
    # TODO: 实现创建新游戏逻辑
    return {"gameId": "mock-game-123", "status": "created"}


@router.get("/{game_id}")
async def get_game_state(game_id: str):
    """获取游戏状态"""
    logger.info(f"[API] 获取游戏状态: {game_id}")
    # TODO: 实现获取游戏状态逻辑
    return {"gameId": game_id, "state": "investigating"}


@router.post("/{game_id}/difficulty")
async def set_difficulty(game_id: str, difficulty: str):
    """设置难度"""
    logger.info(f"[API] 设置游戏难度: {game_id} -> {difficulty}")
    if difficulty not in ["easy", "classic", "hardcore"]:
        raise HTTPException(status_code=400, detail="无效的难度级别")
    # TODO: 实现设置难度逻辑
    return {"gameId": game_id, "difficulty": difficulty}
