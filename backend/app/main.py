"""
FastAPI 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.logging_config import setup_logging
from app.routers import game
from app.routers import redemption


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger.info(f"🚀 启动福尔摩斯探案游戏后端 - 环境: {settings.environment}")

    yield

    logger.info("👋 应用关闭")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title="福尔摩斯式探案游戏 API",
        description="AI驱动的维多利亚时代探案游戏后端服务",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发环境允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(game.router, prefix="/api/game", tags=["game"])
    app.include_router(redemption.router, prefix="/api/redemption", tags=["redemption"])

    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {"status": "healthy", "service": "sherlock-game-backend"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )
