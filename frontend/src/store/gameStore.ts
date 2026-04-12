import { create } from 'zustand'
import type { GameState, Case, GameDifficulty, GamePhase } from '@/types/game'

console.debug('[gameStore.ts] 加载模块')

interface GameStore {
  // 状态
  gameState: GameState | null
  isLoading: boolean
  error: string | null

  // Actions
  setGameState: (gameState: GameState) => void
  setCase: (caseData: Case) => void
  setDifficulty: (difficulty: GameDifficulty) => void
  setPhase: (phase: GamePhase) => void
  addInterviewedSuspect: (suspectId: string) => void
  incrementMistakes: () => void
  setLoading: (isLoading: boolean) => void
  setError: (error: string | null) => void
  resetGame: () => void
}

export const useGameStore = create<GameStore>((set) => {
  console.debug('[gameStore] 初始化 store')

  return {
    gameState: null,
    isLoading: false,
    error: null,

    setGameState: (gameState: GameState) => {
      console.info('[gameStore] 设置游戏状态', { gameId: gameState.gameId })
      set({ gameState })
    },

    setCase: (caseData: Case) => {
      console.info('[gameStore] 设置案件', { caseId: caseData.id })
      set((state) => ({
        gameState: state.gameState
          ? {
              ...state.gameState,
              case: caseData,
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    setDifficulty: (difficulty: GameDifficulty) => {
      console.info('[gameStore] 设置难度', { difficulty })
      set((state) => ({
        gameState: state.gameState
          ? {
              ...state.gameState,
              difficulty,
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    setPhase: (phase: GamePhase) => {
      console.info('[gameStore] 设置游戏阶段', { phase })
      set((state) => ({
        gameState: state.gameState
          ? {
              ...state.gameState,
              phase,
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    addInterviewedSuspect: (suspectId: string) => {
      console.info('[gameStore] 添加已审讯嫌疑人', { suspectId })
      set((state) => {
        if (!state.gameState) return state

        const alreadyInterviewed = state.gameState.interviewedSuspectIds.includes(suspectId)
        if (alreadyInterviewed) return state

        return {
          gameState: {
            ...state.gameState,
            interviewedSuspectIds: [...state.gameState.interviewedSuspectIds, suspectId],
            updatedAt: new Date().toISOString(),
          },
        }
      })
    },

    incrementMistakes: () => {
      console.info('[gameStore] 增加错误次数')
      set((state) => ({
        gameState: state.gameState
          ? {
              ...state.gameState,
              mistakesMade: state.gameState.mistakesMade + 1,
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    setLoading: (isLoading: boolean) => {
      console.debug('[gameStore] 设置加载状态', { isLoading })
      set({ isLoading })
    },

    setError: (error: string | null) => {
      if (error) {
        console.error('[gameStore] 设置错误', { error })
      } else {
        console.debug('[gameStore] 清除错误')
      }
      set({ error })
    },

    resetGame: () => {
      console.info('[gameStore] 重置游戏')
      set({
        gameState: null,
        isLoading: false,
        error: null,
      })
    },
  }
})
