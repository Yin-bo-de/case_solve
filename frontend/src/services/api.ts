// API 服务
import axios from 'axios'
import type { GameState, GameDifficulty } from '@/types/game'

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
}

export default apiClient
