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
}

export default apiClient
