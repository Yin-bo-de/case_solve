"""
兑换码数据模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RedemptionCode(BaseModel):
    """兑换码完整结构（仅服务内部使用，不对外暴露 apikey）"""
    code: str
    max_uses: int = 10
    used_count: int = 0
    openai_api_key: str
    openai_base_url: str
    created_at: datetime
    last_used_at: Optional[datetime] = None


class RedemptionGenerateRequest(BaseModel):
    """生成兑换码请求（可选参数，未传时使用默认值）"""
    max_uses: int = Field(default=10, ge=1, le=1000, description="兑换码最大可用次数，范围 1-1000")


class RedemptionGenerateResponse(BaseModel):
    """生成兑换码响应（不含 apikey）"""
    code: str
    max_uses: int
    used_count: int
    created_at: datetime


class RedemptionVerifyRequest(BaseModel):
    """验证兑换码请求"""
    code: str


class RedemptionVerifyResponse(BaseModel):
    """验证兑换码响应（不含 apikey）"""
    success: bool
    remaining_uses: int
    message: str
