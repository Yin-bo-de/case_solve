"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 环境
    environment: str = "development"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4-turbo-preview"

    # 日志
    log_level: str = "INFO"

    # Agent 上下文管理配置
    suspect_agent_max_history_messages: int = 20
    suspect_agent_max_history_tokens: int = 8000
    watson_chat_max_history_messages: int = 50
    watson_chat_max_history_tokens: int = 12000
    scene_agent_max_history_messages: int = 6
    scene_agent_max_history_tokens: int = 4000
    oracle_agent_max_context_tokens: int = 10000
    witness_agent_max_history_messages: int = 8
    expert_agent_max_history_messages: int = 6
    case_generator_max_output_tokens: int = 8000

    # P1-P5 feature flags（探案游戏「线索被使用」核心闭环改造）
    enable_clue_confrontation: bool = True        # P2: 出示线索质询
    enable_suspect_state_machine: bool = False    # P3: 嫌疑人状态机
    enable_strict_oracle: bool = False            # P4: Oracle 严格模式
    enable_solvability_validation: bool = False   # P5: 案件可解性校验
    strict_accusation_threshold: dict = {"easy": 0, "classic": 1, "hardcore": 2}

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
