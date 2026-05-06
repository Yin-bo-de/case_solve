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
from app.models.case import Case, Suspect, Clue, Scene, SceneObject, Witness, Expert, ExpertKeyFinding, SuspectStatement
from app.agents.prompts.case_prompts import case_generation_prompt, suspect_statements_generation_prompt
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
            max_tokens=settings.case_generator_max_output_tokens,  # 防止大型案件 JSON 被截断
        )
        logger.info("[CaseGeneratorAgent] 初始化案件生成Agent")

    async def generate_case(self, difficulty: str = "classic") -> Case:
        """
        生成完整的维多利亚时代谋杀案。
        三阶段流程：A（主体生成）→ B（statements 二阶段）→ C（可解性校验）。
        阶段 C 失败时整体重试最多 2 次，仍失败则回退 mock case。

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

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            case_id = str(uuid.uuid4())
            logger.info(f"[CaseGeneratorAgent] 第 {attempt}/{max_attempts} 次尝试生成案件")

            # 阶段 A：生成案件主体
            chain = case_generation_prompt | self.llm | StrOutputParser()
            raw_data = await invoke_with_retry(
                chain=chain,
                inputs={"difficulty": difficulty},
                fallback_fn=lambda: None,
                max_retries=2,
                timeout=120.0,
                parse_json=True,
            )

            if raw_data is None:
                logger.warning(f"[CaseGeneratorAgent] 第 {attempt} 次 LLM 返回空")
                if attempt == max_attempts:
                    logger.warning("[CaseGeneratorAgent] 已达最大重试次数，使用 mock 降级")
                    return self._generate_mock_case(case_id, difficulty)
                continue

            case = self._build_case_from_llm_output(case_id, difficulty, raw_data)

            # 阶段 B：二阶段生成 suspect statements
            suspects_with_statements = await self._generate_suspect_statements(case, difficulty)
            case = case.model_copy(update={"suspects": suspects_with_statements})

            # 阶段 C：可解性校验
            errors = self._validate_solvability(case)
            if not errors:
                logger.info(f"[CaseGeneratorAgent] 案件生成完成: {case_id}")
                return case

            logger.warning(
                f"[CaseGeneratorAgent] 第 {attempt} 次可解性校验失败: {errors}"
            )
            if attempt == max_attempts:
                logger.warning("[CaseGeneratorAgent] 已达最大重试次数，使用 mock 降级")
                return self._generate_mock_case(case_id, difficulty)

        # 理论上不会到达这里，作为兜底
        case_id = str(uuid.uuid4())
        return self._generate_mock_case(case_id, difficulty)

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

        # 按难度决定 obviousness 范围
        # obviousness_range: 难度越高，线索越隐蔽
        difficulty_config = {
            "easy":     {"real_range": (0.7, 1.0),
                         "witness_credibilities": [0.85, 0.9], "witness_lying": [False, False]},
            "classic":  {"real_range": (0.4, 0.8),
                         "witness_credibilities": [0.75, 0.6], "witness_lying": [False, True]},
            "hardcore": {"real_range": (0.1, 0.4),
                         "witness_credibilities": [0.5, 0.4], "witness_lying": [True, False]},
        }
        config = difficulty_config.get(difficulty, difficulty_config["classic"])
        real_lo, real_hi = config["real_range"]
        witness_creds = config["witness_credibilities"]
        witness_lying = config["witness_lying"]

        # 5条预定义线索原型（不含 obviousness，由难度决定）
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

        clues = []
        for tmpl in clue_templates:
            clues.append(Clue(
                **tmpl,
                obviousness=round(random.uniform(real_lo, real_hi), 2),
            ))

        logger.debug(
            f"[CaseGeneratorAgent] 难度={difficulty}, "
            f"obviousness范围={real_lo}~{real_hi}"
        )

        # 构造 3 个 scenes，将所有线索挂到对应 objects 上
        # 书房承载大部分物证，客厅和厨房提供人物背景线索
        scenes = [
            Scene(
                id="scene-study",
                name="书房",
                description="宽敞阴暗的书房，高大的红木书架沿墙而立，壁炉里炭火已灭，厚重的羊毛地毯上隐约有污迹",
                npc_persona="沉默的管家，举止谨慎，对死者忠诚但内心藏有秘密",
                objects=[
                    SceneObject(
                        id="obj-fireplace",
                        name="壁炉",
                        description="大理石壁炉，炉膛内有未完全燃尽的灰烬",
                        hidden_clue_ids=["clue-1"],
                        search_hints=["仔细检查灰烬", "寻找未烧尽的纸片"],
                    ),
                    SceneObject(
                        id="obj-desk",
                        name="书桌",
                        description="胡桃木书桌，一个抽屉被强行撬开，文件散落一地",
                        hidden_clue_ids=["clue-2"],
                        search_hints=["检查被撬的抽屉", "翻看散落的文件"],
                    ),
                    SceneObject(
                        id="obj-carpet",
                        name="地毯",
                        description="厚重的波斯地毯，有明显的拖拽痕迹",
                        hidden_clue_ids=["clue-4"],
                        search_hints=["观察地毯纹路", "追踪拖拽痕迹的方向"],
                    ),
                ],
            ),
            Scene(
                id="scene-living-room",
                name="客厅",
                description="维多利亚式客厅，墙上挂着几幅油画，靠窗有一张阅读椅，窗台上摆着枯萎的鲜花",
                npc_persona="焦虑的女仆，经常在此打扫，昨晚在场",
                objects=[
                    SceneObject(
                        id="obj-window",
                        name="窗户",
                        description="朝向街道的落地窗，窗台上有新鲜的泥渍",
                        hidden_clue_ids=["clue-3"],
                        search_hints=["检查窗台的泥渍", "查看窗户是否有被撬开的痕迹"],
                    ),
                    SceneObject(
                        id="obj-corner",
                        name="角落烛台架",
                        description="铸铁烛台架，上面那只精致的铜烛台不见了",
                        hidden_clue_ids=["clue-5"],
                        search_hints=["注意烛台架上的空位", "检查周围地面"],
                    ),
                    SceneObject(
                        id="obj-armchair",
                        name="扶手椅",
                        description="靠近壁炉的皮质扶手椅，座垫上有轻微的凹陷",
                        hidden_clue_ids=[],
                        search_hints=["检查椅垫下方", "观察靠背是否有异常"],
                    ),
                ],
            ),
            Scene(
                id="scene-kitchen",
                name="厨房",
                description="昏暗的厨房，铜质锅具挂在墙上，案板上还留有昨晚准备茶具的痕迹",
                npc_persona="沉默的厨娘，不苟言笑，对宅内发生的事一清二楚",
                objects=[
                    SceneObject(
                        id="obj-tea-cabinet",
                        name="茶具柜",
                        description="放置茶具的木质橱柜，昨晚管家在这里准备茶水",
                        hidden_clue_ids=[],
                        search_hints=["检查茶具是否齐全", "查看柜内有无异常"],
                    ),
                    SceneObject(
                        id="obj-back-door",
                        name="后门",
                        description="通向后院的铁门，门锁有轻微磨损",
                        hidden_clue_ids=[],
                        search_hints=["检查门锁状态", "查看门外的脚印"],
                    ),
                    SceneObject(
                        id="obj-counter",
                        name="操作台",
                        description="石质操作台，台面干净，但抹布被随意丢在一旁",
                        hidden_clue_ids=[],
                        search_hints=["检查抹布上是否有污迹", "查看台面边缘"],
                    ),
                ],
            ),
        ]

        # 集中维护交叉引用关系，便于单点修改
        _MOCK_WITNESS_OBS = {
            "witness-1": "昨晚 9:30 看见杰克·哈里森（suspect-2）从公寓后门匆匆离开，神色慌张",
            "witness-2": "昨晚约 10 点，有一个穿深色斗篷的人进过那栋楼，背影与伊丽莎白·克莱尔（suspect-3）身形相似",
        }

        witnesses = [
            Witness(
                id="witness-1",
                name="莉莉·哈丁",
                age=34,
                occupation="洗衣女工",
                relationship_to_case="死者公寓隔壁的住户",
                timeline="昨晚 8 点到 10 点一直在自家阳台晾衣服，之后回屋睡觉",
                personality_traits=["热心", "好奇", "健谈"],
                secrets=[],
                key_observations=[_MOCK_WITNESS_OBS["witness-1"]],
                is_lying_for_someone=witness_lying[0],
                bribed_by_suspect_id=None,
                related_suspect_ids=["suspect-2"],
                credibility=witness_creds[0],
            ),
            Witness(
                id="witness-2",
                name="老汤姆",
                age=11,
                occupation="街角报童",
                relationship_to_case="在案发楼栋附近卖报，昨晚有所目击",
                timeline="昨晚 9:30 到 10:30 在街角卖晚报，约 10 点 15 分收摊回家",
                personality_traits=["机灵", "胆小", "记性好"],
                secrets=[],
                key_observations=[_MOCK_WITNESS_OBS["witness-2"]],
                is_lying_for_someone=witness_lying[1],
                bribed_by_suspect_id=("suspect-3" if witness_lying[1] else None),
                related_suspect_ids=["suspect-3"],
                credibility=witness_creds[1],
            ),
        ]

        experts = [
            Expert(
                id="expert-1",
                name="塞西尔·哈罗德医生",
                title="皇家法医、苏格兰场顾问",
                expertise=["法医病理", "钝器伤分析", "死亡时间推断"],
                preliminary_report=(
                    "经本人现场初步检验，死者埃德蒙·布莱克伍德头部右侧太阳穴处存在明显钝器伤，"
                    "创口形态呈圆弧状，与直径约 5 厘米的金属物体吻合。"
                    "根据尸体僵硬程度及体温推算，死亡时间约为昨晚 9 点 45 分至 10 点 30 分，"
                    "误差在 30 分钟以内。"
                    "现场采集到的黄铜碎屑样品疑与书房角落的烛台架残件成分相符，"
                    "化验结果将在两日内出具。"
                ),
                key_findings=[
                    ExpertKeyFinding(
                        topic="凶器特征",
                        finding="创口形态与黄铜烛台匹配，烛台上血迹经初步鉴定为死者血型",
                        related_clue_ids=["clue-5"],
                    ),
                    ExpertKeyFinding(
                        topic="死亡时间",
                        finding="死亡时间窗口约为昨晚 9:45 至 10:30，误差 ±30 分钟",
                        related_clue_ids=["clue-5"],
                    ),
                ],
                methodology_notes=[
                    "死亡时间推断基于尸体僵硬度与体温，误差约 ±30 分钟",
                    "黄铜碎屑成分比对结果为初步判断，正式化验尚未完成",
                ],
                related_clue_ids=["clue-5"],
            ),
        ]

        # 为 mock case 的嫌疑人生成 fallback statements（符合可解性约束）
        suspects_with_statements = self._build_fallback_statements(suspects, clues)

        return Case(
            id=case_id,
            victim_name="埃德蒙·布莱克伍德",
            victim_background="富有的古董商人，在白教堂区有一间公寓",
            cause_of_death="头部钝器伤",
            time_of_death="昨晚9点到11点之间",
            location="白教堂区的阴暗公寓",
            date=datetime.utcnow(),
            suspects=suspects_with_statements,
            clues=clues,
            summary="一位富有的古董商人被发现死在自己的书房中，现场一片狼藉...",
            murder_method="用烛台敲击头部致死，然后试图伪造入室抢劫",
            true_murderer_id=true_murderer_id,
            scenes=scenes,
            investigation_locations=[s.name for s in scenes],
            witnesses=witnesses,
            experts=experts,
        )

    def _build_case_from_llm_output(self, case_id: str, difficulty: str, data: dict) -> Case:
        """将 LLM 返回的 JSON 转换为 Case 对象，补充 ID/时间戳/obviousness 等"""
        difficulty_config = {
            "easy":     {"real_range": (0.7, 1.0)},
            "classic":  {"real_range": (0.4, 0.8)},
            "hardcore": {"real_range": (0.1, 0.4)},
        }
        config = difficulty_config.get(difficulty, difficulty_config["classic"])
        real_lo, real_hi = config["real_range"]

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
            # related_suspect_indices → related_suspect_ids
            related_ids = [suspects[idx].id for idx in c.get("related_suspect_indices", []) if idx < len(suspects)]
            clues.append(Clue(
                id=f"clue-{i+1}",
                description=c["description"],
                clue_type=c.get("clue_type", "physical"),
                location=c.get("location"),
                related_suspect_ids=related_ids,
                obviousness=round(random.uniform(real_lo, real_hi), 2),
                investigation_hint=c.get("investigation_hint"),
                chain_next_clue_index=c.get("chain_next_clue_index"),
            ))

        # 解析 scenes（若 LLM 未返回则生成简单的占位 scenes）
        scenes = self._parse_scenes_from_data(data, clues)

        # 解析证人和专家
        witnesses = self._parse_witnesses_from_data(data, suspects)
        experts = self._parse_experts_from_data(data, clues)

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
            scenes=scenes,
            # investigation_locations 作为 scenes.name 的镜像
            investigation_locations=[s.name for s in scenes],
            witnesses=witnesses,
            experts=experts,
        )

    def _parse_scenes_from_data(self, data: dict, clues: list) -> list:
        """
        将 LLM 返回的 scenes JSON 转换为 Scene 对象列表。
        若 LLM 未返回 scenes 或解析失败，则生成 fallback scenes。
        """
        raw_scenes = data.get("scenes", [])
        if not raw_scenes:
            logger.warning("[CaseGeneratorAgent] LLM 未返回 scenes，使用 fallback 构造")
            return self._build_fallback_scenes(clues)

        try:
            scenes = []
            for i, s in enumerate(raw_scenes):
                objects = []
                for j, o in enumerate(s.get("objects", [])):
                    objects.append(SceneObject(
                        id=o.get("id") or f"obj-{i+1}-{j+1}",
                        name=o["name"],
                        description=o.get("description", ""),
                        hidden_clue_ids=o.get("hidden_clue_ids", []),
                        search_hints=o.get("search_hints", []),
                    ))
                scenes.append(Scene(
                    id=s.get("id") or f"scene-{i+1}",
                    name=s["name"],
                    description=s.get("description", ""),
                    atmosphere_image=s.get("atmosphere_image"),
                    npc_persona=s.get("npc_persona", ""),
                    objects=objects,
                ))
            logger.info(f"[CaseGeneratorAgent] 解析 scenes 成功 count={len(scenes)}")
            return scenes
        except Exception as e:
            logger.warning(f"[CaseGeneratorAgent] scenes 解析异常，使用 fallback: {e}")
            return self._build_fallback_scenes(clues)

    def _build_fallback_scenes(self, clues: list) -> list:
        """
        当 LLM 不返回 scenes 时，将所有线索平均分配到 2 个 fallback scenes 中。
        保证所有线索至少在一个 object 的 hidden_clue_ids 中出现。
        """
        mid = max(1, len(clues) // 2)
        first_half = [c.id for c in clues[:mid]]
        second_half = [c.id for c in clues[mid:]]
        return [
            Scene(
                id="scene-study",
                name="书房",
                description="案发现场的书房，线索散落各处",
                npc_persona="沉默的看守，目睹过一些异常",
                objects=[
                    SceneObject(
                        id="obj-study-1",
                        name="书桌",
                        description="宽大的书桌，物品凌乱",
                        hidden_clue_ids=first_half,
                        search_hints=["仔细翻查抽屉", "检查桌面文件"],
                    ),
                    SceneObject(id="obj-study-2", name="书架", description="满是书籍的书架", hidden_clue_ids=[], search_hints=[]),
                    SceneObject(id="obj-study-3", name="壁炉", description="冷却的壁炉", hidden_clue_ids=[], search_hints=[]),
                ],
            ),
            Scene(
                id="scene-living-room",
                name="客厅",
                description="宽敞的维多利亚式客厅，光线昏暗",
                npc_persona="不安的女仆，似乎知道些什么",
                objects=[
                    SceneObject(
                        id="obj-living-1",
                        name="角落",
                        description="客厅角落，有些杂物",
                        hidden_clue_ids=second_half,
                        search_hints=["检查角落的物品", "注意地板痕迹"],
                    ),
                    SceneObject(id="obj-living-2", name="窗户", description="临街的窗户", hidden_clue_ids=[], search_hints=[]),
                    SceneObject(id="obj-living-3", name="扶手椅", description="皮质扶手椅", hidden_clue_ids=[], search_hints=[]),
                ],
            ),
            Scene(
                id="scene-kitchen",
                name="厨房",
                description="案发当晚有人在此活动的厨房",
                npc_persona="沉默的厨娘，知晓宅内动向",
                objects=[
                    SceneObject(id="obj-kitchen-1", name="操作台", description="石质操作台", hidden_clue_ids=[], search_hints=[]),
                    SceneObject(id="obj-kitchen-2", name="后门", description="通向后院的铁门", hidden_clue_ids=[], search_hints=[]),
                    SceneObject(id="obj-kitchen-3", name="茶具柜", description="存放茶具的橱柜", hidden_clue_ids=[], search_hints=[]),
                ],
            ),
        ]


    def _parse_witnesses_from_data(self, data: dict, suspects: list) -> list:
        """
        将 LLM 返回的 witnesses JSON 转换为 Witness 对象列表。
        若 LLM 未返回或解析失败，生成 fallback 证人。
        """
        raw_witnesses = data.get("witnesses", [])
        if not raw_witnesses:
            logger.warning("[CaseGeneratorAgent] LLM 未返回 witnesses，使用 fallback")
            return self._build_fallback_witnesses(suspects)

        try:
            witnesses = []
            for i, w in enumerate(raw_witnesses):
                # related_suspect_indices → related_suspect_ids
                related_ids = [
                    suspects[idx].id
                    for idx in w.get("related_suspect_indices", [])
                    if idx < len(suspects)
                ]
                # 若关联嫌疑人为空，注入第一个非真凶作为兜底
                if not related_ids and suspects:
                    non_guilty = [s for s in suspects if not s.is_guilty]
                    related_ids = [non_guilty[0].id] if non_guilty else [suspects[0].id]
                    logger.warning(
                        f"[CaseGeneratorAgent] witness-{i+1} 关联嫌疑人为空，注入兜底: {related_ids}"
                    )

                # bribed_by_suspect_index → bribed_by_suspect_id
                bribed_idx = w.get("bribed_by_suspect_index")
                bribed_id = suspects[bribed_idx].id if (bribed_idx is not None and bribed_idx < len(suspects)) else None

                witness = Witness(
                    id=f"witness-{i+1}",
                    name=w["name"],
                    age=w.get("age", 30),
                    occupation=w.get("occupation", "市民"),
                    relationship_to_case=w.get("relationship_to_case", "案件相关人员"),
                    timeline=w.get("timeline", ""),
                    personality_traits=w.get("personality_traits", []),
                    secrets=w.get("secrets", []),
                    key_observations=w.get("key_observations", []),
                    is_lying_for_someone=w.get("is_lying_for_someone", False),
                    bribed_by_suspect_id=bribed_id,
                    related_suspect_ids=related_ids,
                    credibility=w.get("credibility", 0.7),
                )
                witnesses.append(witness)

            logger.info(f"[CaseGeneratorAgent] 解析 witnesses 成功 count={len(witnesses)}")
            return witnesses
        except Exception as e:
            logger.warning(f"[CaseGeneratorAgent] witnesses 解析异常，使用 fallback: {e}")
            return self._build_fallback_witnesses(suspects)

    def _parse_experts_from_data(self, data: dict, clues: list) -> list:
        """
        将 LLM 返回的 experts JSON 转换为 Expert 对象列表。
        若 LLM 未返回或解析失败，生成 fallback 专家。
        """
        raw_experts = data.get("experts", [])
        if not raw_experts:
            logger.warning("[CaseGeneratorAgent] LLM 未返回 experts，使用 fallback")
            return self._build_fallback_expert(clues)

        try:
            experts = []
            for i, e in enumerate(raw_experts):
                # related_clue_indices → related_clue_ids
                related_clue_ids = [
                    clues[idx].id
                    for idx in e.get("related_clue_indices", [])
                    if idx < len(clues)
                ]
                if not related_clue_ids and clues:
                    # 找第一条物证线索
                    real_clue = next(
                        (c for c in clues if c.clue_type in ("physical", "forensic")),
                        clues[0]
                    )
                    related_clue_ids = [real_clue.id]
                    logger.warning(
                        f"[CaseGeneratorAgent] expert-{i+1} 关联线索为空，注入兜底: {related_clue_ids}"
                    )

                # key_findings 中的 related_clue_indices → related_clue_ids
                key_findings = []
                for kf in e.get("key_findings", []):
                    kf_clue_ids = [
                        clues[idx].id
                        for idx in kf.get("related_clue_indices", [])
                        if idx < len(clues)
                    ]
                    key_findings.append(ExpertKeyFinding(
                        topic=kf.get("topic", ""),
                        finding=kf.get("finding", ""),
                        related_clue_ids=kf_clue_ids,
                    ))

                expert = Expert(
                    id=f"expert-{i+1}",
                    name=e["name"],
                    title=e.get("title", "法医"),
                    expertise=e.get("expertise", []),
                    preliminary_report=e.get("preliminary_report", ""),
                    key_findings=key_findings,
                    methodology_notes=e.get("methodology_notes", []),
                    related_clue_ids=related_clue_ids,
                )
                experts.append(expert)

            logger.info(f"[CaseGeneratorAgent] 解析 experts 成功 count={len(experts)}")
            return experts
        except Exception as e:
            logger.warning(f"[CaseGeneratorAgent] experts 解析异常，使用 fallback: {e}")
            return self._build_fallback_expert(clues)

    def _build_fallback_witnesses(self, suspects: list) -> list:
        """当 LLM 未返回 witnesses 时，生成 1 个泛用证人"""
        non_guilty = [s for s in suspects if not s.is_guilty]
        ref_suspect = non_guilty[0] if non_guilty else (suspects[0] if suspects else None)
        related_ids = [ref_suspect.id] if ref_suspect else []
        obs = f"案发当晚在案发地点附近看到过可疑人员" if not ref_suspect else \
              f"案发当晚看到过 {ref_suspect.name} 在附近活动"
        return [
            Witness(
                id="witness-1",
                name="无名目击者",
                age=35,
                occupation="附近居民",
                relationship_to_case="案发地点附近居住",
                timeline="案发当晚在附近活动",
                personality_traits=["谨慎"],
                secrets=[],
                key_observations=[obs],
                is_lying_for_someone=False,
                bribed_by_suspect_id=None,
                related_suspect_ids=related_ids,
                credibility=0.65,
            )
        ]

    # ------------------------------------------------------------------
    # 阶段 B：Suspect Statements 二阶段生成（P5）
    # ------------------------------------------------------------------

    async def _generate_suspect_statements(self, case: Case, difficulty: str = "classic") -> list:
        """
        二阶段：为 case 中每位嫌疑人生成 statements。
        先尝试 LLM 生成，弱绑定校验失败则自修复重试 1 次，
        仍失败则回退到 _build_fallback_statements。
        """
        settings = get_settings()
        if not settings.openai_api_key:
            logger.warning("[CaseGeneratorAgent] api_key 缺失，statements 使用 fallback")
            return self._build_fallback_statements(case.suspects, case.clues)

        chain = suspect_statements_generation_prompt | self.llm | StrOutputParser()
        clues_block = self._build_clues_block(case)
        suspects_block = self._build_suspects_block(case)

        inputs = {
            "case_summary": case.summary,
            "murder_method": case.murder_method,
            "true_murderer_id": case.true_murderer_id,
            "difficulty": difficulty,
            "clues_block": clues_block,
            "suspects_block": suspects_block,
        }

        # 第一次尝试
        raw_data = await invoke_with_retry(
            chain=chain,
            inputs=inputs,
            fallback_fn=lambda: None,
            max_retries=1,
            timeout=90.0,
            parse_json=True,
        )

        suspects_with_statements = self._parse_statements_from_llm_output(raw_data, case)
        if suspects_with_statements:
            logger.info(f"[CaseGeneratorAgent] statements LLM 生成成功")
            return suspects_with_statements

        # 第一次失败，自修复重试：在 human prompt 中追加约束提醒
        logger.warning("[CaseGeneratorAgent] statements 首次生成失败/校验不通过，进入自修复重试")
        inputs["suspects_block"] = suspects_block + "\n\n【重要提醒】请确保所有 refutable_by_clue_ids 严格指向上述线索列表中存在且 related_suspect_ids 包含该嫌疑人的线索。"
        raw_data = await invoke_with_retry(
            chain=chain,
            inputs=inputs,
            fallback_fn=lambda: None,
            max_retries=1,
            timeout=90.0,
            parse_json=True,
        )

        suspects_with_statements = self._parse_statements_from_llm_output(raw_data, case)
        if suspects_with_statements:
            logger.info(f"[CaseGeneratorAgent] statements 自修复重试成功")
            return suspects_with_statements

        # 重试仍失败，fallback
        logger.warning("[CaseGeneratorAgent] statements 重试仍失败，使用 fallback")
        return self._build_fallback_statements(case.suspects, case.clues)

    def _build_clues_block(self, case: Case) -> str:
        """将 case.clues 格式化为 prompt 可用的文本块"""
        lines = []
        for c in case.clues:
            lines.append(f"- clue_id: {c.id}")
            lines.append(f"  description: {c.description}")
            lines.append(f"  related_suspect_ids: {c.related_suspect_ids}")
            lines.append("")
        return "\n".join(lines)

    def _build_suspects_block(self, case: Case) -> str:
        """将 case.suspects 格式化为 prompt 可用的文本块"""
        lines = []
        for s in case.suspects:
            lines.append(f"- suspect_id: {s.id}")
            lines.append(f"  name: {s.name}")
            lines.append(f"  background: {s.background}")
            lines.append(f"  motive: {s.motive}")
            lines.append(f"  timeline: {s.timeline}")
            lines.append(f"  is_guilty: {s.is_guilty}")
            lines.append("")
        return "\n".join(lines)

    def _parse_statements_from_llm_output(self, data: Optional[dict], case: Case) -> list:
        """
        解析 LLM 返回的 statements JSON，校验弱绑定约束。
        返回 Suspect 列表（含 statements），若校验失败返回空列表。
        """
        if not data or not isinstance(data, dict):
            return []

        suspects_statements = data.get("suspects_statements", [])
        if not suspects_statements:
            return []

        # 构建 clue_id -> related_suspect_ids 映射
        clue_related_map = {c.id: set(c.related_suspect_ids) for c in case.clues}
        result_suspects = []

        for ss in suspects_statements:
            suspect_id = ss.get("suspect_id", "")
            # 找到对应的 suspect 对象
            suspect = next((s for s in case.suspects if s.id == suspect_id), None)
            if not suspect:
                logger.warning(f"[CaseGeneratorAgent] statements 解析：找不到 suspect_id={suspect_id}")
                return []

            raw_statements = ss.get("statements", [])
            if not raw_statements or len(raw_statements) < 2:
                logger.warning(f"[CaseGeneratorAgent] suspect={suspect_id} statements 数量不足（<2）")
                return []

            parsed_statements = []
            for raw in raw_statements:
                stmt = SuspectStatement(
                    id=raw.get("id", f"stmt-{suspect_id}-{len(parsed_statements)+1}"),
                    content=raw.get("content", ""),
                    is_lie=raw.get("is_lie", False),
                    refutable_by_clue_ids=raw.get("refutable_by_clue_ids", []),
                    revealed_when_broken=raw.get("revealed_when_broken", False),
                )
                # 弱绑定校验
                if not self._validate_statement_bindings(stmt, suspect_id, clue_related_map):
                    logger.warning(
                        f"[CaseGeneratorAgent] suspect={suspect_id} stmt={stmt.id} "
                        f"弱绑定校验失败: refutable_by_clue_ids={stmt.refutable_by_clue_ids}"
                    )
                    return []
                parsed_statements.append(stmt)

            # 替换 suspect 的 statements
            new_suspect = suspect.model_copy(update={"statements": parsed_statements})
            result_suspects.append(new_suspect)

        # 确保所有 suspect 都被覆盖
        if len(result_suspects) != len(case.suspects):
            logger.warning(
                f"[CaseGeneratorAgent] statements 解析：嫌疑人数量不匹配 "
                f"({len(result_suspects)} != {len(case.suspects)})"
            )
            return []

        return result_suspects

    def _validate_statement_bindings(
        self,
        stmt: SuspectStatement,
        suspect_id: str,
        clue_related_map: dict,
    ) -> bool:
        """
        弱绑定约束校验：
        1. refutable_by_clue_ids 中的每个 clue_id 必须存在于 clue_related_map 中
        2. 每个 clue_id 对应的 related_suspect_ids 必须包含当前 suspect_id
        """
        for clue_id in stmt.refutable_by_clue_ids:
            if clue_id not in clue_related_map:
                return False
            if suspect_id not in clue_related_map[clue_id]:
                return False
        return True

    def _build_fallback_statements(self, suspects: list, clues: list) -> list:
        """
        为 mock case 或 LLM 失败回退生成符合可解性约束的 statements。
        确保：至少真凶有 ≥2 条谎言，每条谎言有可反驳线索。
        """
        if not suspects or not clues:
            return suspects

        # 构建 clue_id -> related_suspect_ids 映射
        clue_related_map = {c.id: set(c.related_suspect_ids) for c in clues}

        def _find_refutable_clues(suspect_id: str) -> list:
            """找到所有 related_suspect_ids 包含该 suspect 的 clue_id"""
            return [cid for cid, related in clue_related_map.items() if suspect_id in related]

        result = []
        for suspect in suspects:
            refutable = _find_refutable_clues(suspect.id)
            statements = []

            if suspect.is_guilty:
                # 真凶：2 条谎言 + 1-2 条真话
                # 谎言1：关于时间线
                if len(refutable) >= 1:
                    statements.append(SuspectStatement(
                        id=f"stmt-{suspect.id}-1",
                        content=f"我当晚根本没有接近过死者，此事与我毫无关联。",
                        is_lie=True,
                        refutable_by_clue_ids=[refutable[0]],
                        revealed_when_broken=False,
                    ))
                # 谎言2：关于动机
                if len(refutable) >= 2:
                    statements.append(SuspectStatement(
                        id=f"stmt-{suspect.id}-2",
                        content=f"我与死者之间从无嫌隙，绝无任何伤害他的动机。",
                        is_lie=True,
                        refutable_by_clue_ids=[refutable[1]],
                        revealed_when_broken=True,
                    ))
                # 真话1
                statements.append(SuspectStatement(
                    id=f"stmt-{suspect.id}-3",
                    content=f"我承认我对此案知情，但我绝没有插手任何伤害之事。",
                    is_lie=False,
                    refutable_by_clue_ids=[],
                    revealed_when_broken=False,
                ))
                # 真话2（可选）
                statements.append(SuspectStatement(
                    id=f"stmt-{suspect.id}-4",
                    content=f"我是无辜的。无论证据如何指向我，我的良心是清白的。",
                    is_lie=False,
                    refutable_by_clue_ids=[],
                    revealed_when_broken=False,
                ))
            else:
                # 无辜嫌疑人：0-1 条谎言 + 2-3 条真话
                if refutable and random.random() < 0.3:
                    # 30% 概率有 1 条小谎言
                    statements.append(SuspectStatement(
                        id=f"stmt-{suspect.id}-1",
                        content=f"我对死者没有任何敌意，此案与我无关。",
                        is_lie=True,
                        refutable_by_clue_ids=[refutable[0]],
                        revealed_when_broken=False,
                    ))
                # 真话
                statements.append(SuspectStatement(
                    id=f"stmt-{suspect.id}-2",
                    content=f"我与死者平日相处融洽，我无法想象谁会想伤害他。",
                    is_lie=False,
                    refutable_by_clue_ids=[],
                    revealed_when_broken=False,
                ))
                statements.append(SuspectStatement(
                    id=f"stmt-{suspect.id}-3",
                    content=f"我承认我与死者之间曾有些许不快，但那绝不足以成为我的杀人动机。",
                    is_lie=False,
                    refutable_by_clue_ids=[],
                    revealed_when_broken=False,
                ))
                statements.append(SuspectStatement(
                    id=f"stmt-{suspect.id}-4",
                    content=f"我是清白的，我没有理由对死者痛下杀手。",
                    is_lie=False,
                    refutable_by_clue_ids=[],
                    revealed_when_broken=False,
                ))

            new_suspect = suspect.model_copy(update={"statements": statements})
            result.append(new_suspect)

        return result

    # ------------------------------------------------------------------
    # 阶段 C：可解性校验（P5）
    # ------------------------------------------------------------------

    def _validate_solvability(self, case: Case) -> list:
        """
        校验案件是否满足可解性强约束。
        返回错误信息列表，空列表表示校验通过。
        """
        errors = []
        settings = get_settings()
        if not settings.enable_solvability_validation:
            return errors

        # 收集所有被 refutable_by_clue_ids 引用的 clue_id
        referenced_clue_ids = set()
        for s in case.suspects:
            for stmt in s.statements:
                referenced_clue_ids.update(stmt.refutable_by_clue_ids)

        # 校验1：至少 2 条 clue 被 statements 引用
        if len(referenced_clue_ids) < 2:
            errors.append(
                f"可解性校验失败：被 statements 引用的线索不足 2 条（实际 {len(referenced_clue_ids)} 条）"
            )

        # 校验2：至少 1 名嫌疑人有 ≥2 条谎言且每条都有可反驳线索
        has_lie_chain = False
        for s in case.suspects:
            lie_stmts = [
                stmt for stmt in s.statements
                if stmt.is_lie and stmt.refutable_by_clue_ids
            ]
            if len(lie_stmts) >= 2:
                has_lie_chain = True
                break
        if not has_lie_chain:
            errors.append(
                "可解性校验失败：没有嫌疑人持有 ≥2 条可反驳的谎言链"
            )

        # 校验3：每条 statement 的 refutable_by_clue_ids 都指向真实 clue 且关联匹配
        clue_ids_in_case = {c.id for c in case.clues}
        clue_related_map = {c.id: set(c.related_suspect_ids) for c in case.clues}
        for s in case.suspects:
            for stmt in s.statements:
                for clue_id in stmt.refutable_by_clue_ids:
                    if clue_id not in clue_ids_in_case:
                        errors.append(
                            f"弱绑定校验失败：suspect={s.id} stmt={stmt.id} "
                            f"引用了不存在的 clue_id={clue_id}"
                        )
                    elif s.id not in clue_related_map.get(clue_id, set()):
                        errors.append(
                            f"弱绑定校验失败：suspect={s.id} stmt={stmt.id} "
                            f"引用的 clue_id={clue_id} 未关联该嫌疑人"
                        )

        # 校验4：真凶至少持有 1 条谎言链（≥1 条可反驳的谎言）
        guilty_suspect = next((s for s in case.suspects if s.is_guilty), None)
        if guilty_suspect:
            guilty_lies = [
                stmt for stmt in guilty_suspect.statements
                if stmt.is_lie and stmt.refutable_by_clue_ids
            ]
            if len(guilty_lies) < 1:
                errors.append(
                    f"可解性校验失败：真凶 {guilty_suspect.id} 没有可反驳的谎言"
                )
        else:
            errors.append("可解性校验失败：案件中没有标记真凶")

        return errors

    def _build_fallback_expert(self, clues: list) -> list:
        """当 LLM 未返回 experts 时，生成 1 个基于物证的法医"""
        real_clue = next(
            (c for c in clues if c.clue_type in ("physical", "forensic")),
            clues[0] if clues else None
        )
        related_ids = [real_clue.id] if real_clue else []
        report = "经初步法医检验，死者系遭外力侵害致死。死亡时间估计为案发当晚，具体时间窗口待进一步分析确认。"
        return [
            Expert(
                id="expert-1",
                name="法医检验员",
                title="法医",
                expertise=["法医病理"],
                preliminary_report=report,
                key_findings=[
                    ExpertKeyFinding(
                        topic="死因",
                        finding="外力侵害致死，具体凶器待确认",
                        related_clue_ids=related_ids,
                    )
                ] if related_ids else [],
                methodology_notes=["死亡时间推断存在误差，完整报告尚待出具"],
                related_clue_ids=related_ids,
            )
        ]


# 全局案件生成器实例
_case_generator: Optional[CaseGeneratorAgent] = None


def get_case_generator() -> CaseGeneratorAgent:
    """获取案件生成器单例"""
    global _case_generator
    if _case_generator is None:
        _case_generator = CaseGeneratorAgent()
    return _case_generator
