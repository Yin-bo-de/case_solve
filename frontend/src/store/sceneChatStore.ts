import { create } from 'zustand'
import { devtools, persist, createJSONStorage } from 'zustand/middleware'
import { createGameScopedStorage } from './gameScopedStorage'
import type { SceneSearchResponse } from '@/types/game'

console.debug('[sceneChatStore.ts] 加载模块')

export interface SceneChatMessage {
  role: 'user' | 'npc'
  content: string
  candidates?: SceneSearchResponse['clueCandidates']
  dialogOptions?: string[]
}

interface SceneChatStore {
  // key: sceneId, value: 该场景的聊天记录
  messagesByScene: Record<string, SceneChatMessage[]>

  addMessage: (sceneId: string, message: SceneChatMessage) => void
  getMessages: (sceneId: string) => SceneChatMessage[]
  clearScene: (sceneId: string) => void
  resetAll: () => void
}

export const useSceneChatStore = create<SceneChatStore>()(
  devtools(
    persist(
      (set, get) => ({
        messagesByScene: {},

        addMessage: (sceneId, message) => {
          console.info('[sceneChatStore] addMessage', { sceneId, role: message.role })
          set((state) => ({
            messagesByScene: {
              ...state.messagesByScene,
              [sceneId]: [...(state.messagesByScene[sceneId] ?? []), message],
            },
          }))
        },

        getMessages: (sceneId) => {
          return get().messagesByScene[sceneId] ?? []
        },

        clearScene: (sceneId) => {
          console.info('[sceneChatStore] clearScene', { sceneId })
          set((state) => {
            const next = { ...state.messagesByScene }
            delete next[sceneId]
            return { messagesByScene: next }
          })
        },

        resetAll: () => {
          console.info('[sceneChatStore] resetAll')
          set({ messagesByScene: {} })
        },
      }),
      {
        name: 'scene-chat',
        storage: createJSONStorage(() => createGameScopedStorage('scene-chat')),
        partialize: (state) => ({
          messagesByScene: state.messagesByScene,
        }),
      }
    ),
    { name: 'SceneChatStore' }
  )
)
