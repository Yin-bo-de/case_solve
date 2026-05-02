"""
兑换码相关 API 路由
"""
from fastapi import APIRouter, HTTPException, Body
from loguru import logger

from app.models.redemption import (
    RedemptionGenerateRequest,
    RedemptionGenerateResponse,
    RedemptionVerifyRequest,
    RedemptionVerifyResponse,
)
from app.services.redemption_service import get_redemption_service
from app.services.game_service import get_game_service
from app.models.game import GameDifficulty

router = APIRouter()


@router.post("/generate", response_model=RedemptionGenerateResponse)
async def generate_code(
    request: RedemptionGenerateRequest = Body(default_factory=RedemptionGenerateRequest),
):
    """生成兑换码（绑定当前 settings 的 OpenAI 配置，响应不含 apikey）"""
    logger.info(f"[API] 生成兑换码请求 max_uses={request.max_uses}")
    service = get_redemption_service()
    result = service.generate_code(max_uses=request.max_uses)
    return result


@router.post("/verify", response_model=RedemptionVerifyResponse)
async def verify_code(request: RedemptionVerifyRequest):
    """
    仅验证兑换码有效性（不扣减次数，不创建游戏）。
    前端验证成功后调用 /new 接口创建游戏并生成案件。
    """
    logger.info(f"[API] 验证兑换码请求: {request.code[:4]}***")

    redemption_service = get_redemption_service()
    success, record, message = redemption_service.validate_only(request.code)

    if not success:
        logger.warning(f"[API] 兑换码验证失败: {request.code[:4]}*** - {message}")
        return RedemptionVerifyResponse(
            success=False,
            remaining_uses=0,
            message=message,
            game_id=None,
        )

    remaining = record.max_uses - record.used_count
    logger.info(f"[API] 兑换码验证通过: {request.code[:4]}***, 剩余: {remaining}")

    return RedemptionVerifyResponse(
        success=True,
        remaining_uses=remaining,
        message="验证成功",
        game_id=None,
    )
