// API 服务
import axios from 'axios'
import type { GameState, GameDifficulty, Observation, Inference, Hypothesis, DeductionChain } from '@/types/game'

console.info('[api.ts] 初始化 API 服务')

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 记录所有 API 请求
apiClient.interceptors.request.use(
  (config) => {
    console.debug(`[API] 请求: ${config.method?.toUpperCase()} ${config.url}`, config.data || '')
    return config
  },
  (error) => {
    console.error('[API] 请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器 - 记录所有 API 响应
apiClient.interceptors.response.use(
  (response) => {
    console.debug(`[API] 响应: ${response.status}`, response.data)
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

// 谎言检测结果类型
export interface LieDetectionResult {
  lie_detected: boolean
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
  async createNewGame(difficulty: GameDifficulty = 'classic'): Promise<GameState> {
    console.info('[gameApi] 创建新游戏', { difficulty })
    const response = await apiClient.post<GameState>('/api/game/new', { difficulty })
    return response.data
  },

  /** 获取游戏状态 */
  async getGameState(gameId: string): Promise<GameState> {
    console.info('[gameApi] 获取游戏状态', { gameId })
    const response = await apiClient.get<GameState>(`/api/game/${gameId}`)
    return response.data
  },

  /** 设置游戏难度 */
  async setDifficulty(gameId: string, difficulty: GameDifficulty): Promise<{ gameId: string; difficulty: GameDifficulty }> {
    console.info('[gameApi] 设置游戏难度', { gameId, difficulty })
    const response = await apiClient.post<{ gameId: string; difficulty: GameDifficulty }>(
      `/api/game/${gameId}/difficulty`,
      { difficulty }
    )
    return response.data
  },

  /** 获取华生对观察的评论 */
  async getWatsonObservationComment(gameId: string, observation: Observation): Promise<{ comment: string }> {
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
    suspect_name: string
    response: string
    lie_detection: LieDetectionResult
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
}

export default apiClient
