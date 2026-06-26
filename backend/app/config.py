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
    enable_suspect_state_machine: bool = True    # P3: 嫌疑人状态机
    enable_strict_oracle: bool = True            # P4: Oracle 严格模式
    enable_solvability_validation: bool = True   # P5: 案件可解性校验
    strict_accusation_threshold: dict = {"easy": 0, "classic": 1, "hardcore": 2}

    # P6: Narrative Director feature flags
    enable_narrative_director: bool = True       # 叙事导演主开关
    enable_pressure_accumulation: bool = True    # 对话压力累积
    enable_story_beats: bool = True              # 故事节拍系统

    # 压力信号权重
    pressure_signal_weight_evasion: float = 0.15
    pressure_signal_weight_contradiction: float = 0.30
    pressure_signal_weight_over_explanation: float = 0.10
    pressure_signal_weight_emotional_leakage: float = 0.20
    pressure_signal_weight_inconsistency: float = 0.25
    pressure_signal_weight_deflection: float = 0.10

    # 压力阈值
    pressure_decay_per_turn: float = 0.0          # 无压力信号时衰减量（0=不衰减）
    pressure_threshold_pressured: float = 0.40    # 跨此阈值为 pressured
    pressure_threshold_broken: float = 0.75       # 跨此阈值为 broken

    # 叙事导演 LLM 配置
    narrative_director_max_history_messages: int = 10
    narrative_director_max_history_tokens: int = 4000
    narrative_director_temperature: float = 0.3

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
