"""
兑换码相关 API 路由
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.redemption import (
    RedemptionGenerateResponse,
    RedemptionVerifyRequest,
    RedemptionVerifyResponse,
)
from app.services.redemption_service import get_redemption_service
from app.services.game_service import get_game_service
from app.models.game import GameDifficulty

router = APIRouter()


@router.post("/generate", response_model=RedemptionGenerateResponse)
async def generate_code():
    """生成兑换码（绑定当前 settings 的 OpenAI 配置，响应不含 apikey）"""
    logger.info("[API] 生成兑换码请求")
    service = get_redemption_service()
    result = service.generate_code()
    return result


@router.post("/verify", response_model=RedemptionVerifyResponse)
async def verify_code(request: RedemptionVerifyRequest):
    """
    验证兑换码并扣减一次使用次数。
    验证成功后直接创建一个 START 阶段的游戏会话，返回 game_id 给前端。
    """
    logger.info(f"[API] 验证兑换码请求: {request.code[:4]}***")

    redemption_service = get_redemption_service()
    success, record, message = redemption_service.validate_and_consume(request.code)

    if not success:
        logger.warning(f"[API] 兑换码验证失败: {request.code[:4]}*** - {message}")
        return RedemptionVerifyResponse(
            success=False,
            remaining_uses=0,
            message=message,
            game_id=None,
        )

    # 验证通过 → 创建游戏会话，绑定 OpenAI 配置快照
    game_service = get_game_service()
    game = game_service.create_game(
        difficulty=GameDifficulty.CLASSIC,
        openai_api_key=record.openai_api_key,
        openai_base_url=record.openai_base_url,
        redemption_code=request.code,
    )

    remaining = record.max_uses - record.used_count
    logger.info(f"[API] 兑换码验证成功，创建游戏: {game.game_id}, 剩余次数: {remaining}")

    return RedemptionVerifyResponse(
        success=True,
        remaining_uses=remaining,
        message="验证成功",
        game_id=game.game_id,
    )
