import { create } from 'zustand'
import type { WatsonChatMessage } from '@/types/game'
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
  }
})
