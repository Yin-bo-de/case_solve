"""
日志配置模块

配置 loguru 的文件输出与按天轮转，并拦截标准库 logging（uvicorn 等）
使其也进入 loguru 的日志流。
"""
import logging
import sys

from loguru import logger

from app.config import get_settings


class InterceptHandler(logging.Handler):
    """拦截标准库 logging，将记录重定向到 loguru。

    通过遍历调用栈找到真正的日志发起位置，保证文件名/行号准确。
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """初始化日志配置。

n    - 移除 loguru 默认 stderr sink，重新添加统一格式的 stderr + 文件 sink
    - 文件路径使用相对路径 ``logs/app.log``：
      容器内（WORKDIR=/app）解析为 ``/app/logs/app.log``；
      本地开发解析为 ``backend/logs/app.log``，两端兼容。
    - ``rotation="00:00"`` 每天午夜自动切分新日志文件。
    - ``retention="30 days"`` 自动清理超过 30 天的旧日志，防止磁盘无限膨胀。
    - 拦截 uvicorn/fastapi 的标准库 logging，统一落入 loguru 文件。
    """
    settings = get_settings()

    # 移除默认 sink，避免格式不统一
    logger.remove()

    # stderr：保留 docker logs 可见性
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # 文件输出：按天轮转，保留 30 天
    logger.add(
        "logs/app.log",
        rotation="00:00",
        retention="30 days",
        level=settings.log_level,
        encoding="utf-8",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        ),
    )

    # 拦截标准库 logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        logging_logger = logging.getLogger(name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    logger.info("日志配置初始化完成 | 文件: logs/app.log | 轮转: 每日 00:00 | 保留: 30 天")
