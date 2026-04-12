"""
游戏相关 API 路由
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.game import GameState, CreateGameRequest, GameDifficulty
from app.services.game_service import get_game_service
from app.agents.case_generator_agent import get_case_generator

router = APIRouter()


@router.post("/new", response_model=GameState)
async def create_new_game(request: CreateGameRequest):
    """创建新案件"""
    logger.info(f"[API] 创建新游戏请求, 难度: {request.difficulty}")

    game_service = get_game_service()
    case_generator = get_case_generator()

    # 创建游戏状态
    game = game_service.create_game(difficulty=request.difficulty)

    # 生成案件
    case = await case_generator.generate_case(difficulty=request.difficulty.value)
    game_service.set_case(game.game_id, case)

    # 获取更新后的游戏状态
    updated_game = game_service.get_game(game.game_id)
    if not updated_game:
        raise HTTPException(status_code=500, detail="创建游戏失败")

    logger.info(f"[API] 游戏创建成功: {game.game_id}")
    return updated_game


@router.get("/{game_id}", response_model=GameState)
async def get_game_state(game_id: str):
    """获取游戏状态"""
    logger.info(f"[API] 获取游戏状态: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    return game


@router.post("/{game_id}/difficulty")
async def set_difficulty(game_id: str, difficulty: GameDifficulty):
    """设置难度"""
    logger.info(f"[API] 设置游戏难度: {game_id} -> {difficulty}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    # 更新难度
    game.difficulty = difficulty

    # 根据新难度调整参数
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

    game.max_mistakes = max_mistakes
    game.time_limit_minutes = time_limit

    logger.info(f"[API] 难度设置成功: {game_id} -> {difficulty}")
    return {"gameId": game_id, "difficulty": difficulty}
