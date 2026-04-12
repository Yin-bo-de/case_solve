"""
游戏相关 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from typing import Optional, List, Dict, Any

from app.models.game import GameState, CreateGameRequest, GameDifficulty
from app.models.case import Observation
from app.services.game_service import get_game_service
from app.agents.case_generator_agent import get_case_generator
from app.agents.watson_agent import get_watson_agent
from app.agents.suspect_agent import get_suspect_agent

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


class SuspectQuestionRequest(BaseModel):
    """嫌疑人提问请求"""
    suspect_id: str
    question: str
    conversation_history: List[Dict[str, str]] = []
    is_private: bool = True
    other_suspect_ids: List[str] = []


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


@router.post("/{game_id}/interrogation/question")
async def ask_suspect_question(game_id: str, request: SuspectQuestionRequest):
    """向嫌疑人提问（单独审讯或全体质询）"""
    logger.info(f"[API] 向嫌疑人提问: {game_id}, 嫌疑人: {request.suspect_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    # 找到对应的嫌疑人
    suspect = next(
        (s for s in game.case.suspects if s.id == request.suspect_id),
        None
    )
    if not suspect:
        raise HTTPException(status_code=404, detail=f"嫌疑人不存在: {request.suspect_id}")

    # 调用嫌疑人Agent生成回复
    suspect_agent = get_suspect_agent()
    response = await suspect_agent.generate_response(
        suspect=suspect,
        case=game.case,
        user_question=request.question,
        conversation_history=request.conversation_history,
        is_private=request.is_private,
        other_suspects_present=request.other_suspect_ids
    )

    # 检测谎言
    lie_detection = await suspect_agent.detect_lie(suspect, response, game.case)

    logger.info(f"[API] 嫌疑人回复生成成功: {game_id}")
    return {
        "suspect_id": suspect.id,
        "suspect_name": suspect.name,
        "response": response,
        "lie_detection": lie_detection
    }


@router.post("/{game_id}/interrogation/interjection")
async def get_suspect_interjection(
    game_id: str,
    responding_suspect_id: str,
    other_suspect_id: str,
    context: str
):
    """获取嫌疑人的插话/反驳（全体质询时）"""
    logger.info(f"[API] 获取嫌疑人插话: {game_id}, {other_suspect_id} -> {responding_suspect_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    # 找到对应的嫌疑人
    responding_suspect = next(
        (s for s in game.case.suspects if s.id == responding_suspect_id),
        None
    )
    other_suspect = next(
        (s for s in game.case.suspects if s.id == other_suspect_id),
        None
    )

    if not responding_suspect or not other_suspect:
        raise HTTPException(status_code=404, detail="嫌疑人不存在")

    # 调用嫌疑人Agent生成插话
    suspect_agent = get_suspect_agent()
    interjection = await suspect_agent.generate_interjection(
        responding_suspect=responding_suspect,
        other_suspect=other_suspect,
        case=game.case,
        context=context
    )

    logger.info(f"[API] 嫌疑人插话生成成功: {game_id}")
    return {"interjection": interjection}
