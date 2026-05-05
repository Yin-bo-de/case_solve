"""
游戏服务
"""
from typing import Dict, Optional, List, Any
from loguru import logger
from datetime import datetime
import uuid

from app.models.game import (
    GameState, GameDifficulty, GamePhase,
    WatsonChatMessage, WatsonChatContext
)
from app.models.case import (
    Case, Clue, Observation, Inference, Hypothesis, DeductionChain
)
from app.config import get_settings


class GameService:
    """游戏服务类"""

    def __init__(self):
        self._games: Dict[str, GameState] = {}
        self._deduction_chains: Dict[str, DeductionChain] = {}
        self._watson_chat_history: Dict[str, List[WatsonChatMessage]] = {}
        logger.info("[GameService] 初始化游戏服务")

    def create_game(
        self,
        difficulty: GameDifficulty = GameDifficulty.CLASSIC,
        openai_api_key: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        redemption_code: Optional[str] = None,
    ) -> GameState:
        """创建新游戏，可绑定兑换码的 OpenAI 配置快照"""
        import uuid

        game_id = str(uuid.uuid4())

        # 根据难度设置参数
        max_mistakes = {
            GameDifficulty.EASY: 3,
            GameDifficulty.CLASSIC: 2,
            GameDifficulty.HARDCORE: 1,
        }[difficulty]

        time_limit = {
            GameDifficulty.EASY: 60,
            GameDifficulty.CLASSIC: 90,
            GameDifficulty.HARDCORE: None,
        }[difficulty]

        game_state = GameState(
            game_id=game_id,
            difficulty=difficulty,
            phase=GamePhase.START,
            max_mistakes=max_mistakes,
            time_limit_minutes=time_limit,
            start_time=datetime.utcnow(),
            openai_api_key=openai_api_key,
            openai_base_url=openai_base_url,
            redemption_code=redemption_code,
        )

        self._games[game_id] = game_state

        # 初始化推理链条
        self._init_deduction_chain(game_id)

        logger.info(f"[GameService] 创建游戏: {game_id}, 难度: {difficulty}")
        return game_state

    def get_game(self, game_id: str) -> Optional[GameState]:
        """获取游戏状态"""
        return self._games.get(game_id)

    def set_case(self, game_id: str, case: Case) -> bool:
        """设置案件"""
        game = self.get_game(game_id)
        if not game:
            logger.warning(f"[GameService] 游戏不存在: {game_id}")
            return False

        game.case = case
        game.phase = GamePhase.INVESTIGATION
        game.updated_at = datetime.utcnow()

        # 将案件线索转换为观察记录
        deduction_chain = self.get_or_create_deduction_chain(game_id)
        for clue in case.clues:
            if clue.discovered:
                observation = Observation(
                    id=str(uuid.uuid4()),
                    description=clue.description,
                    location=clue.location or "未知位置",
                    related_clue_ids=[clue.id]
                )
                deduction_chain.observations.append(observation)

        logger.info(f"[GameService] 设置案件: {game_id} -> {case.id}")
        return True

    def _init_deduction_chain(self, game_id: str) -> DeductionChain:
        """初始化推理链条"""
        import uuid
        chain_id = str(uuid.uuid4())
        chain = DeductionChain(id=chain_id)
        self._deduction_chains[game_id] = chain
        return chain

    def get_or_create_deduction_chain(self, game_id: str) -> DeductionChain:
        """获取或创建推理链条"""
        if game_id not in self._deduction_chains:
            return self._init_deduction_chain(game_id)
        return self._deduction_chains[game_id]

    def create_inference(
        self,
        game_id: str,
        content: str,
        observation_ids: List[str],
        parent_inference_ids: List[str]
    ) -> Inference:
        """创建推理"""
        import uuid
        chain = self.get_or_create_deduction_chain(game_id)

        # 推理数量软上限防护
        MAX_INFERENCES_PER_GAME = 50
        if len(chain.inferences) >= MAX_INFERENCES_PER_GAME:
            raise ValueError(f"推理记录已达上限 ({MAX_INFERENCES_PER_GAME}条)，请先删除不必要的记录")

        # 计算置信度（基于观察数量）
        confidence = min(0.3 + len(observation_ids) * 0.15, 0.95)

        # 识别支持和反对证据
        supporting_evidence = []
        contradicting_evidence = []

        # 从观察中提取支持证据
        for obs in chain.observations:
            if obs.id in observation_ids:
                supporting_evidence.append(obs.description)

        inference = Inference(
            id=str(uuid.uuid4()),
            content=content,
            observation_ids=observation_ids,
            parent_inference_ids=parent_inference_ids,
            confidence=confidence,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence
        )

        chain.inferences.append(inference)
        chain.updated_at = datetime.utcnow()
        logger.info(f"[GameService] 创建推理: {game_id} -> {inference.id}")
        return inference

    def delete_inference(self, game_id: str, inference_id: str) -> bool:
        """删除推理"""
        chain = self.get_or_create_deduction_chain(game_id)
        initial_len = len(chain.inferences)
        chain.inferences = [i for i in chain.inferences if i.id != inference_id]
        chain.updated_at = datetime.utcnow()
        success = len(chain.inferences) < initial_len
        logger.info(f"[GameService] 删除推理: {game_id} -> {inference_id}, 成功: {success}")
        return success

    def create_hypothesis(
        self,
        game_id: str,
        title: str,
        description: str,
        inference_ids: List[str],
        suspect_id: Optional[str]
    ) -> Hypothesis:
        """创建假设"""
        import uuid
        chain = self.get_or_create_deduction_chain(game_id)

        # 假设数量软上限防护
        MAX_HYPOTHESES_PER_GAME = 20
        if len(chain.hypotheses) >= MAX_HYPOTHESES_PER_GAME:
            raise ValueError(f"假设记录已达上限 ({MAX_HYPOTHESES_PER_GAME}条)，请先删除不必要的记录")

        # 收集支持证据
        supporting_evidence = []
        opposing_evidence = []
        for inference in chain.inferences:
            if inference.id in inference_ids:
                supporting_evidence.extend(inference.supporting_evidence)

        # 计算支持度评分
        support_score = sum(
            inf.confidence for inf in chain.inferences
            if inf.id in inference_ids
        )

        hypothesis = Hypothesis(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            inference_ids=inference_ids,
            suspect_id=suspect_id,
            is_verified=False,
            support_score=support_score
        )

        chain.hypotheses.append(hypothesis)
        chain.updated_at = datetime.utcnow()
        logger.info(f"[GameService] 创建假设: {game_id} -> {hypothesis.id}")
        return hypothesis

    def verify_hypothesis(
        self,
        game_id: str,
        hypothesis_id: str,
        is_verified: bool,
        verification_notes: Optional[str]
    ) -> Optional[Hypothesis]:
        """验证假设"""
        chain = self.get_or_create_deduction_chain(game_id)

        for hypothesis in chain.hypotheses:
            if hypothesis.id == hypothesis_id:
                hypothesis.is_verified = is_verified
                hypothesis.verification_notes = verification_notes
                chain.updated_at = datetime.utcnow()
                logger.info(f"[GameService] 验证假设: {game_id} -> {hypothesis_id}, 状态: {is_verified}")
                return hypothesis

        return None

    def delete_hypothesis(self, game_id: str, hypothesis_id: str) -> bool:
        """删除假设"""
        chain = self.get_or_create_deduction_chain(game_id)
        initial_len = len(chain.hypotheses)
        chain.hypotheses = [h for h in chain.hypotheses if h.id != hypothesis_id]
        chain.updated_at = datetime.utcnow()
        success = len(chain.hypotheses) < initial_len
        logger.info(f"[GameService] 删除假设: {game_id} -> {hypothesis_id}, 成功: {success}")
        return success

    def detect_logic_gaps(
        self,
        game_id: str,
        inference_ids: List[str],
        hypothesis_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """检测逻辑缺口"""
        chain = self.get_or_create_deduction_chain(game_id)
        gaps = []

        # 检查推理是否有足够的观察支持
        for inference in chain.inferences:
            if inference.id in inference_ids and len(inference.observation_ids) < 2:
                gaps.append({
                    "type": "insufficient_evidence",
                    "target_type": "inference",
                    "target_id": inference.id,
                    "description": "这个推理只有很少的观察支持，可能需要更多证据"
                })

        # 检查假设是否有足够的推理支持
        for hypothesis in chain.hypotheses:
            if hypothesis.id in hypothesis_ids:
                if len(hypothesis.inference_ids) < 2:
                    gaps.append({
                        "type": "insufficient_inferences",
                        "target_type": "hypothesis",
                        "target_id": hypothesis.id,
                        "description": "这个假设只有很少的推理支持，建议建立更多推理节点"
                    })

                # 检查是否关联了嫌疑人
                if not hypothesis.suspect_id:
                    gaps.append({
                        "type": "no_suspect_linked",
                        "target_type": "hypothesis",
                        "target_id": hypothesis.id,
                        "description": "这个假设没有关联具体的嫌疑人，考虑是否需要关联"
                    })

        # 检查是否有未使用的观察
        used_observation_ids = set()
        for inference in chain.inferences:
            used_observation_ids.update(inference.observation_ids)

        unused_observations = [
            obs for obs in chain.observations
            if obs.id not in used_observation_ids
        ]

        if len(unused_observations) > 0:
            gaps.append({
                "type": "unused_observations",
                "description": f"还有 {len(unused_observations)} 条观察记录没有被用于任何推理",
                "unused_count": len(unused_observations)
            })

        return gaps

    def check_conclusion_readiness(self, game_id: str) -> Dict[str, Any]:
        """检查是否可以进入结案阶段"""
        chain = self.get_or_create_deduction_chain(game_id)
        game = self.get_game(game_id)

        if not game or not game.case:
            return {
                "is_ready": False,
                "reason": "案件未设置",
                "observations_count": 0,
                "inferences_count": 0,
                "hypotheses_count": 0,
                "minimum_observations": 5
            }

        # 计算已收集的观察数量
        observations_count = len(chain.observations)
        inferences_count = len(chain.inferences)
        hypotheses_count = len(chain.hypotheses)

        # 最低要求：至少5条观察记录
        minimum_observations = 5
        is_ready = observations_count >= minimum_observations

        reason = ""
        if not is_ready:
            reason = f"还需要收集 {minimum_observations - observations_count} 条观察记录才能进入结案阶段"

        return {
            "is_ready": is_ready,
            "reason": reason,
            "observations_count": observations_count,
            "inferences_count": inferences_count,
            "hypotheses_count": hypotheses_count,
            "minimum_observations": minimum_observations
        }

    def make_accusation(
        self,
        game_id: str,
        suspect_id: str,
        reasoning_steps: List[str]
    ) -> Dict[str, Any]:
        """指认凶手"""
        game = self.get_game(game_id)
        chain = self.get_or_create_deduction_chain(game_id)

        if not game or not game.case:
            raise ValueError("案件未设置")

        # 找到被指控的嫌疑人
        accused_suspect = next(
            (s for s in game.case.suspects if s.id == suspect_id),
            None
        )

        if not accused_suspect:
            raise ValueError("嫌疑人不存在")

        # 检查是否正确
        true_murderer_id = game.case.true_murderer_id
        is_correct = suspect_id == true_murderer_id

        # 记录错误次数
        if not is_correct:
            game.mistakes_made += 1

        # 找到真凶
        true_murderer = next(
            (s for s in game.case.suspects if s.id == true_murderer_id),
            None
        )

        # 更新推理链条
        chain.final_accusation = suspect_id
        chain.conclusion = f"指认了 {accused_suspect.name}，结果: {'正确' if is_correct else '错误'}"
        chain.updated_at = datetime.utcnow()

        # 华生的反馈
        watson_feedback = ""
        if is_correct:
            watson_feedback = f"太棒了，老朋友！你完全正确！{accused_suspect.name} 就是凶手！"
        else:
            watson_feedback = f"我觉得这里可能有问题...{accused_suspect.name} 似乎不是真正的凶手。我们再仔细想想？"

        return {
            "is_correct": is_correct,
            "accused_suspect": {
                "id": accused_suspect.id,
                "name": accused_suspect.name,
                "background": accused_suspect.background
            },
            "true_murderer": {
                "id": true_murderer.id if true_murderer else None,
                "name": true_murderer.name if true_murderer else None
            } if is_correct else None,
            "watson_feedback": watson_feedback,
            "mistakes_made": game.mistakes_made,
            "max_mistakes": game.max_mistakes,
            "can_continue": game.mistakes_made < game.max_mistakes
        }

    def get_case_reveal(self, game_id: str) -> Dict[str, Any]:
        """获取完整案件真相"""
        game = self.get_game(game_id)

        if not game or not game.case:
            raise ValueError("案件未设置")

        # 找到真凶
        true_murderer = next(
            (s for s in game.case.suspects if s.id == game.case.true_murderer_id),
            None
        )

        return {
            "victim": {
                "name": game.case.victim_name,
                "background": game.case.victim_background,
                "cause_of_death": game.case.cause_of_death,
                "time_of_death": game.case.time_of_death,
                "location": game.case.location
            },
            "true_murderer": {
                "id": true_murderer.id if true_murderer else None,
                "name": true_murderer.name if true_murderer else None,
                "age": true_murderer.age if true_murderer else None,
                "background": true_murderer.background if true_murderer else None,
                "motive": true_murderer.motive if true_murderer else None,
                "secrets": true_murderer.secrets if true_murderer else []
            } if true_murderer else None,
            "murder_method": game.case.murder_method,
            "case_summary": game.case.summary,
            "all_suspects": [
                {
                    "id": s.id,
                    "name": s.name,
                    "age": s.age,
                    "background": s.background,
                    "motive": s.motive,
                    "is_guilty": s.is_guilty
                }
                for s in game.case.suspects
            ],
            "key_clues": [
                {
                    "id": c.id,
                    "description": c.description,
                    "clue_type": c.clue_type,
                    "is_red_herring": c.is_red_herring
                }
                for c in game.case.clues
                if not c.is_red_herring
            ]
        }

    def add_user_clue(
        self,
        game_id: str,
        user_label: str,
        description: str,
        source_type: str,
        source_ref: Optional[str] = None,
        base_clue_id: Optional[str] = None,
        quoted_text: Optional[str] = None,
    ) -> Clue:
        """添加或标记用户线索。若 base_clue_id 命中已有 clue 则标记发现；否则新建用户自定义线索。"""
        game = self.get_game(game_id)
        if not game or not game.case:
            raise ValueError("游戏或案件不存在")

        # 用户线索数量软上限防护
        MAX_USER_CLUES_PER_GAME = 30
        user_clues = [c for c in game.case.clues if getattr(c, "user_generated", False)]
        if len(user_clues) >= MAX_USER_CLUES_PER_GAME and not base_clue_id:
            raise ValueError(f"用户自定义线索已达上限 ({MAX_USER_CLUES_PER_GAME}条)，请先整理已有线索")

        if base_clue_id:
            existing = next((c for c in game.case.clues if c.id == base_clue_id), None)
            if existing:
                existing.discovered = True
                existing.user_label = user_label
                if quoted_text:
                    existing.quoted_text = quoted_text
                logger.info(f"[GameService] 标记线索已发现: {game_id} base_clue_id={base_clue_id}")
                return existing

        clue = Clue(
            id="user_" + uuid.uuid4().hex[:8],
            description=description,
            clue_type=source_type,
            user_label=user_label,
            source_type=source_type,
            source_ref=source_ref,
            quoted_text=quoted_text,
            user_generated=True,
            discovered=True,
        )
        game.case.clues.append(clue)
        logger.info(f"[GameService] 新增用户线索: {game_id} clue_id={clue.id}")
        return clue

    def update_inference(self, game_id: str, inference: Inference) -> bool:
        """写回 Oracle 验证结果等字段到已有推理记录"""
        chain = self.get_or_create_deduction_chain(game_id)
        for i, existing in enumerate(chain.inferences):
            if existing.id == inference.id:
                chain.inferences[i] = inference
                chain.updated_at = datetime.utcnow()
                logger.info(f"[GameService] 更新推理: {game_id} inference_id={inference.id}")
                return True
        logger.warning(f"[GameService] 推理不存在，更新失败: {game_id} inference_id={inference.id}")
        return False

    def record_accusation(
        self,
        game_id: str,
        suspect_id: str,
        is_correct: bool,
        explanation: str,
        reasoning_record_ids: List[str],
    ) -> None:
        """记录指控结果，更新错误次数和推理链条结论"""
        game = self.get_game(game_id)
        chain = self.get_or_create_deduction_chain(game_id)

        if game and not is_correct:
            game.mistakes_made += 1
            game.updated_at = datetime.utcnow()

        chain.final_accusation = suspect_id
        chain.conclusion = explanation
        chain.updated_at = datetime.utcnow()
        logger.info(
            f"[GameService] 记录指控: {game_id} suspect_id={suspect_id} is_correct={is_correct}"
        )

    def update_clue_verification(
        self,
        game_id: str,
        clue_id: str,
        status: str,
        verified_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """更新线索验证状态，并同步冗余索引 GameState.verified_clue_ids"""
        game = self.get_game(game_id)
        if not game or not game.case:
            logger.warning(f"[GameService] 游戏或案件不存在: {game_id}")
            return False

        target_clue = next((c for c in game.case.clues if c.id == clue_id), None)
        if not target_clue:
            logger.warning(f"[GameService] 线索不存在: {game_id} clue_id={clue_id}")
            return False

        target_clue.verification_status = status
        if verified_by is not None:
            target_clue.verified_by = verified_by
        if notes is not None:
            target_clue.verification_notes = notes

        # 同步冗余索引
        if status == "verified" and clue_id not in game.verified_clue_ids:
            game.verified_clue_ids.append(clue_id)
        elif status != "verified" and clue_id in game.verified_clue_ids:
            game.verified_clue_ids = [cid for cid in game.verified_clue_ids if cid != clue_id]

        game.updated_at = datetime.utcnow()
        logger.info(
            f"[GameService] 更新线索验证状态: {game_id} clue_id={clue_id} status={status}"
        )
        return True

    def mark_clue_refuted(
        self,
        game_id: str,
        clue_id: str,
        refuted_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """将线索标记为已被驳斥"""
        return self.update_clue_verification(
            game_id=game_id,
            clue_id=clue_id,
            status="refuted",
            verified_by=refuted_by,
            notes=notes,
        )

    def add_watson_chat_message(
        self,
        game_id: str,
        role: str,
        content: str,
        message_type: str
    ) -> WatsonChatMessage:
        """添加华生对话消息"""
        if game_id not in self._watson_chat_history:
            self._watson_chat_history[game_id] = []

        settings = get_settings()
        max_history = settings.watson_chat_max_history_messages
        history = self._watson_chat_history[game_id]

        # 聊天记录上限保护：超出时丢弃最旧的消息
        if len(history) >= max_history:
            removed = len(history) - max_history + 1
            self._watson_chat_history[game_id] = history[removed:]
            logger.info(f"[GameService] Watson 聊天记录上限保护: 丢弃最旧 {removed} 条消息")

        message = WatsonChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            message_type=message_type,
            timestamp=datetime.utcnow()
        )

        self._watson_chat_history[game_id].append(message)
        logger.info(f"[GameService] 添加华生对话消息: {game_id} -> {role}")
        return message

    def get_watson_chat_history(self, game_id: str) -> List[WatsonChatMessage]:
        """获取华生对话历史"""
        return self._watson_chat_history.get(game_id, [])

    def build_watson_chat_context(self, game_id: str) -> Optional[WatsonChatContext]:
        """构建华生对话上下文"""
        game = self.get_game(game_id)
        if not game:
            return None

        chain = self.get_or_create_deduction_chain(game_id)

        # 统计线索数量
        clues_collected = 0
        current_clue_ids = []
        current_clues = []
        available_scenes = []
        suspects = []
        if game.case:
            clues_collected = len([c for c in game.case.clues if c.discovered])
            current_clue_ids = [c.id for c in game.case.clues if c.discovered]
            current_clues = [
                {
                    "id": c.id,
                    "label": c.user_label or "未命名线索",
                    "description": c.description,
                }
                for c in game.case.clues if c.discovered
            ]
            available_scenes = [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                }
                for s in game.case.scenes
            ]
            suspects = [
                {
                    "id": s.id,
                    "name": s.name,
                    "background": s.background,
                }
                for s in game.case.suspects
            ]

        # 统计嫌疑人
        current_suspect_ids = []
        if game.case:
            current_suspect_ids = [s.id for s in game.case.suspects]

        # 证人、专家摘要（供华生对话引用）
        witnesses = []
        experts = []
        if game.case:
            witnesses = [
                {
                    "id": w.id,
                    "name": w.name,
                    "occupation": w.occupation,
                    "relationship_to_case": w.relationship_to_case,
                }
                for w in game.case.witnesses
            ]
            experts = [
                {"id": e.id, "name": e.name, "title": e.title}
                for e in game.case.experts
            ]

        return WatsonChatContext(
            game_phase=game.phase,
            observations_count=len(chain.observations),
            clues_collected=clues_collected,
            suspects_interviewed=game.interviewed_suspect_ids,
            inferences_count=len(chain.inferences),
            hypotheses_count=len(chain.hypotheses),
            current_clue_ids=current_clue_ids,
            current_suspect_ids=current_suspect_ids,
            current_clues=current_clues,
            available_scenes=available_scenes,
            suspects=suspects,
            witnesses=witnesses,
            experts=experts,
        )


# 全局游戏服务实例
_game_service: Optional[GameService] = None


def get_game_service() -> GameService:
    """获取游戏服务单例"""
    global _game_service
    if _game_service is None:
        _game_service = GameService()
    return _game_service
