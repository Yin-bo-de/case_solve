import { create } from 'zustand'
import { devtools, persist, createJSONStorage } from 'zustand/middleware'
import { createGameScopedStorage } from './gameScopedStorage'
import type { ConversationMessage, LieDetectionResult, ContradictionResult } from '@/services/api'
import type { WatsonTip, Clue } from '@/types/game'
import { gameApi } from '@/services/api'

console.debug('[interrogationStore.ts] 加载模块')

// 审讯模式
export type InterrogationMode = 'private' | 'group'

// 全体质询消息类型
export interface GroupMessage {
  id: string
  role: 'user' | 'suspect' | 'watson' | 'system' | 'interjection'
  content: string
  suspectId?: string
  suspectName?: string
  timestamp: string
}

// @提及的嫌疑人
export interface MentionedSuspect {
  id: string
  name: string
}

interface InterrogationStore {
  // 审讯模式
  mode: InterrogationMode

  // 密室问话状态
  conversationHistory: ConversationMessage[]
  selectedSuspectId: string | null

  // 全体质询状态
  groupMessages: GroupMessage[]
  mentionedSuspects: MentionedSuspect[]
  interjectionCounts: Record<string, number>
  suspectStatements: Record<string, string[]>
  showContradictionAlert: boolean
  contradictions: ContradictionResult[]

  // Lie detection 状态
  lieDetection: LieDetectionResult | null

  // Actions - 模式
  setMode: (mode: InterrogationMode) => void

  // Actions - 密室问话
  addConversationMessage: (message: ConversationMessage) => void
  setConversationHistory: (messages: ConversationMessage[]) => void
  clearConversationHistory: () => void
  setSelectedSuspectId: (suspectId: string | null) => void
  setLieDetection: (detection: LieDetectionResult | null) => void
  clearPrivateInterrogation: () => void

  // Actions - 全体质询
  addGroupMessage: (message: GroupMessage) => void
  setGroupMessages: (messages: GroupMessage[]) => void
  clearGroupMessages: () => void
  addMentionedSuspect: (suspect: MentionedSuspect) => void
  removeMentionedSuspect: (suspectId: string) => void
  clearMentionedSuspects: () => void
  setMentionedSuspects: (suspects: MentionedSuspect[]) => void
  updateInterjectionCount: (suspectId: string, delta: number) => void
  resetInterjectionCounts: () => void
  addSuspectStatement: (suspectId: string, statement: string) => void
  setShowContradictionAlert: (show: boolean) => void
  setContradictions: (contradictions: ContradictionResult[]) => void
  clearGroupInterrogation: () => void

  // 华生实时提示（单独审讯）
  watsonTips: WatsonTip[]
  watsonTipsLoading: boolean
  /** 审讯中提取的线索（本地缓存，真实数据存 cluesStore） */
  extractedClues: Clue[]

  // Actions - 华生提示
  fetchTips: (gameId: string, suspectId: string, history: ConversationMessage[]) => Promise<void>
  extractClue: (
    gameId: string,
    payload: { suspectId: string; quotedText: string; contextMessages: ConversationMessage[]; userLabel: string }
  ) => Promise<Clue>
  clearWatsonTips: () => void

  // Actions - 通用
  resetAll: () => void
}

export const useInterrogationStore = create<InterrogationStore>()(
  devtools(
    persist(
      (set) => {
        console.debug('[interrogationStore] 初始化 store')

        return {
          // 初始状态
          mode: 'private',
          conversationHistory: [],
          selectedSuspectId: null,
          groupMessages: [],
          mentionedSuspects: [],
          interjectionCounts: {},
          suspectStatements: {},
          showContradictionAlert: false,
          contradictions: [],
          lieDetection: null,
          watsonTips: [],
          watsonTipsLoading: false,
          extractedClues: [],

          // Actions - 模式
          setMode: (mode) => {
            set({ mode })
            console.info('[interrogationStore] 设置审讯模式', { mode })
          },

          // 密室问话 Actions
          addConversationMessage: (message) => {
            set((state) => ({ conversationHistory: [...state.conversationHistory, message] }))
            console.info('[interrogationStore] 添加对话消息', { role: message.role })
          },

          setConversationHistory: (messages) => {
            set({ conversationHistory: messages })
            console.debug('[interrogationStore] 设置对话历史', { count: messages.length })
          },

          clearConversationHistory: () => {
            set({ conversationHistory: [] })
            console.info('[interrogationStore] 清空对话历史')
          },

          setSelectedSuspectId: (suspectId) => {
            set({ selectedSuspectId: suspectId })
            console.debug('[interrogationStore] 设置选中的嫌疑人', { suspectId })
          },

          setLieDetection: (detection) => {
            set({ lieDetection: detection })
            if (detection) {
              console.info('[interrogationStore] 设置谎言检测结果', detection)
            }
          },

          clearPrivateInterrogation: () => {
            set({
              conversationHistory: [],
              selectedSuspectId: null,
              lieDetection: null,
            })
            console.info('[interrogationStore] 清空单独审讯状态')
          },

          // 全体质询 Actions
          addGroupMessage: (message) => {
            set((state) => ({ groupMessages: [...state.groupMessages, message] }))
            console.info('[interrogationStore] 添加全体质询消息', { role: message.role, suspectName: message.suspectName })
          },

          setGroupMessages: (messages) => {
            set({ groupMessages: messages })
            console.debug('[interrogationStore] 设置全体质询消息', { count: messages.length })
          },

          clearGroupMessages: () => {
            set({ groupMessages: [] })
            console.info('[interrogationStore] 清空全体质询消息')
          },

          addMentionedSuspect: (suspect) => {
            set((state) => {
              const exists = state.mentionedSuspects.some((s) => s.id === suspect.id)
              if (exists) return state
              return { mentionedSuspects: [...state.mentionedSuspects, suspect] }
            })
            console.info('[interrogationStore] 添加提及嫌疑人', { suspectId: suspect.id })
          },

          removeMentionedSuspect: (suspectId) => {
            set((state) => ({
              mentionedSuspects: state.mentionedSuspects.filter((s) => s.id !== suspectId),
            }))
            console.info('[interrogationStore] 移除提及嫌疑人', { suspectId })
          },

          clearMentionedSuspects: () => {
            set({ mentionedSuspects: [] })
            console.info('[interrogationStore] 清空提及嫌疑人')
          },

          setMentionedSuspects: (suspects) => {
            set({ mentionedSuspects: suspects })
            console.debug('[interrogationStore] 设置提及嫌疑人', { count: suspects.length })
          },

          updateInterjectionCount: (suspectId, delta) => {
            set((state) => ({
              interjectionCounts: {
                ...state.interjectionCounts,
                [suspectId]: (state.interjectionCounts[suspectId] || 0) + delta,
              },
            }))
          },

          resetInterjectionCounts: () => {
            set({ interjectionCounts: {} })
            console.info('[interrogationStore] 重置打断计数')
          },

          addSuspectStatement: (suspectId, statement) => {
            set((state) => ({
              suspectStatements: {
                ...state.suspectStatements,
                [suspectId]: [...(state.suspectStatements[suspectId] || []), statement],
              },
            }))
          },

          setShowContradictionAlert: (show) => {
            set({ showContradictionAlert: show })
          },

          setContradictions: (contradictions) => {
            set({ contradictions })
            console.debug('[interrogationStore] 设置矛盾结果', { count: contradictions.length })
          },

          clearGroupInterrogation: () => {
            set({
              groupMessages: [],
              mentionedSuspects: [],
              contradictions: [],
              interjectionCounts: {},
              suspectStatements: {},
              showContradictionAlert: false,
            })
            console.info('[interrogationStore] 清空全体质询状态')
          },

          // Actions - 华生提示
          fetchTips: async (gameId, suspectId, history) => {
            console.info('[interrogationStore] 获取华生审讯提示', { gameId, suspectId })
            set({ watsonTipsLoading: true })
            try {
              const apiHistory = history.map((m) => ({ role: m.role, content: m.content }))
              const result = await gameApi.getInterrogationTips(gameId, suspectId, apiHistory)
              set({ watsonTips: result.tips, watsonTipsLoading: false })
              console.info('[interrogationStore] 华生提示已更新', { count: result.tips.length })
            } catch (err) {
              console.error('[interrogationStore] 获取华生提示失败', err)
              set({ watsonTipsLoading: false })
            }
          },

          extractClue: async (gameId, payload) => {
            console.info('[interrogationStore] 提取审讯线索', { gameId, suspectId: payload.suspectId })
            const clue = await gameApi.extractClueFromInterrogation(gameId, payload)
            set((state) => ({ extractedClues: [...state.extractedClues, clue] }))
            console.info('[interrogationStore] 审讯线索已提取', { clueId: clue.id })
            return clue
          },

          clearWatsonTips: () => {
            set({ watsonTips: [], watsonTipsLoading: false })
          },

          // Actions - 通用
          resetAll: () => {
            set({
              mode: 'private',
              conversationHistory: [],
              selectedSuspectId: null,
              groupMessages: [],
              mentionedSuspects: [],
              interjectionCounts: {},
              suspectStatements: {},
              showContradictionAlert: false,
              contradictions: [],
              lieDetection: null,
              watsonTips: [],
              watsonTipsLoading: false,
              extractedClues: [],
            })
            console.info('[interrogationStore] 重置所有状态')
          },
        }
      },
      {
        name: 'interrogation-store',
        storage: createJSONStorage(() => createGameScopedStorage('interrogation-store')),
        partialize: (state) => ({
          mode: state.mode,
          conversationHistory: state.conversationHistory,
          selectedSuspectId: state.selectedSuspectId,
          groupMessages: state.groupMessages,
          mentionedSuspects: state.mentionedSuspects,
          interjectionCounts: state.interjectionCounts,
          suspectStatements: state.suspectStatements,
          contradictions: state.contradictions,
        }),
      }
    ),
    { name: 'InterrogationStore' }
  )
)
