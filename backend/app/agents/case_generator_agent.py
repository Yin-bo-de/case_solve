"""
案件生成Agent - 生成维多利亚时代背景的谋杀案
"""
from typing import Optional
from loguru import logger
from datetime import datetime
import uuid
import random

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

from app.config import get_settings
from app.models.case import Case, Suspect, Clue
from app.agents.prompts.case_prompts import case_generation_prompt
from app.agents._llm_helpers import invoke_with_retry


class CaseGeneratorAgent:
    """案件生成Agent类"""

    def __init__(self):
        """初始化案件生成器"""
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.8,  # 较高温度增加创造性
        )
        logger.info("[CaseGeneratorAgent] 初始化案件生成Agent")

    async def generate_case(self, difficulty: str = "classic") -> Case:
        """
        生成完整的维多利亚时代谋杀案

        Args:
            difficulty: 游戏难度 ("easy", "classic", "hardcore")

        Returns:
            完整的Case对象
        """
        logger.info(f"[CaseGeneratorAgent] 开始生成新案件 (难度: {difficulty})")

        settings = get_settings()

        # API key 缺失时直接降级，不做 LLM 调用
        if not settings.openai_api_key:
            logger.warning("[CaseGeneratorAgent] openai_api_key 未配置，使用 mock 降级")
            case_id = str(uuid.uuid4())
            case = self._generate_mock_case(case_id, difficulty)
            logger.info(f"[CaseGeneratorAgent] 案件生成完成: {case_id}")
            return case

        # 生成案件ID
        case_id = str(uuid.uuid4())
        chain = case_generation_prompt | self.llm | StrOutputParser()

        raw_data = await invoke_with_retry(
            chain=chain,
            inputs={"difficulty": difficulty},
            fallback_fn=lambda: None,  # None 时走下面的降级逻辑
            max_retries=2,
            timeout=45.0,
            parse_json=True,
        )

        if raw_data is None:
            logger.warning("[CaseGeneratorAgent] LLM 返回空，使用 mock 降级")
            case = self._generate_mock_case(case_id, difficulty)
            logger.info(f"[CaseGeneratorAgent] 案件生成完成: {case_id}")
            return case

        case = self._build_case_from_llm_output(case_id, difficulty, raw_data)
        logger.info(f"[CaseGeneratorAgent] 案件生成完成: {case_id}")
        return case

    def _generate_mock_case(self, case_id: str, difficulty: str) -> Case:
        """生成模拟案件数据（临时实现）"""
        # 真凶
        true_murderer_id = "suspect-1"

        # 嫌疑人列表
        suspects = [
            Suspect(
                id="suspect-1",
                name="玛莎·佩恩",
                age=42,
                background="死者的女管家，在布莱克伍德家工作10年，忠诚但薪资微薄",
                motive="多年来被死者克扣工资，还发现死者准备解雇她",
                timeline="昨晚9点在厨房准备茶具，10点回到自己房间",
                is_guilty=True,
                personality_traits=["谨慎", "敏感", "有条理"],
                secrets=["她偷偷拿了死者书房的一些金币"],
            ),
            Suspect(
                id="suspect-2",
                name="杰克·哈里森",
                age=28,
                background="死者的学徒，跟着死者3年，渴望成为独立古董商",
                motive="死者私吞了他发现的一件珍贵古董的收益",
                timeline="昨晚8点在自己房间整理账目，9点半后外出散步",
                is_guilty=False,
                personality_traits=["野心勃勃", "急躁", "诚实"],
                secrets=["他一直在偷偷联系其他古董商"],
            ),
            Suspect(
                id="suspect-3",
                name="伊丽莎白·克莱尔",
                age=31,
                background="死者的未婚妻，结婚在即，但似乎并不情愿",
                motive="发现死者实际上负债累累，婚约只是为了她的财产",
                timeline="昨晚7点到9点在客厅读书，之后回房休息",
                is_guilty=False,
                personality_traits=["优雅", "紧张", "聪明"],
                secrets=["她正准备解除婚约"],
            ),
        ]

        # 按难度决定红鲱鱼数量和 obviousness 范围
        # red_herring_count: 难度越高，误导线索越多
        # obviousness_range: 难度越高，线索越隐蔽
        difficulty_config = {
            "easy":     {"red_herring_count": 1, "real_range": (0.7, 1.0), "decoy_range": (0.3, 0.5)},
            "classic":  {"red_herring_count": 2, "real_range": (0.4, 0.8), "decoy_range": (0.2, 0.4)},
            "hardcore": {"red_herring_count": 3, "real_range": (0.1, 0.4), "decoy_range": (0.1, 0.3)},
        }
        config = difficulty_config.get(difficulty, difficulty_config["classic"])
        red_herring_count = config["red_herring_count"]
        real_lo, real_hi = config["real_range"]
        decoy_lo, decoy_hi = config["decoy_range"]

        # 5条预定义线索原型（不含 is_red_herring / obviousness，由难度决定）
        clue_templates = [
            dict(
                id="clue-1",
                description="壁炉灰烬中有未烧尽的信件残片，提到'金币'和'欺骗'",
                clue_type="physical",
                location="书房壁炉",
                related_suspect_ids=["suspect-1"],
            ),
            dict(
                id="clue-2",
                description="抽屉被撬开，物品散落一地，但值钱的东西还在",
                clue_type="physical",
                location="书房书桌",
                related_suspect_ids=["suspect-2"],
            ),
            dict(
                id="clue-3",
                description="窗台上有新鲜的泥渍，来自外面的街道",
                clue_type="physical",
                location="书房窗户",
                related_suspect_ids=["suspect-2", "suspect-3"],
            ),
            dict(
                id="clue-4",
                description="地毯有明显的拖拽痕迹，从书桌到壁炉",
                clue_type="physical",
                location="书房地毯",
                related_suspect_ids=["suspect-1"],
            ),
            dict(
                id="clue-5",
                description="一个精致的烛台，上面有血迹，放在角落",
                clue_type="physical",
                location="书房角落",
                related_suspect_ids=["suspect-1", "suspect-2", "suspect-3"],
            ),
        ]

        # clue-2、clue-3、clue-4 作为候选红鲱鱼池（clue-1、clue-5 始终是真实线索）
        decoy_pool = ["clue-2", "clue-3", "clue-4"]
        red_herring_ids = set(decoy_pool[:red_herring_count])

        clues = []
        for tmpl in clue_templates:
            is_rh = tmpl["id"] in red_herring_ids
            lo, hi = (decoy_lo, decoy_hi) if is_rh else (real_lo, real_hi)
            clues.append(Clue(
                **tmpl,
                is_red_herring=is_rh,
                obviousness=round(random.uniform(lo, hi), 2),
            ))

        logger.debug(
            f"[CaseGeneratorAgent] 难度={difficulty}, 红鲱鱼数={red_herring_count}, "
            f"obviousness范围(真实)={real_lo}~{real_hi}"
        )

        return Case(
            id=case_id,
            victim_name="埃德蒙·布莱克伍德",
            victim_background="富有的古董商人，在白教堂区有一间公寓",
            cause_of_death="头部钝器伤",
            time_of_death="昨晚9点到11点之间",
            location="白教堂区的阴暗公寓",
            date=datetime.utcnow(),
            suspects=suspects,
            clues=clues,
            summary="一位富有的古董商人被发现死在自己的书房中，现场一片狼藉...",
            murder_method="用烛台敲击头部致死，然后试图伪造入室抢劫",
            true_murderer_id=true_murderer_id,
            investigation_locations=["书房", "客厅", "厨房", "嫌疑人房间"],
        )

    def _build_case_from_llm_output(self, case_id: str, difficulty: str, data: dict) -> Case:
        """将 LLM 返回的 JSON 转换为 Case 对象，补充 ID/时间戳/obviousness 等"""
        difficulty_config = {
            "easy":     {"red_herring_count": 1, "real_range": (0.7, 1.0), "decoy_range": (0.3, 0.5)},
            "classic":  {"red_herring_count": 2, "real_range": (0.4, 0.8), "decoy_range": (0.2, 0.4)},
            "hardcore": {"red_herring_count": 3, "real_range": (0.1, 0.4), "decoy_range": (0.1, 0.3)},
        }
        config = difficulty_config.get(difficulty, difficulty_config["classic"])
        real_lo, real_hi = config["real_range"]
        decoy_lo, decoy_hi = config["decoy_range"]

        # 构建嫌疑人（补充 ID）
        suspects = []
        for i, s in enumerate(data["suspects"]):
            suspects.append(Suspect(
                id=f"suspect-{i+1}",
                **{k: v for k, v in s.items()},
            ))

        true_murderer_id = suspects[data["true_murderer_index"]].id

        # 构建线索（补充 ID / obviousness）
        clues = []
        for i, c in enumerate(data["clues"]):
            is_rh = c.get("is_red_herring", False)
            lo, hi = (decoy_lo, decoy_hi) if is_rh else (real_lo, real_hi)
            # related_suspect_indices → related_suspect_ids
            related_ids = [suspects[idx].id for idx in c.get("related_suspect_indices", []) if idx < len(suspects)]
            clues.append(Clue(
                id=f"clue-{i+1}",
                description=c["description"],
                clue_type=c.get("clue_type", "physical"),
                location=c.get("location"),
                related_suspect_ids=related_ids,
                is_red_herring=is_rh,
                obviousness=round(random.uniform(lo, hi), 2),
            ))

        return Case(
            id=case_id,
            victim_name=data["victim_name"],
            victim_background=data["victim_background"],
            cause_of_death=data["cause_of_death"],
            time_of_death=data["time_of_death"],
            location=data["location"],
            date=datetime.utcnow(),
            suspects=suspects,
            clues=clues,
            summary=data["summary"],
            murder_method=data["murder_method"],
            true_murderer_id=true_murderer_id,
            investigation_locations=data.get("investigation_locations", []),
        )


# 全局案件生成器实例
_case_generator: Optional[CaseGeneratorAgent] = None


def get_case_generator() -> CaseGeneratorAgent:
    """获取案件生成器单例"""
    global _case_generator
    if _case_generator is None:
        _case_generator = CaseGeneratorAgent()
    return _case_generator
