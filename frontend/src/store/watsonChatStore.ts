import { create } from 'zustand'
import type { WatsonChatMessage, WatsonMessageType, Observation } from '@/types/game'
import { gameApi } from '@/services/api'

console.debug('[watsonChatStore.ts] 加载模块')

interface WatsonChatStore {
  // 状态
  messages: WatsonChatMessage[]
  isLoading: boolean
  error: string | null
  isDialogOpen: boolean
  isDialogExpanded: boolean

  // Actions
  sendMessage: (gameId: string, message: string) => Promise<void>
  fetchHistory: (gameId: string) => Promise<void>
  clearMessages: () => void
  setLoading: (isLoading: boolean) => void
  setError: (error: string | null) => void
  setDialogOpen: (isOpen: boolean) => void
  setDialogExpanded: (isExpanded: boolean) => void

  // 华生主动提示相关
  addWatsonMessage: (content: string, messageType: WatsonMessageType) => void
  requestObservationComment: (gameId: string, observation: Observation) => Promise<void>
  requestIdleHint: (gameId: string, observationsCount: number, areasExamined: number, totalAreas: number) => Promise<void>
}

export const useWatsonChatStore = create<WatsonChatStore>((set, get) => {
  console.debug('[watsonChatStore] 初始化 store')

  return {
    messages: [],
    isLoading: false,
    error: null,
    isDialogOpen: true,
    isDialogExpanded: true,

    sendMessage: async (gameId: string, message: string) => {
      console.info('[watsonChatStore] 发送消息给华生', { gameId, message: message.substring(0, 50) })

      set(() => ({
        isLoading: true,
        error: null,
      }))

      try {
        const response = await gameApi.sendWatsonMessage(gameId, message)
        console.info('[watsonChatStore] 收到华生回复', { messageType: response.messageType })

        // 获取完整历史
        await get().fetchHistory(gameId)
      } catch (error) {
        console.error('[watsonChatStore] 发送消息失败', error)
        set({
          isLoading: false,
          error: '发送消息失败，请重试',
        })
      }
    },

    fetchHistory: async (gameId: string) => {
      console.info('[watsonChatStore] 获取对话历史', { gameId })

      try {
        const response = await gameApi.getWatsonChatHistory(gameId)
        console.debug('[watsonChatStore] 对话历史获取成功', { count: response.messages.length })
        set({
          messages: response.messages,
          isLoading: false,
          error: null,
        })
      } catch (error) {
        console.error('[watsonChatStore] 获取对话历史失败', error)
        set({
          isLoading: false,
          error: '获取对话历史失败',
        })
      }
    },

    clearMessages: () => {
      console.info('[watsonChatStore] 清空对话历史')
      set({ messages: [] })
    },

    setLoading: (isLoading: boolean) => {
      console.debug('[watsonChatStore] 设置加载状态', { isLoading })
      set({ isLoading })
    },

    setError: (error: string | null) => {
      if (error) {
        console.error('[watsonChatStore] 设置错误', { error })
      } else {
        console.debug('[watsonChatStore] 清除错误')
      }
      set({ error })
    },

    setDialogOpen: (isOpen: boolean) => {
      console.info('[watsonChatStore] 设置对话框显示状态', { isOpen })
      set({ isDialogOpen: isOpen })
    },

    setDialogExpanded: (isExpanded: boolean) => {
      console.info('[watsonChatStore] 设置对话框展开状态', { isExpanded })
      set({ isDialogExpanded: isExpanded })
    },

    // 添加华生的主动提示（不调用后端 API）
    addWatsonMessage: (content: string, messageType: WatsonMessageType = 'general') => {
      console.info('[watsonChatStore] 添加华生主动提示', { content: content.substring(0, 50), messageType })
      const message: WatsonChatMessage = {
        id: `watson-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role: 'watson',
        content,
        messageType,
        timestamp: new Date().toISOString(),
      }
      set((state) => ({ messages: [...state.messages, message] }))
    },

    // 请求华生对观察的评论（调用后端 API）
    requestObservationComment: async (gameId: string, observation: Observation) => {
      console.info('[watsonChatStore] 请求华生观察评论', { gameId, observationId: observation.id })

      try {
        set({ isLoading: true, error: null })

        const response = await gameApi.getWatsonObservationComment(gameId, observation)
        console.info('[watsonChatStore] 收到华生观察评论')

        // 使用 addWatsonMessage 添加消息
        get().addWatsonMessage(response.comment, 'clue_discussion')
      } catch (error) {
        console.error('[watsonChatStore] 请求华生观察评论失败', error)
        set({ error: '获取华生评论失败' })
      } finally {
        set({ isLoading: false })
      }
    },

    // 请求华生空闲提示（调用后端 API）
    requestIdleHint: async (
      gameId: string,
      observationsCount: number,
      areasExamined: number,
      totalAreas: number
    ) => {
      console.info('[watsonChatStore] 请求华生空闲提示', { gameId, observationsCount, areasExamined })

      try {
        set({ isLoading: true, error: null })

        const response = await gameApi.getWatsonHint(
          gameId,
          'idle',
          observationsCount,
          areasExamined,
          totalAreas
        )

        if (response.hint) {
          console.info('[watsonChatStore] 收到华生空闲提示')
          get().addWatsonMessage(response.hint, 'guidance')
        } else {
          console.debug('[watsonChatStore] 华生没有提供空闲提示')
        }
      } catch (error) {
        console.error('[watsonChatStore] 请求华生空闲提示失败', error)
        set({ error: '获取华生提示失败' })
      } finally {
        set({ isLoading: false })
      }
    },
  }
})
