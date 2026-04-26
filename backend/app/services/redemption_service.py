"""
兑换码服务
- 使用本地 JSON 文件持久化（MVP 阶段无需数据库）
- threading.Lock 保证并发扣减不超扣
- 原子写（写临时文件 + os.replace）防进程崩溃导致数据损坏
"""
import os
import json
import random
import string
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger

from app.models.redemption import RedemptionCode, RedemptionGenerateResponse
from app.config import get_settings


DATA_DIR = Path(__file__).parent.parent.parent / "data"
CODES_FILE = DATA_DIR / "redemption_codes.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RedemptionService:
    """兑换码服务单例"""

    def __init__(self):
        self._lock = threading.Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("[RedemptionService] 初始化兑换码服务")

    # ------------------------------------------------------------------
    # 公开方法
    # ------------------------------------------------------------------

    def generate_code(self) -> RedemptionGenerateResponse:
        """生成一个新兑换码，快照当前 settings 的 OpenAI 配置"""
        settings = get_settings()
        code = self._make_code()
        now = datetime.now(timezone.utc)

        record = RedemptionCode(
            code=code,
            max_uses=10,
            used_count=0,
            openai_api_key=settings.openai_api_key,
            openai_base_url=settings.openai_base_url,
            created_at=now,
            last_used_at=None,
        )

        with self._lock:
            data = self._load()
            data["codes"].append(record.model_dump(mode="json"))
            self._save(data)

        logger.info(f"[RedemptionService] 生成兑换码: {code}")
        return RedemptionGenerateResponse(
            code=code,
            max_uses=record.max_uses,
            used_count=record.used_count,
            created_at=now,
        )

    def validate_and_consume(self, code: str) -> tuple[bool, Optional[RedemptionCode], str]:
        """
        校验兑换码有效性并扣减一次使用次数。

        Returns:
            (success, redemption_code_or_none, message)
        """
        with self._lock:
            data = self._load()
            entry = next((c for c in data["codes"] if c["code"] == code), None)

            if entry is None:
                logger.warning(f"[RedemptionService] 兑换码不存在: {code}")
                return False, None, "兑换码无效"

            if entry["used_count"] >= entry["max_uses"]:
                logger.warning(f"[RedemptionService] 兑换码已耗尽: {code}")
                return False, None, "兑换码已达使用上限"

            entry["used_count"] += 1
            entry["last_used_at"] = _now_iso()
            self._save(data)

        record = RedemptionCode(**entry)
        remaining = record.max_uses - record.used_count
        logger.info(f"[RedemptionService] 兑换码验证成功: {code}, 剩余: {remaining}")
        return True, record, "验证成功"

    def get_remaining_uses(self, code: str) -> int:
        """查询剩余可用次数（不扣减）"""
        data = self._load()
        entry = next((c for c in data["codes"] if c["code"] == code), None)
        if entry is None:
            return 0
        return max(0, entry["max_uses"] - entry["used_count"])

    # ------------------------------------------------------------------
    # 私有辅助
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        """从 JSON 文件加载数据，文件不存在时返回空结构"""
        if not CODES_FILE.exists():
            return {"codes": []}
        try:
            with open(CODES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"[RedemptionService] 读取兑换码文件失败: {e}")
            return {"codes": []}

    def _save(self, data: dict) -> None:
        """原子写：先写临时文件，再 os.replace 替换正式文件"""
        tmp_file = CODES_FILE.with_suffix(".tmp")
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, CODES_FILE)
        except OSError as e:
            logger.error(f"[RedemptionService] 写入兑换码文件失败: {e}")
            if tmp_file.exists():
                tmp_file.unlink(missing_ok=True)
            raise

    @staticmethod
    def _make_code() -> str:
        """生成 XXXX-XXXX-XXXX 格式的随机兑换码"""
        chars = string.ascii_uppercase + string.digits
        segments = ["".join(random.choices(chars, k=4)) for _ in range(3)]
        return "-".join(segments)


# ------------------------------------------------------------------
# 单例工厂
# ------------------------------------------------------------------

_redemption_service: Optional[RedemptionService] = None


def get_redemption_service() -> RedemptionService:
    """获取兑换码服务单例"""
    global _redemption_service
    if _redemption_service is None:
        _redemption_service = RedemptionService()
    return _redemption_service
