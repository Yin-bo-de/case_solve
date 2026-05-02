"""
游戏相关 API 路由
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from typing import Optional, List, Dict, Any, Literal

from app.models.game import (
    GameState, CreateGameRequest, GameDifficulty, GamePhase,
    WatsonChatMessage
)
from app.models.case import Observation, Inference, Hypothesis, DeductionChain
from app.services.game_service import get_game_service
from app.services.redemption_service import get_redemption_service
from app.agents.case_generator_agent import get_case_generator
from app.agents.watson_agent import get_watson_agent, WatsonAgent
from app.agents.suspect_agent import get_suspect_agent
from app.agents.witness_agent import get_witness_agent
from app.agents.expert_agent import get_expert_agent

router = APIRouter()


class CreateInferenceRequest(BaseModel):
    """创建推理请求"""
    content: str
    observation_ids: List[str] = []
    parent_inference_ids: List[str] = []


class CreateHypothesisRequest(BaseModel):
    """创建假设请求"""
    title: str
    description: str
    inference_ids: List[str] = []
    suspect_id: Optional[str] = None


class VerifyHypothesisRequest(BaseModel):
    """验证假设请求"""
    is_verified: bool
    verification_notes: Optional[str] = None


class WatsonDeductionFeedbackRequest(BaseModel):
    """华生推理反馈请求"""
    inference_ids: List[str] = []
    hypothesis_ids: List[str] = []


class WatsonObservationRequest(BaseModel):
    """华生观察评论请求"""
    observation: Observation


class WatsonHintRequest(BaseModel):
    """华生提示请求"""
    hint_type: str = "idle"
    observations_count: int = 0
    areas_examined: int = 0
    total_areas: int = 0
    # 场景勘查提示（hint_type == "scene" 时使用）
    scene_name: Optional[str] = None
    recent_actions: List[str] = []
    unchecked_object_names: Optional[List[str]] = None


class SuspectQuestionRequest(BaseModel):
    """嫌疑人提问请求"""
    suspect_id: str
    question: str
    conversation_history: List[Dict[str, str]] = []
    is_private: bool = True
    other_suspect_ids: List[str] = []


class ContradictionCheckRequest(BaseModel):
    """矛盾检测请求"""
    conversation_history: List[Dict[str, str]] = []
    suspect_statements: Dict[str, List[str]] = {}  # suspect_id -> list of statements


class GroupControlRequest(BaseModel):
    """全体质询控制请求"""
    action: str  # "quiet", "let_speak", "continue"
    target_suspect_id: Optional[str] = None


class SceneSearchRequest(BaseModel):
    """场景搜查请求"""
    query: str
    history: List[Dict[str, str]] = []


class SceneClueCandidate(BaseModel):
    """场景线索候选项"""
    object_id: str
    suggested_clue_id: Optional[str] = None
    hint: str


class SceneSearchResponse(BaseModel):
    """场景搜查响应"""
    narrative: str
    matched_object_ids: List[str] = []
    clue_candidates: List[SceneClueCandidate] = []
    dialog_options: List[str] = []


class AddClueRequest(BaseModel):
    """添加自定义线索请求"""
    user_label: str
    description: str
    source_type: str  # scene | interrogation
    source_ref: Optional[str] = None
    base_clue_id: Optional[str] = None  # 若是已有 case.clues 的"被发现"
    quoted_text: Optional[str] = None


class SubmitReasoningRequest(BaseModel):
    """提交组合推理请求"""
    clue_ids: List[str]
    conclusion: str


class ExtractClueFromInterrogationRequest(BaseModel):
    """从审讯片段提取线索请求"""
    suspect_id: str
    quoted_text: str
    context_messages: List[Dict[str, str]] = []
    user_label: str


class WatsonInterrogationTipsRequest(BaseModel):
    """华生审讯提示请求"""
    suspect_id: str
    conversation_history: List[Dict[str, str]] = []


class MakeAccusationRequest(BaseModel):
    """指认凶手请求"""
    suspect_id: str
    reasoning_record_ids: List[str]   # 必填，1-3 条
    reasoning_steps: List[str] = []   # 兼容旧字段


class WitnessQuestionRequest(BaseModel):
    """证人提问请求"""
    witness_id: str
    question: str
    conversation_history: List[Dict[str, str]] = []


class ExpertQuestionRequest(BaseModel):
    """专家提问请求"""
    expert_id: str
    question: str
    conversation_history: List[Dict[str, str]] = []


class ExtractClueFromActorRequest(BaseModel):
    """从证人/专家对话片段提取线索请求"""
    actor_type: Literal["witness", "expert"]
    actor_id: str
    quoted_text: str
    context_messages: List[Dict[str, str]] = []
    user_label: str


class WitnessWatsonTipsRequest(BaseModel):
    """华生证人审讯提示请求"""
    witness_id: str
    conversation_history: List[Dict[str, str]] = []


class WatsonChatRequest(BaseModel):
    """华生对话请求"""
    message: str


class GetWatsonHistoryResponse(BaseModel):
    """获取对话历史响应"""
    messages: List[WatsonChatMessage]


@router.post("/new", response_model=GameState)
async def create_new_game(request: CreateGameRequest):
    """创建新案件，若提供了 redemption_code 则绑定其 OpenAI 配置并扣减一次使用次数"""
    logger.info(f"[API] 创建新游戏请求, 难度: {request.difficulty}, 兑换码: {'已绑定' if request.redemption_code else '无'}")

    game_service = get_game_service()
    case_generator = get_case_generator()

    openai_api_key = None
    openai_base_url = None

    # 若提供了兑换码，获取其绑定的 OpenAI 配置（验证可用性）
    if request.redemption_code:
        redemption_service = get_redemption_service()
        success, record, msg = redemption_service.validate_only(request.redemption_code)
        if not success:
            raise HTTPException(status_code=400, detail=f"兑换码无效: {msg}")
        openai_api_key = record.openai_api_key
        openai_base_url = record.openai_base_url

    # 创建游戏状态
    game = game_service.create_game(
        difficulty=request.difficulty,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        redemption_code=request.redemption_code,
    )

    # 生成案件
    case = await case_generator.generate_case(difficulty=request.difficulty.value)
    game_service.set_case(game.game_id, case)

    # 获取更新后的游戏状态
    updated_game = game_service.get_game(game.game_id)
    if not updated_game:
        raise HTTPException(status_code=500, detail="创建游戏失败")

    # 若绑定了兑换码，扣减一次使用次数
    if updated_game.redemption_code:
        redemption_service = get_redemption_service()
        success, _, msg = redemption_service.consume(updated_game.redemption_code)
        if not success:
            logger.warning(f"[API] 兑换码扣减失败: {updated_game.redemption_code} - {msg}")
        else:
            remaining = redemption_service.get_remaining_uses(updated_game.redemption_code)
            logger.info(f"[API] 兑换码扣减成功: {updated_game.redemption_code}, 剩余: {remaining}")

    logger.info(f"[API] 游戏创建成功: {game.game_id}")
    return updated_game


@router.get("/{game_id}", response_model=GameState)
async def get_game_state(game_id: str):
    """获取游戏状态"""
    logger.info(f"[API] 获取游戏状态: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    return game


class SetDifficultyRequest(BaseModel):
    """设置难度请求"""
    difficulty: GameDifficulty


@router.post("/{game_id}/difficulty", response_model=GameState)
async def set_difficulty(game_id: str, request: SetDifficultyRequest):
    """
    设置难度并（若游戏处于 START 阶段且尚无案件）自动生成案件。
    兑换码验证流程中游戏是在 verify 阶段预创建的，
    此端点负责完成难度设置 + 案件生成，返回完整 GameState。
    """
    difficulty = request.difficulty
    logger.info(f"[API] 设置游戏难度: {game_id} -> {difficulty}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    # 更新难度
    game.difficulty = difficulty

    # 根据新难度调整参数
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

    game.max_mistakes = max_mistakes
    game.time_limit_minutes = time_limit

    # 若游戏处于 START 阶段且无案件，自动生成案件（兑换码验证预创建游戏的场景）
    if game.phase == GamePhase.START and game.case is None:
        logger.info(f"[API] 游戏无案件，自动生成: {game_id} 难度: {difficulty}")
        case_generator = get_case_generator()
        case = await case_generator.generate_case(difficulty=difficulty.value)
        game_service.set_case(game_id, case)
        game = game_service.get_game(game_id)
        if not game:
            raise HTTPException(status_code=500, detail="案件生成后游戏状态丢失")

    logger.info(f"[API] 难度设置成功: {game_id} -> {difficulty}, phase: {game.phase}")
    return game


@router.post("/{game_id}/watson/observation")
async def get_watson_observation_comment(game_id: str, request: WatsonObservationRequest):
    """获取华生对新观察的评论"""
    logger.info(f"[API] 获取华生观察评论: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    watson = WatsonAgent.from_difficulty(game.difficulty.value)
    comment = await watson.share_observation(request.observation)

    logger.info(f"[API] 华生观察评论生成成功: {game_id}, 难度: {game.difficulty.value}")
    return {"comment": comment}


@router.post("/{game_id}/watson/hint")
async def get_watson_hint(game_id: str, request: WatsonHintRequest):
    """获取华生提示（当用户长时间无进展时）"""
    logger.info(f"[API] 获取华生提示: {game_id}, 类型: {request.hint_type}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    watson = WatsonAgent.from_difficulty(game.difficulty.value)
    hint: Optional[str] = None

    if request.hint_type == "scene":
        if not request.scene_name:
            raise HTTPException(status_code=400, detail="hint_type=scene 时 scene_name 为必填")
        collected_clues = [c for c in (game.case.clues if game.case else []) if c.discovered or c.user_generated]
        hint = await watson.offer_scene_hint(
            scene_name=request.scene_name,
            recent_actions=request.recent_actions,
            collected_clues=collected_clues,
            unchecked_object_names=request.unchecked_object_names,
            total_clues=len(game.case.clues) if game.case else 5,
            difficulty=game.difficulty.value,
        )
    elif request.hint_type == "idle":
        # 长时间无进展，给出提示
        if request.areas_examined < request.total_areas:
            remaining = request.total_areas - request.areas_examined
            hint = f"老朋友，我们还有 {remaining} 个地方没仔细看过。也许应该再检查一下那些还没勘查的区域？"
        elif request.observations_count == 0:
            hint = "让我们开始吧！点击场景中的任何区域来仔细查看。"
        else:
            hint = await watson.encourage()
    elif request.hint_type == "area":
        # 进入某个区域时的提示
        hints = [
            "仔细看看这里，可能有什么重要的线索。",
            "我觉得这个地方值得好好检查一下。",
            "你觉得这里会有什么发现吗？",
        ]
        import random
        hint = random.choice(hints)

    logger.info(f"[API] 华生提示生成成功: {game_id}")
    return {"hint": hint}


@router.post("/{game_id}/interrogation/question")
async def ask_suspect_question(game_id: str, request: SuspectQuestionRequest):
    """向嫌疑人提问（单独审讯或全体质询）"""
    logger.info(f"[API] 向嫌疑人提问: {game_id}, 嫌疑人: {request.suspect_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    # 找到对应的嫌疑人
    suspect = next(
        (s for s in game.case.suspects if s.id == request.suspect_id),
        None
    )
    if not suspect:
        raise HTTPException(status_code=404, detail=f"嫌疑人不存在: {request.suspect_id}")

    # 调用嫌疑人Agent生成回复
    suspect_agent = get_suspect_agent()
    response = await suspect_agent.generate_response(
        suspect=suspect,
        case=game.case,
        user_question=request.question,
        conversation_history=request.conversation_history,
        is_private=request.is_private,
        other_suspects_present=request.other_suspect_ids
    )

    # 检测谎言
    lie_detection = await suspect_agent.detect_lie(suspect, response, game.case)

    logger.info(f"[API] 嫌疑人回复生成成功: {game_id}")
    return {
        "suspect_id": suspect.id,
        "suspect_name": suspect.name,
        "response": response,
        "lie_detection": lie_detection
    }


@router.post("/{game_id}/interrogation/interjection")
async def get_suspect_interjection(
    game_id: str,
    responding_suspect_id: str,
    other_suspect_id: str,
    context: str
):
    """获取嫌疑人的插话/反驳（全体质询时）"""
    logger.info(f"[API] 获取嫌疑人插话: {game_id}, {other_suspect_id} -> {responding_suspect_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    # 找到对应的嫌疑人
    responding_suspect = next(
        (s for s in game.case.suspects if s.id == responding_suspect_id),
        None
    )
    other_suspect = next(
        (s for s in game.case.suspects if s.id == other_suspect_id),
        None
    )

    if not responding_suspect or not other_suspect:
        raise HTTPException(status_code=404, detail="嫌疑人不存在")

    # 调用嫌疑人Agent生成插话
    suspect_agent = get_suspect_agent()
    interjection = await suspect_agent.generate_interjection(
        responding_suspect=responding_suspect,
        other_suspect=other_suspect,
        case=game.case,
        context=context
    )

    logger.info(f"[API] 嫌疑人插话生成成功: {game_id}")
    return {"interjection": interjection}


@router.post("/{game_id}/interrogation/contradiction-check")
async def check_contradictions(game_id: str, request: ContradictionCheckRequest):
    """检测证词中的矛盾点（LLM 驱动，由 WatsonAgent.detect_contradictions 实现）"""
    logger.info(f"[API] 检测矛盾: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    watson = WatsonAgent.from_difficulty(game.difficulty.value)
    contradictions = await watson.detect_contradictions(
        case=game.case,
        conversation_history=request.conversation_history,
        suspect_statements=request.suspect_statements,
    )

    logger.info(f"[API] 矛盾检测完成: {game_id} count={len(contradictions)}")
    return {"contradictions": contradictions, "count": len(contradictions)}


@router.post("/{game_id}/interrogation/group-control")
async def group_control(game_id: str, request: GroupControlRequest):
    """全体质询控场（用户绝对控制权）"""
    logger.info(f"[API] 全体质询控场: {game_id}, 动作: {request.action}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    # 处理不同的控场动作
    response_message = ""
    if request.action == "quiet":
        response_message = "好的，都安静下来！让我们听一个人说。"
    elif request.action == "let_speak":
        response_message = f"好的，让他继续说。"
    elif request.action == "continue":
        response_message = "继续，我们听听接下来怎么说。"
    else:
        response_message = "我们继续。"

    logger.info(f"[API] 控场操作完成: {game_id}")
    return {"success": True, "message": response_message}


@router.post("/{game_id}/scene/{scene_id}/search", response_model=SceneSearchResponse)
async def scene_search(game_id: str, scene_id: str, request: SceneSearchRequest):
    """场景 NPC 搜查：自然语言探索场景对象"""
    logger.info(f"[API] 场景搜查: {game_id} scene_id={scene_id} query_len={len(request.query)}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(status_code=404, detail="game/case 不存在")

    scene = next((s for s in game.case.scenes if s.id == scene_id), None)
    if not scene:
        raise HTTPException(status_code=404, detail=f"scene 不存在: {scene_id}")

    from app.agents.scene_agent import get_scene_agent
    result = await get_scene_agent().search(
        scene=scene, case=game.case, query=request.query, history=request.history
    )
    logger.info(f"[API] 场景搜查完成: {game_id} scene_id={scene_id}")
    return result


@router.post("/{game_id}/clues")
async def add_clue(game_id: str, request: AddClueRequest):
    """添加用户自定义命名线索"""
    logger.info(f"[API] 添加线索: {game_id} source_type={request.source_type}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(status_code=404, detail="game/case 不存在")

    clue = game_service.add_user_clue(
        game_id=game_id,
        user_label=request.user_label,
        description=request.description,
        source_type=request.source_type,
        source_ref=request.source_ref,
        base_clue_id=request.base_clue_id,
        quoted_text=request.quoted_text,
    )
    logger.info(f"[API] 线索添加成功: {game_id} clue_id={clue.id}")
    return clue


@router.post("/{game_id}/deduction/reasoning")
async def submit_reasoning(game_id: str, request: SubmitReasoningRequest):
    """组合推理（核心）：选取线索 + 结论 → Oracle 验证 → 持久化为 Inference"""
    logger.info(f"[API] 提交推理: {game_id} clue_count={len(request.clue_ids)}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(status_code=404, detail="game/case 不存在")

    if not request.clue_ids:
        raise HTTPException(status_code=400, detail="至少选择 1 条线索")

    selected = [c for c in game.case.clues if c.id in request.clue_ids]
    if len(selected) != len(request.clue_ids):
        raise HTTPException(status_code=400, detail="存在无效的线索 id")

    from app.agents.oracle_agent import get_oracle_agent
    oracle_result = await get_oracle_agent().verify_inference(
        case=game.case, clues=selected, conclusion=request.conclusion
    )

    inference = game_service.create_inference(
        game_id=game_id,
        content=request.conclusion,
        observation_ids=[],
        parent_inference_ids=[],
    )
    inference.clue_ids = request.clue_ids
    inference.verification_result = oracle_result["verdict"]
    inference.oracle_explanation = oracle_result["explanation"]
    inference.confidence = float(oracle_result.get("score", 0.5))
    game_service.update_inference(game_id, inference)

    logger.info(
        f"[API] 推理验证完成: {game_id} inference_id={inference.id} verdict={oracle_result['verdict']}"
    )
    return {
        "inference": inference,
        "verification_result": oracle_result["verdict"],
        "score": oracle_result.get("score", 0.5),
        "explanation": oracle_result["explanation"],
        "missing_links": oracle_result.get("missing_links", []),
        "misused_clues": oracle_result.get("misused_clues", []),
    }


@router.post("/{game_id}/interrogation/extract-clue")
async def extract_clue_from_interrogation(
    game_id: str, request: ExtractClueFromInterrogationRequest
):
    """从审讯对话片段生成线索"""
    logger.info(f"[API] 从审讯提取线索: {game_id} suspect_id={request.suspect_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(status_code=404, detail="game/case 不存在")

    clue = game_service.add_user_clue(
        game_id=game_id,
        user_label=request.user_label,
        description=request.quoted_text,
        source_type="interrogation",
        source_ref=request.suspect_id,
        quoted_text=request.quoted_text,
    )
    logger.info(f"[API] 审讯线索提取成功: {game_id} clue_id={clue.id}")
    return clue


@router.post("/{game_id}/interrogation/watson-tips")
async def watson_interrogation_tips(
    game_id: str, request: WatsonInterrogationTipsRequest
):
    """华生审讯实时提示：基于已知线索和对话给出审问建议"""
    logger.info(f"[API] 获取华生审讯提示: {game_id} suspect_id={request.suspect_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(status_code=404, detail="game/case 不存在")

    suspect = next((s for s in game.case.suspects if s.id == request.suspect_id), None)
    if not suspect:
        raise HTTPException(status_code=404, detail="嫌疑人不存在")

    watson = WatsonAgent.from_difficulty(game.difficulty.value)
    tips = await watson.offer_interrogation_tips(
        case=game.case,
        suspect=suspect,
        conversation_history=request.conversation_history,
        clues=[c for c in game.case.clues if c.discovered or c.user_generated],
    )
    logger.info(f"[API] 华生审讯提示生成成功: {game_id} tips_count={len(tips)}")
    return {"tips": tips}


@router.post("/{game_id}/interrogation/witness/question")
async def ask_witness_question(game_id: str, request: WitnessQuestionRequest):
    """向证人提问"""
    logger.info(f"[API] 向证人提问: {game_id}, 证人: {request.witness_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")
    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    witness = next(
        (w for w in game.case.witnesses if w.id == request.witness_id),
        None
    )
    if not witness:
        raise HTTPException(status_code=404, detail=f"证人不存在: {request.witness_id}")

    witness_agent = get_witness_agent()
    response = await witness_agent.generate_response(
        witness=witness,
        case=game.case,
        user_question=request.question,
        conversation_history=request.conversation_history,
    )
    credibility_check = await witness_agent.detect_credibility(
        witness=witness,
        response=response,
        case=game.case,
    )

    logger.info(f"[API] 证人回复生成成功: {game_id}")
    return {
        "witness_id": witness.id,
        "witness_name": witness.name,
        "response": response,
        "credibility_check": credibility_check,
    }


@router.post("/{game_id}/interrogation/expert/question")
async def ask_expert_question(game_id: str, request: ExpertQuestionRequest):
    """向专家提问"""
    logger.info(f"[API] 向专家提问: {game_id}, 专家: {request.expert_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")
    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    expert = next(
        (e for e in game.case.experts if e.id == request.expert_id),
        None
    )
    if not expert:
        raise HTTPException(status_code=404, detail=f"专家不存在: {request.expert_id}")

    expert_agent = get_expert_agent()
    response = await expert_agent.answer_question(
        expert=expert,
        case=game.case,
        user_question=request.question,
        conversation_history=request.conversation_history,
    )

    logger.info(f"[API] 专家回复生成成功: {game_id}")
    return {
        "expert_id": expert.id,
        "expert_name": expert.name,
        "response": response,
    }


@router.get("/{game_id}/interrogation/expert/{expert_id}/preliminary-report")
async def get_expert_preliminary_report(game_id: str, expert_id: str):
    """获取专家初步法医报告"""
    logger.info(f"[API] 获取专家初步报告: {game_id}, 专家: {expert_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")
    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    expert = next(
        (e for e in game.case.experts if e.id == expert_id),
        None
    )
    if not expert:
        raise HTTPException(status_code=404, detail=f"专家不存在: {expert_id}")

    expert_agent = get_expert_agent()
    report = await expert_agent.get_preliminary_report(expert=expert, case=game.case)

    key_findings_summary = [
        {"topic": f.topic, "finding": f.finding}
        for f in expert.key_findings
    ]

    logger.info(f"[API] 专家初步报告返回成功: {game_id}")
    return {
        "expert_id": expert.id,
        "expert_name": expert.name,
        "title": expert.title,
        "preliminary_report": report,
        "key_findings_summary": key_findings_summary,
    }


@router.post("/{game_id}/interrogation/extract-clue-from-actor")
async def extract_clue_from_actor(game_id: str, request: ExtractClueFromActorRequest):
    """从证人/专家对话片段生成线索"""
    logger.info(
        f"[API] 从{request.actor_type}提取线索: {game_id} actor_id={request.actor_id}"
    )

    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(status_code=404, detail="game/case 不存在")

    clue = game_service.add_user_clue(
        game_id=game_id,
        user_label=request.user_label,
        description=request.quoted_text,
        source_type=request.actor_type,
        source_ref=request.actor_id,
        quoted_text=request.quoted_text,
    )
    logger.info(f"[API] {request.actor_type}线索提取成功: {game_id} clue_id={clue.id}")
    return clue


@router.post("/{game_id}/interrogation/witness/watson-tips")
async def watson_witness_interrogation_tips(
    game_id: str, request: WitnessWatsonTipsRequest
):
    """华生证人审讯实时提示：提示侦探追问关键目击事实"""
    logger.info(f"[API] 获取华生证人提示: {game_id} witness_id={request.witness_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)
    if not game or not game.case:
        raise HTTPException(status_code=404, detail="game/case 不存在")

    witness = next(
        (w for w in game.case.witnesses if w.id == request.witness_id), None
    )
    if not witness:
        raise HTTPException(status_code=404, detail="证人不存在")

    watson = WatsonAgent.from_difficulty(game.difficulty.value)
    tips = await watson.offer_witness_interrogation_tips(
        case=game.case,
        witness=witness,
        conversation_history=request.conversation_history,
        clues=[c for c in game.case.clues if c.discovered or c.user_generated],
    )
    logger.info(f"[API] 华生证人提示生成成功: {game_id} tips_count={len(tips)}")
    return {"tips": tips}


@router.get("/{game_id}/deduction", response_model=DeductionChain)
async def get_deduction_chain(game_id: str):
    """获取推理链条"""
    logger.info(f"[API] 获取推理链条: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    deduction_chain = game_service.get_or_create_deduction_chain(game_id)
    return deduction_chain


@router.post("/{game_id}/deduction/inference", response_model=Inference)
async def create_inference(game_id: str, request: CreateInferenceRequest):
    """创建推理"""
    logger.info(f"[API] 创建推理: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    inference = game_service.create_inference(
        game_id,
        request.content,
        request.observation_ids,
        request.parent_inference_ids
    )
    return inference


@router.delete("/{game_id}/deduction/inference/{inference_id}")
async def delete_inference(game_id: str, inference_id: str):
    """删除推理"""
    logger.info(f"[API] 删除推理: {game_id}, {inference_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    success = game_service.delete_inference(game_id, inference_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"推理不存在: {inference_id}")

    return {"success": True}


@router.post("/{game_id}/deduction/hypothesis", response_model=Hypothesis)
async def create_hypothesis(game_id: str, request: CreateHypothesisRequest):
    """创建假设"""
    logger.info(f"[API] 创建假设: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    hypothesis = game_service.create_hypothesis(
        game_id,
        request.title,
        request.description,
        request.inference_ids,
        request.suspect_id
    )
    return hypothesis


@router.post("/{game_id}/deduction/hypothesis/{hypothesis_id}/verify", response_model=Hypothesis)
async def verify_hypothesis(game_id: str, hypothesis_id: str, request: VerifyHypothesisRequest):
    """验证假设"""
    logger.info(f"[API] 验证假设: {game_id}, {hypothesis_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    hypothesis = game_service.verify_hypothesis(
        game_id,
        hypothesis_id,
        request.is_verified,
        request.verification_notes
    )
    if not hypothesis:
        raise HTTPException(status_code=404, detail=f"假设不存在: {hypothesis_id}")

    return hypothesis


@router.delete("/{game_id}/deduction/hypothesis/{hypothesis_id}")
async def delete_hypothesis(game_id: str, hypothesis_id: str):
    """删除假设"""
    logger.info(f"[API] 删除假设: {game_id}, {hypothesis_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    success = game_service.delete_hypothesis(game_id, hypothesis_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"假设不存在: {hypothesis_id}")

    return {"success": True}


@router.post("/{game_id}/deduction/watson-feedback")
async def get_watson_deduction_feedback(game_id: str, request: WatsonDeductionFeedbackRequest):
    """获取华生对推理的反馈"""
    logger.info(f"[API] 获取华生推理反馈: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    deduction_chain = game_service.get_or_create_deduction_chain(game_id)

    # 分析推理链条
    logic_gaps = game_service.detect_logic_gaps(game_id, request.inference_ids, request.hypothesis_ids)

    watson = get_watson_agent()
    feedback = await watson.analyze_deduction(deduction_chain, logic_gaps)

    return {
        "feedback": feedback["analysis"],
        "suggestions": feedback["suggestions"],
        "logic_gaps": logic_gaps
    }


@router.get("/{game_id}/conclusion/readiness")
async def check_conclusion_readiness(game_id: str):
    """检查是否可以进入结案阶段"""
    logger.info(f"[API] 检查结案准备状态: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    readiness = game_service.check_conclusion_readiness(game_id)
    return readiness


@router.post("/{game_id}/conclusion/accuse")
async def make_accusation(game_id: str, request: MakeAccusationRequest):
    """指认凶手：必须附带 1-3 条推理记录，经 Oracle 裁决后记录结果"""
    logger.info(f"[API] 指认凶手: {game_id} suspect_id={request.suspect_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    if not request.reasoning_record_ids or len(request.reasoning_record_ids) > 3:
        raise HTTPException(status_code=400, detail="需提供 1-3 条推理记录作为指控依据")

    chain = game_service.get_or_create_deduction_chain(game_id)
    records = [i for i in chain.inferences if i.id in request.reasoning_record_ids]
    if len(records) != len(request.reasoning_record_ids):
        raise HTTPException(status_code=400, detail="存在无效的推理记录 id")
    if any(r.verification_result == "wrong" for r in records):
        raise HTTPException(status_code=400, detail="不可使用已被裁决官标记为错误的推理记录")

    from app.agents.oracle_agent import get_oracle_agent
    oracle_result = await get_oracle_agent().verify_accusation(
        case=game.case,
        suspect_id=request.suspect_id,
        reasoning_records=records,
    )

    game_service.record_accusation(
        game_id=game_id,
        suspect_id=request.suspect_id,
        is_correct=oracle_result["is_correct"],
        explanation=oracle_result["verdict_explanation"],
        reasoning_record_ids=request.reasoning_record_ids,
    )
    game.phase = GamePhase.CONCLUSION
    game.updated_at = datetime.utcnow()

    logger.info(f"[API] 指认结果: {game_id} is_correct={oracle_result['is_correct']}")
    return oracle_result


@router.get("/{game_id}/conclusion/reveal")
async def get_case_reveal(game_id: str):
    """获取完整案件真相"""
    logger.info(f"[API] 获取案件真相: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    reveal = game_service.get_case_reveal(game_id)
    return reveal


@router.post("/{game_id}/watson/chat")
async def chat_with_watson(game_id: str, request: WatsonChatRequest):
    """与华生对话"""
    logger.info(f"[API] 与华生对话: {game_id}, 消息: {request.message[:50]}...")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    # 构建对话上下文
    context = game_service.build_watson_chat_context(game_id)
    if not context:
        raise HTTPException(status_code=500, detail="构建对话上下文失败")

    # 保存用户消息
    game_service.add_watson_chat_message(
        game_id, "user", request.message, "general"
    )

    # 调用华生Agent
    watson = get_watson_agent()
    response, message_type = await watson.chat(request.message, context)

    # 保存华生回复
    game_service.add_watson_chat_message(
        game_id, "watson", response, message_type
    )

    logger.info(f"[API] 华生回复生成成功: {game_id}, 类型: {message_type}")
    return {
        "message": response,
        "message_type": message_type
    }


@router.get("/{game_id}/watson/history", response_model=GetWatsonHistoryResponse)
async def get_watson_chat_history(game_id: str):
    """获取华生对话历史"""
    logger.info(f"[API] 获取华生对话历史: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    messages = game_service.get_watson_chat_history(game_id)
    return {"messages": messages}
