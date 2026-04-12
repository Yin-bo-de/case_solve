"""
游戏相关 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from typing import Optional

from app.models.game import GameState, CreateGameRequest, GameDifficulty
from app.models.case import Observation
from app.services.game_service import get_game_service
from app.agents.case_generator_agent import get_case_generator
from app.agents.watson_agent import get_watson_agent

router = APIRouter()


class WatsonObservationRequest(BaseModel):
    """华生观察评论请求"""
    observation: Observation


class WatsonHintRequest(BaseModel):
    """华生提示请求"""
    hint_type: str = "idle"
    observations_count: int = 0
    areas_examined: int = 0
    total_areas: int = 0


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


@router.post("/{game_id}/watson/observation")
async def get_watson_observation_comment(game_id: str, request: WatsonObservationRequest):
    """获取华生对新观察的评论"""
    logger.info(f"[API] 获取华生观察评论: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    watson = get_watson_agent()
    comment = await watson.share_observation(request.observation)

    logger.info(f"[API] 华生观察评论生成成功: {game_id}")
    return {"comment": comment}


@router.post("/{game_id}/watson/hint")
async def get_watson_hint(game_id: str, request: WatsonHintRequest):
    """获取华生提示（当用户长时间无进展时）"""
    logger.info(f"[API] 获取华生提示: {game_id}, 类型: {request.hint_type}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    watson = get_watson_agent()
    hint: Optional[str] = None

    if request.hint_type == "idle":
        # 长时间无进展，给出提示
        if request.areas_examined < request.total_areas:
            remaining = request.total_areas - request.areas_examined
            hint = f"老朋友，我们还有 {remaining} 个地方没仔细看过。也许应该再检查一下那些还没勘查的区域？"
        elif request.observations_count == 0:
            hint = "让我们开始吧！点击场景中的任何区域来仔细查看。"
        else:
            hint = await watson.encourage()
    elif request.hint_type == "area":
        # 进入某个区域时的提示
        hints = [
            "仔细看看这里，可能有什么重要的线索。",
            "我觉得这个地方值得好好检查一下。",
            "你觉得这里会有什么发现吗？",
        ]
        import random
        hint = random.choice(hints)

    logger.info(f"[API] 华生提示生成成功: {game_id}")
    return {"hint": hint}
