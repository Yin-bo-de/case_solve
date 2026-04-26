"""
兑换码服务单元测试
覆盖：生成、验证成功/失败、次数耗尽、并发安全
"""
import json
import threading
import pytest
from pathlib import Path
from unittest.mock import patch

from app.services.redemption_service import RedemptionService, CODES_FILE, DATA_DIR


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_codes_file(tmp_path, monkeypatch):
    """每个测试使用独立临时目录，隔离 JSON 文件"""
    tmp_codes = tmp_path / "redemption_codes.json"
    monkeypatch.setattr(
        "app.services.redemption_service.CODES_FILE", tmp_codes
    )
    monkeypatch.setattr(
        "app.services.redemption_service.DATA_DIR", tmp_path
    )
    yield tmp_codes


@pytest.fixture
def service():
    """每个测试独立的 RedemptionService 实例（非单例）"""
    return RedemptionService()


# ─── 生成测试 ─────────────────────────────────────────────────────────────────

class TestGenerateCode:
    def test_generate_creates_json_file(self, service, clean_codes_file):
        """生成后 JSON 文件应存在，且 used_count 为 0"""
        with patch("app.services.redemption_service.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "sk-test"
            mock_settings.return_value.openai_base_url = "https://api.openai.com/v1"
            response = service.generate_code()

        assert clean_codes_file.exists(), "JSON 文件应被创建"
        data = json.loads(clean_codes_file.read_text())
        assert len(data["codes"]) == 1
        assert data["codes"][0]["used_count"] == 0
        assert data["codes"][0]["code"] == response.code

    def test_generate_code_format(self, service):
        """生成的兑换码格式应为 XXXX-XXXX-XXXX"""
        with patch("app.services.redemption_service.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "sk-test"
            mock_settings.return_value.openai_base_url = "https://api.openai.com/v1"
            response = service.generate_code()

        parts = response.code.split("-")
        assert len(parts) == 3, "兑换码应由 3 段组成"
        assert all(len(p) == 4 for p in parts), "每段应为 4 个字符"

    def test_generate_does_not_expose_apikey(self, service):
        """生成响应不应包含 openai_api_key"""
        with patch("app.services.redemption_service.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "sk-secret"
            mock_settings.return_value.openai_base_url = "https://api.openai.com/v1"
            response = service.generate_code()

        response_dict = response.model_dump()
        assert "openai_api_key" not in response_dict, "响应不应包含 apikey"


# ─── 验证测试 ─────────────────────────────────────────────────────────────────

class TestValidateCode:
    def _gen(self, service):
        with patch("app.services.redemption_service.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "sk-test"
            mock_settings.return_value.openai_base_url = "https://api.openai.com/v1"
            return service.generate_code()

    def test_valid_code_succeeds(self, service):
        """有效兑换码验证应成功，used_count 增加 1"""
        response = self._gen(service)
        success, record, msg = service.validate_and_consume(response.code)

        assert success is True
        assert msg == "验证成功"
        assert record is not None
        assert record.used_count == 1

    def test_nonexistent_code_fails(self, service):
        """不存在的兑换码应返回失败"""
        success, record, msg = service.validate_and_consume("XXXX-XXXX-XXXX")

        assert success is False
        assert record is None
        assert "无效" in msg

    def test_exhausted_code_fails(self, service):
        """使用 10 次后，第 11 次应失败"""
        response = self._gen(service)
        code = response.code

        for _ in range(10):
            success, _, _ = service.validate_and_consume(code)
            assert success is True

        success, record, msg = service.validate_and_consume(code)
        assert success is False
        assert "上限" in msg

    def test_get_remaining_uses(self, service):
        """get_remaining_uses 应返回正确剩余次数"""
        response = self._gen(service)
        code = response.code

        assert service.get_remaining_uses(code) == 10

        service.validate_and_consume(code)
        service.validate_and_consume(code)
        assert service.get_remaining_uses(code) == 8

    def test_get_remaining_nonexistent(self, service):
        """不存在的兑换码应返回 0"""
        assert service.get_remaining_uses("NONE-NONE-NONE") == 0


# ─── 并发安全测试 ─────────────────────────────────────────────────────────────

class TestConcurrency:
    def test_concurrent_consume_no_overcharge(self, service):
        """多线程并发验证，used_count 不应超过 max_uses"""
        with patch("app.services.redemption_service.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "sk-test"
            mock_settings.return_value.openai_base_url = "https://api.openai.com/v1"
            response = service.generate_code()
        code = response.code

        results = []
        errors = []

        def consume():
            try:
                success, _, _ = service.validate_and_consume(code)
                results.append(success)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=consume) for _ in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"并发执行出现异常: {errors}"
        successful = sum(1 for r in results if r)
        assert successful == 10, f"成功次数应为 10（max_uses），实际为 {successful}"
