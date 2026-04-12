"""
游戏相关 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from typing import Optional, List, Dict, Any

from app.models.game import GameState, CreateGameRequest, GameDifficulty
from app.models.case import Observation, Inference, Hypothesis, DeductionChain
from app.services.game_service import get_game_service
from app.agents.case_generator_agent import get_case_generator
from app.agents.watson_agent import get_watson_agent
from app.agents.suspect_agent import get_suspect_agent

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


@router.post("/new", response_model=GameState)
async def create_new_game(request: CreateGameRequest):
    """创建新案件"""
    logger.info(f"[API] 创建新游戏请求, 难度: {request.difficulty}")

    game_service = get_game_service()
    case_generator = get_case_generator()

    # 创建游戏状态
    game = game_service.create_game(difficulty=request.difficulty)

    # 生成案件
    case = await case_generator.generate_case(difficulty=request.difficulty.value)
    game_service.set_case(game.game_id, case)

    # 获取更新后的游戏状态
    updated_game = game_service.get_game(game.game_id)
    if not updated_game:
        raise HTTPException(status_code=500, detail="创建游戏失败")

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


@router.post("/{game_id}/difficulty")
async def set_difficulty(game_id: str, difficulty: GameDifficulty):
    """设置难度"""
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

    logger.info(f"[API] 难度设置成功: {game_id} -> {difficulty}")
    return {"gameId": game_id, "difficulty": difficulty}


@router.post("/{game_id}/watson/observation")
async def get_watson_observation_comment(game_id: str, request: WatsonObservationRequest):
    """获取华生对新观察的评论"""
    logger.info(f"[API] 获取华生观察评论: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    watson = get_watson_agent()
    comment = await watson.share_observation(request.observation)

    logger.info(f"[API] 华生观察评论生成成功: {game_id}")
    return {"comment": comment}


@router.post("/{game_id}/watson/hint")
async def get_watson_hint(game_id: str, request: WatsonHintRequest):
    """获取华生提示（当用户长时间无进展时）"""
    logger.info(f"[API] 获取华生提示: {game_id}, 类型: {request.hint_type}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    watson = get_watson_agent()
    hint: Optional[str] = None

    if request.hint_type == "idle":
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
    """检测证词中的矛盾点"""
    logger.info(f"[API] 检测矛盾: {game_id}")

    game_service = get_game_service()
    game = game_service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"游戏不存在: {game_id}")

    if not game.case:
        raise HTTPException(status_code=400, detail=f"案件未设置: {game_id}")

    # 简单的矛盾检测逻辑（Mock实现）
    contradictions = []

    # 检查不同嫌疑人关于同一时间点的陈述
    statements_by_topic = {}

    for suspect_id, statements in request.suspect_statements.items():
        suspect = next((s for s in game.case.suspects if s.id == suspect_id), None)
        if not suspect:
            continue

        for stmt in statements:
            # 提取关键词（简单实现）
            keywords = ["昨晚", "10点", "11点", "厨房", "客厅", "书房", "睡觉", "读书", " alone"]
            for keyword in keywords:
                if keyword in stmt:
                    if keyword not in statements_by_topic:
                        statements_by_topic[keyword] = []
                    statements_by_topic[keyword].append({
                        "suspect_id": suspect_id,
                        "suspect_name": suspect.name,
                        "statement": stmt
                    })

    # 查找同一话题下的矛盾陈述
    for topic, topic_statements in statements_by_topic.items():
        if len(topic_statements) >= 2:
            # 简单检查：如果两个嫌疑人在同一话题下的陈述看起来不同
            for i in range(len(topic_statements)):
                for j in range(i + 1, len(topic_statements)):
                    stmt1 = topic_statements[i]
                    stmt2 = topic_statements[j]

                    # 简单的矛盾检测启发式
                    if ("在厨房" in stmt1["statement"] and "在客厅" in stmt2["statement"]) or \
                       ("在睡觉" in stmt1["statement"] and "在读书" in stmt2["statement"]) or \
                       ("独自一人" in stmt1["statement"] and "和某人在一起" in stmt2["statement"]):

                        contradictions.append({
                            "type": "timeline_conflict",
                            "topic": topic,
                            "suspect_1": stmt1,
                            "suspect_2": stmt2,
                            "description": f"{stmt1['suspect_name']}和{stmt2['suspect_name']}关于{topic}的陈述存在矛盾",
                            "confidence": 0.7
                        })

    # 如果对话历史中提到时间，也可以检查
    if len(contradictions) == 0 and len(request.conversation_history) > 3:
        # 随机生成一个模拟的矛盾点（演示用）
        if game.case.suspects and len(game.case.suspects) >= 2:
            s1 = game.case.suspects[0]
            s2 = game.case.suspects[1]
            contradictions.append({
                "type": "location_conflict",
                "topic": "昨晚的行踪",
                "suspect_1": {"suspect_id": s1.id, "suspect_name": s1.name, "statement": "我昨晚一直在自己房间"},
                "suspect_2": {"suspect_id": s2.id, "suspect_name": s2.name, "statement": "我昨晚看到有人从书房出来"},
                "description": f"{s1.name}的房间窗户正对{s2.name}的房间，如果{s1.name}在睡觉，{s2.name}应该能听到动静",
                "confidence": 0.6
            })

    logger.info(f"[API] 矛盾检测完成: {game_id}, 发现 {len(contradictions)} 个矛盾")
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
