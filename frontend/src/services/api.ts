// API 服务
import axios from 'axios'
import type { GameState, GameDifficulty, Observation } from '@/types/game'

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
}

export default apiClient
