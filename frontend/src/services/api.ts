// API 服务
import axios from 'axios'
import type {
  GameStateDto, GameDifficulty, Observation, Inference, Hypothesis, DeductionChain,
  ConclusionReadiness, AccusationResult, CaseReveal,
  WatsonChatMessage, WatsonMessageType,
  Clue, SceneSearchResponse, ReasoningRecord, WatsonTip,
} from '@/types/game'
import type { RedemptionVerifyResponse, RedemptionGenerateResponse } from '@/types/redemption'

console.info('[api.ts] 初始化 API 服务')

// 验证 gameId 的辅助函数
const validateGameId = (gameId: string, functionName: string): void => {
  if (!gameId || gameId === 'undefined') {
    console.error(`[gameApi] ${functionName} 被调用时 gameId 无效`, { gameId })
    throw new Error(`gameId 不能为空 (${functionName})`)
  }
}

// 将 snake_case 转换为 camelCase
const snakeToCamel = (str: string): string => {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

// 将 camelCase 转换为 snake_case
const camelToSnake = (str: string): string => {
  return str.replace(/([A-Z])/g, '_$1').toLowerCase()
}

// 递归转换对象的键从 snake_case 到 camelCase
const convertKeysToCamel = (obj: any): any => {
  if (Array.isArray(obj)) {
    return obj.map(convertKeysToCamel)
  } else if (obj !== null && typeof obj === 'object') {
    return Object.keys(obj).reduce((result: any, key) => {
      const camelKey = snakeToCamel(key)
      result[camelKey] = convertKeysToCamel(obj[key])
      return result
    }, {})
  }
  return obj
}

// 递归转换对象的键从 camelCase 到 snake_case
const convertKeysToSnake = (obj: any): any => {
  if (Array.isArray(obj)) {
    return obj.map(convertKeysToSnake)
  } else if (obj !== null && typeof obj === 'object') {
    return Object.keys(obj).reduce((result: any, key) => {
      const snakeKey = camelToSnake(key)
      result[snakeKey] = convertKeysToSnake(obj[key])
      return result
    }, {})
  }
  return obj
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 记录所有 API 请求并转换字段名
apiClient.interceptors.request.use(
  (config) => {
    // 转换请求数据的键从 camelCase 到 snake_case
    if (config.data) {
      config.data = convertKeysToSnake(config.data)
    }
    console.debug(`[API] 请求: ${config.method?.toUpperCase()} ${config.url}`, config.data || '')
    return config
  },
  (error) => {
    console.error('[API] 请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器 - 记录所有 API 响应并转换字段名
apiClient.interceptors.response.use(
  (response) => {
    console.debug(`[API] 响应: ${response.status}`, response.data)
    // 转换响应数据的键从 snake_case 到 camelCase
    if (response.data) {
      response.data = convertKeysToCamel(response.data)
    }
    return response
  },
  (error) => {
    console.error('[API] 响应错误:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

// 对话历史消息类型
export interface ConversationMessage {
  role: 'user' | 'suspect' | 'watson'
  content: string
  timestamp?: string
}

// 谎言检测结果类型（支持两种命名格式）
export interface LieDetectionResult {
  lie_detected: boolean
  lieDetected?: boolean
  confidence: number
  microexpression?: string
  notes?: string
}

// 矛盾检测结果类型
export interface ContradictionResult {
  type: string
  topic: string
  suspect_1: {
    suspect_id: string
    suspect_name: string
    statement: string
  }
  suspect_2: {
    suspect_id: string
    suspect_name: string
    statement: string
  }
  description: string
  confidence: number
}

// 全体质询控制动作类型
export type GroupControlAction = 'quiet' | 'let_speak' | 'continue'

export const gameApi = {
  /** 创建新游戏 */
  async createNewGame(difficulty: GameDifficulty = 'classic', redemptionCode?: string): Promise<GameStateDto> {
    console.info('[gameApi] 创建新游戏', { difficulty, redemptionCode: redemptionCode ? `${redemptionCode.slice(0, 4)}***` : undefined })
    const payload: Record<string, unknown> = { difficulty }
    if (redemptionCode) {
      payload.redemption_code = redemptionCode
    }
    const response = await apiClient.post<GameStateDto>('/api/game/new', payload)
    return response.data
  },

  /** 获取游戏状态 */
  async getGameState(gameId: string): Promise<GameStateDto> {
    if (!gameId || gameId === 'undefined') {
      console.error('[gameApi] 尝试获取游戏状态但 gameId 无效', { gameId })
      throw new Error('gameId 不能为空')
    }
    console.info('[gameApi] 获取游戏状态', { gameId })
    const response = await apiClient.get<GameStateDto>(`/api/game/${gameId}`)
    return response.data
  },

  /** 设置游戏难度，若游戏无案件则同时生成案件，返回完整 GameState */
  async setDifficulty(gameId: string, difficulty: GameDifficulty): Promise<GameStateDto> {
    validateGameId(gameId, 'setDifficulty')
    console.info('[gameApi] 设置游戏难度', { gameId, difficulty })
    const response = await apiClient.post<GameStateDto>(
      `/api/game/${gameId}/difficulty`,
      { difficulty }
    )
    return response.data
  },

  /** 获取华生对观察的评论 */
  async getWatsonObservationComment(gameId: string, observation: Observation): Promise<{ comment: string }> {
    validateGameId(gameId, 'getWatsonObservationComment')
    console.info('[gameApi] 获取华生观察评论', { gameId, observationId: observation.id })
    const response = await apiClient.post<{ comment: string }>(
      `/api/game/${gameId}/watson/observation`,
      { observation }
    )
    return response.data
  },

  /** 获取华生提示 */
  async getWatsonHint(
    gameId: string,
    hintType: string = 'idle',
    observationsCount: number = 0,
    areasExamined: number = 0,
    totalAreas: number = 0
  ): Promise<{ hint: string | null }> {
    validateGameId(gameId, 'getWatsonHint')
    console.info('[gameApi] 获取华生提示', { gameId, hintType })
    const response = await apiClient.post<{ hint: string | null }>(`/api/game/${gameId}/watson/hint`, {
      hint_type: hintType,
      observations_count: observationsCount,
      areas_examined: areasExamined,
      total_areas: totalAreas,
    })
    return response.data
  },

  /** 向嫌疑人提问 */
  async askSuspectQuestion(
    gameId: string,
    suspectId: string,
    question: string,
    conversationHistory: ConversationMessage[] = [],
    isPrivate: boolean = true,
    otherSuspectIds: string[] = []
  ): Promise<{
    suspect_id: string
    suspectId?: string
    suspect_name: string
    suspectName?: string
    response: string
    lie_detection: LieDetectionResult
    lieDetection?: LieDetectionResult
  }> {
    console.info('[gameApi] 向嫌疑人提问', { gameId, suspectId, question: question.substring(0, 50) })
    const response = await apiClient.post(`/api/game/${gameId}/interrogation/question`, {
      suspect_id: suspectId,
      question,
      conversation_history: conversationHistory,
      is_private: isPrivate,
      other_suspect_ids: otherSuspectIds,
    })
    return response.data
  },

  /** 获取嫌疑人插话 */
  async getSuspectInterjection(
    gameId: string,
    respondingSuspectId: string,
    otherSuspectId: string,
    context: string
  ): Promise<{ interjection: string | null }> {
    console.info('[gameApi] 获取嫌疑人插话', { gameId, respondingSuspectId, otherSuspectId })
    const params = new URLSearchParams({
      responding_suspect_id: respondingSuspectId,
      other_suspect_id: otherSuspectId,
      context,
    })
    const response = await apiClient.post(`/api/game/${gameId}/interrogation/interjection?${params.toString()}`)
    return response.data
  },

  /** 检测证词矛盾 */
  async checkContradictions(
    gameId: string,
    conversationHistory: ConversationMessage[] = [],
    suspectStatements: Record<string, string[]> = {}
  ): Promise<{ contradictions: ContradictionResult[]; count: number }> {
    console.info('[gameApi] 检测证词矛盾', { gameId })
    const response = await apiClient.post(`/api/game/${gameId}/interrogation/contradiction-check`, {
      conversation_history: conversationHistory,
      suspect_statements: suspectStatements,
    })
    return response.data
  },

  /** 全体质询控场 */
  async groupControl(
    gameId: string,
    action: GroupControlAction,
    targetSuspectId?: string
  ): Promise<{ success: boolean; message: string }> {
    console.info('[gameApi] 全体质询控场', { gameId, action, targetSuspectId })
    const response = await apiClient.post(`/api/game/${gameId}/interrogation/group-control`, {
      action,
      target_suspect_id: targetSuspectId,
    })
    return response.data
  },

  /** 获取推理链条 */
  async getDeductionChain(gameId: string): Promise<DeductionChain> {
    validateGameId(gameId, 'getDeductionChain')
    console.info('[gameApi] 获取推理链条', { gameId })
    const response = await apiClient.get<DeductionChain>(`/api/game/${gameId}/deduction`)
    return response.data
  },

  /** 创建推理 */
  async createInference(
    gameId: string,
    content: string,
    observationIds: string[],
    parentInferenceIds: string[] = []
  ): Promise<Inference> {
    console.info('[gameApi] 创建推理', { gameId, content, observationIds, parentInferenceIds })
    const response = await apiClient.post<Inference>(`/api/game/${gameId}/deduction/inference`, {
      content,
      observation_ids: observationIds,
      parent_inference_ids: parentInferenceIds,
    })
    return response.data
  },

  /** 创建假设 */
  async createHypothesis(
    gameId: string,
    title: string,
    description: string,
    inferenceIds: string[],
    suspectId?: string
  ): Promise<Hypothesis> {
    console.info('[gameApi] 创建假设', { gameId, title, inferenceIds, suspectId })
    const response = await apiClient.post<Hypothesis>(`/api/game/${gameId}/deduction/hypothesis`, {
      title,
      description,
      inference_ids: inferenceIds,
      suspect_id: suspectId,
    })
    return response.data
  },

  /** 验证假设 */
  async verifyHypothesis(
    gameId: string,
    hypothesisId: string,
    isVerified: boolean,
    verificationNotes?: string
  ): Promise<Hypothesis> {
    console.info('[gameApi] 验证假设', { gameId, hypothesisId, isVerified })
    const response = await apiClient.post<Hypothesis>(`/api/game/${gameId}/deduction/hypothesis/${hypothesisId}/verify`, {
      is_verified: isVerified,
      verification_notes: verificationNotes,
    })
    return response.data
  },

  /** 删除推理 */
  async deleteInference(gameId: string, inferenceId: string): Promise<{ success: boolean }> {
    console.info('[gameApi] 删除推理', { gameId, inferenceId })
    const response = await apiClient.delete(`/api/game/${gameId}/deduction/inference/${inferenceId}`)
    return response.data
  },

  /** 删除假设 */
  async deleteHypothesis(gameId: string, hypothesisId: string): Promise<{ success: boolean }> {
    console.info('[gameApi] 删除假设', { gameId, hypothesisId })
    const response = await apiClient.delete(`/api/game/${gameId}/deduction/hypothesis/${hypothesisId}`)
    return response.data
  },

  /** 获取华生对推理的反馈 */
  async getWatsonDeductionFeedback(
    gameId: string,
    inferenceIds: string[],
    hypothesisIds: string[]
  ): Promise<{ feedback: string; suggestions: string[]; logic_gaps?: any[] }> {
    console.info('[gameApi] 获取华生推理反馈', { gameId, inferenceIds, hypothesisIds })
    const response = await apiClient.post(`/api/game/${gameId}/deduction/watson-feedback`, {
      inference_ids: inferenceIds,
      hypothesis_ids: hypothesisIds,
    })
    return response.data
  },

  /** 检查结案准备状态 */
  async checkConclusionReadiness(gameId: string): Promise<ConclusionReadiness> {
    validateGameId(gameId, 'checkConclusionReadiness')
    console.info('[gameApi] 检查结案准备状态', { gameId })
    const response = await apiClient.get<ConclusionReadiness>(`/api/game/${gameId}/conclusion/readiness`)
    return response.data
  },

  /** 指认凶手（新版，传 reasoning_record_ids） */
  async makeAccusation(
    gameId: string,
    suspectId: string,
    reasoningRecordIds: string[] = []
  ): Promise<AccusationResult> {
    validateGameId(gameId, 'makeAccusation')
    console.info('[gameApi] 指认凶手', { gameId, suspectId, reasoningRecordIds })
    const response = await apiClient.post<AccusationResult>(`/api/game/${gameId}/conclusion/accuse`, {
      suspect_id: suspectId,
      reasoning_record_ids: reasoningRecordIds,
    })
    return response.data
  },

  /** 场景搜索：向场景 NPC 提问 */
  async sceneSearch(
    gameId: string,
    sceneId: string,
    query: string,
    history: Array<{ role: string; content: string }> = []
  ): Promise<SceneSearchResponse> {
    validateGameId(gameId, 'sceneSearch')
    console.info('[gameApi] 场景搜索', { gameId, sceneId, query: query.substring(0, 50) })
    const response = await apiClient.post<SceneSearchResponse>(
      `/api/game/${gameId}/scene/${sceneId}/search`,
      { query, history }
    )
    return response.data
  },

  /** 添加/标记线索 */
  async addClue(
    gameId: string,
    payload: {
      userLabel: string
      description: string
      sourceType: 'scene' | 'interrogation'
      sourceRef?: string
      baseClueId?: string
      quotedText?: string
    }
  ): Promise<Clue> {
    validateGameId(gameId, 'addClue')
    console.info('[gameApi] 添加线索', { gameId, userLabel: payload.userLabel })
    const response = await apiClient.post<Clue>(`/api/game/${gameId}/clues`, payload)
    return response.data
  },

  /** 提交组合推理，经 OracleAgent 验证 */
  async submitReasoning(
    gameId: string,
    clueIds: string[],
    conclusion: string
  ): Promise<{
    inference: ReasoningRecord
    verificationResult: 'correct' | 'wrong' | 'partial'
    score: number
    explanation: string
    missingLinks: string[]
    misusedClues: string[]
  }> {
    validateGameId(gameId, 'submitReasoning')
    console.info('[gameApi] 提交推理', { gameId, clueIds, conclusion: conclusion.substring(0, 50) })
    const response = await apiClient.post(`/api/game/${gameId}/deduction/reasoning`, {
      clue_ids: clueIds,
      conclusion,
    })
    return response.data
  },

  /** 从审讯片段生成线索 */
  async extractClueFromInterrogation(
    gameId: string,
    payload: {
      suspectId: string
      quotedText: string
      contextMessages: Array<{ role: string; content: string }>
      userLabel: string
    }
  ): Promise<Clue> {
    validateGameId(gameId, 'extractClueFromInterrogation')
    console.info('[gameApi] 从审讯提取线索', { gameId, suspectId: payload.suspectId })
    const response = await apiClient.post<Clue>(
      `/api/game/${gameId}/interrogation/extract-clue`,
      payload
    )
    return response.data
  },

  /** 获取华生审讯实时提示 */
  async getInterrogationTips(
    gameId: string,
    suspectId: string,
    history: Array<{ role: string; content: string }> = []
  ): Promise<{ tips: WatsonTip[] }> {
    validateGameId(gameId, 'getInterrogationTips')
    console.info('[gameApi] 获取审讯华生提示', { gameId, suspectId })
    const response = await apiClient.post<{ tips: WatsonTip[] }>(
      `/api/game/${gameId}/interrogation/watson-tips`,
      { suspect_id: suspectId, conversation_history: history }
    )
    return response.data
  },

  /** 获取案件真相 */
  async getCaseReveal(gameId: string): Promise<CaseReveal> {
    validateGameId(gameId, 'getCaseReveal')
    console.info('[gameApi] 获取案件真相', { gameId })
    const response = await apiClient.get<CaseReveal>(`/api/game/${gameId}/conclusion/reveal`)
    return response.data
  },

  /** 与华生对话 */
  async sendWatsonMessage(
    gameId: string,
    message: string
  ): Promise<{
    message: string
    messageType: WatsonMessageType
  }> {
    validateGameId(gameId, 'sendWatsonMessage')
    console.info('[gameApi] 与华生对话', { gameId, message: message.substring(0, 50) })
    const response = await apiClient.post<{
      message: string
      messageType: WatsonMessageType
    }>(`/api/game/${gameId}/watson/chat`, { message })
    return response.data
  },

  /** 获取华生对话历史 */
  async getWatsonChatHistory(gameId: string): Promise<{
    messages: WatsonChatMessage[]
  }> {
    validateGameId(gameId, 'getWatsonChatHistory')
    console.info('[gameApi] 获取华生对话历史', { gameId })
    const response = await apiClient.get<{
      messages: WatsonChatMessage[]
    }>(`/api/game/${gameId}/watson/history`)
    return response.data
  },
}

export const redemptionApi = {
  /** 生成兑换码（管理员调用） */
  async generate(): Promise<RedemptionGenerateResponse> {
    console.info('[redemptionApi] 生成兑换码')
    const response = await apiClient.post<RedemptionGenerateResponse>('/api/redemption/generate')
    return response.data
  },

  /** 验证兑换码，成功后返回 game_id */
  async verify(code: string): Promise<RedemptionVerifyResponse> {
    const maskedCode = code.length > 4 ? `${code.slice(0, 4)}***` : '***'
    console.info('[redemptionApi] 验证兑换码', { code: maskedCode })
    const response = await apiClient.post<RedemptionVerifyResponse>('/api/redemption/verify', { code })
    return response.data
  },
}

export default apiClient
