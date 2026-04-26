"""
Agent 上下文大小管理单元测试
验证：token 估算、消息截断、聊天记录上限、推理数据软上限
"""
import pytest
from unittest.mock import MagicMock, patch

from app.agents._llm_helpers import estimate_token_count, truncate_messages_by_token
from app.services.game_service import GameService
from app.models.game import GameDifficulty


class TestTokenEstimation:
    """测试 token 估算函数"""

    def test_estimate_empty_string(self):
        assert estimate_token_count("") >= 0

    def test_estimate_english_text(self):
        text = "Hello world"
        count = estimate_token_count(text)
        assert count > 0
        # 英文粗略估算：约 0.75 tokens / word，2 个单词约 2-3 tokens
        assert count < 20

    def test_estimate_chinese_text(self):
        text = "你好世界"
        count = estimate_token_count(text)
        assert count > 0
        # 中文粗略估算：约 1 token / 字符（cl100k_base）
        assert count >= 2

    def test_estimate_long_text(self):
        text = "The quick brown fox jumps over the lazy dog. " * 100
        count = estimate_token_count(text)
        assert count > 100


class TestTruncateMessagesByToken:
    """测试消息截断函数"""

    def test_short_list_not_truncated(self):
        """短列表不截断"""
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        result = truncate_messages_by_token(messages, max_tokens=1000)
        assert len(result) == 2
        assert result == messages

    def test_long_list_truncated_to_recent(self):
        """长列表正确截断到最近的消息"""
        messages = [
            {"role": "user", "content": f"message {i}"}
            for i in range(100)
        ]
        # 设置一个很低的 token 上限，只能保留最近几条
        result = truncate_messages_by_token(messages, max_tokens=20)
        assert len(result) < 100
        # 保留的是最近的消息
        assert result[-1]["content"] == "message 99"

    def test_single_long_message_truncated(self):
        """单条超长消息的处理"""
        long_text = "word " * 10000  # 约 10000 个单词
        messages = [
            {"role": "user", "content": long_text},
        ]
        result = truncate_messages_by_token(messages, max_tokens=10)
        assert len(result) == 1
        # 内容被截断
        assert len(result[0]["content"]) < len(long_text)

    def test_empty_list(self):
        """空列表返回空"""
        result = truncate_messages_by_token([], max_tokens=100)
        assert result == []

    def test_preserves_last_message(self):
        """始终保留最后一条消息"""
        messages = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
            {"role": "user", "content": "third"},
        ]
        result = truncate_messages_by_token(messages, max_tokens=5)
        assert len(result) >= 1
        assert result[-1]["content"] == "third"


class TestSuspectAgentHistoryTruncation:
    """测试 SuspectAgent 的上下文截断逻辑"""

    @pytest.fixture
    def mock_suspect(self):
        suspect = MagicMock()
        suspect.name = "嫌疑人A"
        suspect.background = "背景"
        suspect.motive = "动机"
        suspect.timeline = "时间线"
        suspect.personality_traits = ["谨慎"]
        suspect.secrets = ["秘密1"]
        suspect.is_guilty = False
        return suspect

    @pytest.fixture
    def mock_case(self):
        case = MagicMock()
        case.victim_name = "受害者"
        case.victim_background = "背景"
        case.summary = "案件摘要"
        return case

    @pytest.mark.asyncio
    async def test_history_truncated_to_max_rounds(self, mock_suspect, mock_case):
        """传入 100 条历史（50轮），确认只保留最近 20 轮（40条）"""
        from app.agents.suspect_agent import SuspectAgent

        agent = SuspectAgent()

        # 构造 100 条消息（50轮 user + assistant）
        history = []
        for i in range(50):
            history.append({"role": "user", "content": f"问题 {i}"})
            history.append({"role": "assistant", "content": f"回答 {i}"})

        mock_result = MagicMock()
        mock_result.content = "测试回复"

        with patch("app.agents.suspect_agent.invoke_with_retry") as mock_invoke:
            mock_invoke.return_value = mock_result

            await agent.generate_response(
                suspect=mock_suspect,
                case=mock_case,
                user_question="最新问题",
                conversation_history=history,
            )

            # 检查传入的 history 参数
            call_kwargs = mock_invoke.call_args[1]["inputs"]
            passed_history = call_kwargs["history"]
            # 应截断为最近 20 轮 = 40 条消息
            assert len(passed_history) <= 40


class TestWatsonChatHistoryLimit:
    """测试 Watson 聊天历史上限"""

    def test_history_limit_enforced(self):
        """连续添加 60 条消息，确认只保留 50 条"""
        service = GameService()
        game = service.create_game(GameDifficulty.CLASSIC)
        game_id = game.game_id

        # 添加 60 条消息
        for i in range(60):
            service.add_watson_chat_message(
                game_id=game_id,
                role="user" if i % 2 == 0 else "watson",
                content=f"消息 {i}",
                message_type="general",
            )

        history = service.get_watson_chat_history(game_id)
        assert len(history) == 50
        # 保留的是最近的消息
        assert history[-1].content == "消息 59"

    def test_history_limit_not_exceeded(self):
        """添加 30 条消息，不应触发截断"""
        service = GameService()
        game = service.create_game(GameDifficulty.CLASSIC)
        game_id = game.game_id

        for i in range(30):
            service.add_watson_chat_message(
                game_id=game_id,
                role="user" if i % 2 == 0 else "watson",
                content=f"消息 {i}",
                message_type="general",
            )

        history = service.get_watson_chat_history(game_id)
        assert len(history) == 30


class TestDeductionChainLimits:
    """测试推理链条数据上限"""

    def test_inference_limit(self):
        """推理数量达到上限时抛出异常"""
        service = GameService()
        game = service.create_game(GameDifficulty.CLASSIC)
        game_id = game.game_id

        # 先创建 50 条推理
        for i in range(50):
            service.create_inference(
                game_id=game_id,
                content=f"推理 {i}",
                observation_ids=[],
                parent_inference_ids=[],
            )

        # 第 51 条应失败
        with pytest.raises(ValueError, match="推理记录已达上限"):
            service.create_inference(
                game_id=game_id,
                content="超出上限的推理",
                observation_ids=[],
                parent_inference_ids=[],
            )

    def test_hypothesis_limit(self):
        """假设数量达到上限时抛出异常"""
        service = GameService()
        game = service.create_game(GameDifficulty.CLASSIC)
        game_id = game.game_id

        # 先创建 20 条假设
        for i in range(20):
            service.create_hypothesis(
                game_id=game_id,
                title=f"假设 {i}",
                description="描述",
                inference_ids=[],
                suspect_id=None,
            )

        # 第 21 条应失败
        with pytest.raises(ValueError, match="假设记录已达上限"):
            service.create_hypothesis(
                game_id=game_id,
                title="超出上限的假设",
                description="描述",
                inference_ids=[],
                suspect_id=None,
            )
