import { create } from 'zustand'
import { devtools, persist, createJSONStorage } from 'zustand/middleware'
import { createGameScopedStorage } from './gameScopedStorage'
import type { ConversationMessage, LieDetectionResult, ContradictionResult } from '@/services/api'
import type { WatsonTip, Clue, CredibilityCheckResult, ActorType, NarrativeBlock, NarrativeEvent } from '@/types/game'
import { gameApi } from '@/services/api'
import { useGameStore } from './gameStore'

console.debug('[interrogationStore.ts] 加载模块')

// 审讯模式
export type InterrogationMode = 'private' | 'group'

// 左栏 Tab 类型
export type SelectedTab = 'suspects' | 'witnesses' | 'experts'

// 证人/专家对话消息（role 扩展到 witness/expert）
export interface ActorMessage {
  role: 'user' | 'witness' | 'expert'
  content: string
  timestamp?: string
}

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

  // 左栏 Tab（嫌疑人/证人/专家）
  selectedTab: SelectedTab

  // 密室问话状态
  conversationHistoryBySuspect: Record<string, ConversationMessage[]>
  selectedSuspectId: string | null
  getCurrentConversationHistory: (suspectId?: string) => ConversationMessage[]

  // 证人状态（并存字段）
  selectedWitnessId: string | null
  witnessConversationsByWitnessId: Record<string, ActorMessage[]>
  witnessCredibilityCheck: CredibilityCheckResult | null
  witnessWatsonTips: WatsonTip[]
  witnessWatsonTipsLoading: boolean

  // 专家状态（并存字段）
  selectedExpertId: string | null
  expertConversationsByExpertId: Record<string, ActorMessage[]>
  expertReportLoadedById: Record<string, boolean>

  // 从证人/专家提取的线索（本地缓存，真实数据存 cluesStore）
  extractedActorClues: Clue[]

  // 全体质询状态
  groupMessages: GroupMessage[]
  mentionedSuspects: MentionedSuspect[]
  interjectionCounts: Record<string, number>
  suspectStatements: Record<string, string[]>
  showContradictionAlert: boolean
  contradictions: ContradictionResult[]

  // Lie detection 状态
  lieDetection: LieDetectionResult | null

  // Actions - 模式与 Tab
  setMode: (mode: InterrogationMode) => void
  setSelectedTab: (tab: SelectedTab) => void

  // Actions - 密室问话
  addConversationMessage: (message: ConversationMessage, suspectId?: string) => void
  setConversationHistory: (messages: ConversationMessage[], suspectId?: string) => void
  clearConversationHistory: (suspectId?: string) => void
  setSelectedSuspectId: (suspectId: string | null) => void
  setLieDetection: (detection: LieDetectionResult | null) => void
  clearPrivateInterrogation: () => void

  // Actions - 证人
  setSelectedWitnessId: (witnessId: string | null) => void
  addWitnessConversationMessage: (message: ActorMessage, witnessId: string) => void
  setWitnessCredibilityCheck: (check: CredibilityCheckResult | null) => void
  fetchWitnessTips: (gameId: string, witnessId: string, history: ActorMessage[]) => Promise<void>

  // Actions - 专家
  setSelectedExpertId: (expertId: string | null) => void
  addExpertConversationMessage: (message: ActorMessage, expertId: string) => void
  markExpertReportLoaded: (expertId: string) => void

  // Actions - 证人/专家提取线索
  extractClueFromActor: (
    gameId: string,
    payload: {
      actorType: Exclude<ActorType, 'suspect'>
      actorId: string
      quotedText: string
      contextMessages: ActorMessage[]
      userLabel: string
    }
  ) => Promise<Clue>

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

  // 华生实时提示（单独审讯嫌疑人）
  watsonTips: WatsonTip[]
  watsonTipsLoading: boolean
  /** 审讯嫌疑人中提取的线索（本地缓存，真实数据存 cluesStore） */
  extractedClues: Clue[]

  // Actions - 华生提示（嫌疑人）
  fetchTips: (gameId: string, suspectId: string, history: ConversationMessage[]) => Promise<void>
  extractClue: (
    gameId: string,
    payload: { suspectId: string; quotedText: string; contextMessages: ConversationMessage[]; userLabel: string }
  ) => Promise<Clue>
  clearWatsonTips: () => void

  // P3: 嫌疑人状态机（calm / pressured / broken）
  suspectStates: Record<string, 'calm' | 'pressured' | 'broken'>

  // P6: Narrative state
  suspectPressures: Record<string, number>  // suspect_id -> pressure (0.0-1.0)
  lastNarrativeBlock: NarrativeBlock | null
  narrativeEvents: NarrativeEvent[]

  // P2: 出示线索对质
  confrontLoading: boolean
  confrontSuspectWithClue: (
    gameId: string,
    suspectId: string,
    clueId: string,
    clueLabel: string,
    conversationHistory: ConversationMessage[]
  ) => Promise<{
    response: string
    relevance: string
    clueAfter: Clue
    conversationMessage: { role: string; content: string; timestamp: string }
  } | null>

  // P6: Narrative Director
  setNarrativeBlock: (suspectId: string, block: NarrativeBlock) => void

  // Actions - 通用
  resetAll: () => void
}

export const useInterrogationStore = create<InterrogationStore>()(
  devtools(
    persist(
      (set, get) => {
        console.debug('[interrogationStore] 初始化 store')

        return {
          // 初始状态
          mode: 'private',
          selectedTab: 'suspects',
          conversationHistoryBySuspect: {},
          selectedSuspectId: null,
          // 证人初始状态
          selectedWitnessId: null,
          witnessConversationsByWitnessId: {},
          witnessCredibilityCheck: null,
          witnessWatsonTips: [],
          witnessWatsonTipsLoading: false,
          // 专家初始状态
          selectedExpertId: null,
          expertConversationsByExpertId: {},
          expertReportLoadedById: {},
          extractedActorClues: [],
          // 全体质询
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
          confrontLoading: false,
          suspectStates: {},
          suspectPressures: {},
          lastNarrativeBlock: null,
          narrativeEvents: [],

          // Actions - 模式与 Tab
          setMode: (mode) => {
            set({ mode })
            console.info('[interrogationStore] 设置审讯模式', { mode })
          },

          setSelectedTab: (tab) => {
            set({ selectedTab: tab })
            console.info('[interrogationStore] 切换左栏 Tab', { tab })
          },

          // 密室问话 Actions
          addConversationMessage: (message, targetSuspectId) => {
            set((state) => {
              const suspectId = targetSuspectId || state.selectedSuspectId || 'default'
              return {
                conversationHistoryBySuspect: {
                  ...state.conversationHistoryBySuspect,
                  [suspectId]: [...(state.conversationHistoryBySuspect[suspectId] || []), message],
                },
              }
            })
            console.info('[interrogationStore] 添加对话消息', { role: message.role, suspectId: targetSuspectId })
          },

          setConversationHistory: (messages, targetSuspectId) => {
            set((state) => {
              const suspectId = targetSuspectId || state.selectedSuspectId || 'default'
              return {
                conversationHistoryBySuspect: {
                  ...state.conversationHistoryBySuspect,
                  [suspectId]: messages,
                },
              }
            })
            console.debug('[interrogationStore] 设置对话历史', { count: messages.length, suspectId: targetSuspectId })
          },

          clearConversationHistory: (targetSuspectId) => {
            set((state) => {
              const suspectId = targetSuspectId || state.selectedSuspectId || 'default'
              const next = { ...state.conversationHistoryBySuspect }
              delete next[suspectId]
              return { conversationHistoryBySuspect: next }
            })
            console.info('[interrogationStore] 清空对话历史', { suspectId: targetSuspectId })
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
            set((state) => {
              const suspectId = state.selectedSuspectId || 'default'
              const next = { ...state.conversationHistoryBySuspect }
              delete next[suspectId]
              return {
                conversationHistoryBySuspect: next,
                selectedSuspectId: null,
                lieDetection: null,
              }
            })
            console.info('[interrogationStore] 清空单独审讯状态')
          },

          getCurrentConversationHistory: (targetSuspectId) => {
            const state = get()
            const suspectId = targetSuspectId || state.selectedSuspectId || 'default'
            return state.conversationHistoryBySuspect[suspectId] || []
          },

          // Actions - 证人
          setSelectedWitnessId: (witnessId) => {
            set({ selectedWitnessId: witnessId, witnessCredibilityCheck: null })
            console.debug('[interrogationStore] 设置选中的证人', { witnessId })
          },

          addWitnessConversationMessage: (message, witnessId) => {
            set((state) => ({
              witnessConversationsByWitnessId: {
                ...state.witnessConversationsByWitnessId,
                [witnessId]: [...(state.witnessConversationsByWitnessId[witnessId] || []), message],
              },
            }))
            console.info('[interrogationStore] 添加证人对话消息', { role: message.role, witnessId })
          },

          setWitnessCredibilityCheck: (check) => {
            set({ witnessCredibilityCheck: check })
            if (check) {
              console.info('[interrogationStore] 设置证人可信度检测结果', check)
            }
          },

          fetchWitnessTips: async (gameId, witnessId, history) => {
            console.info('[interrogationStore] 获取证人审讯提示', { gameId, witnessId })
            set({ witnessWatsonTipsLoading: true })
            try {
              const apiHistory = history.map((m) => ({ role: m.role, content: m.content }))
              const result = await gameApi.getWitnessInterrogationTips(gameId, witnessId, apiHistory)
              set({ witnessWatsonTips: result.tips, witnessWatsonTipsLoading: false })
              console.info('[interrogationStore] 证人审讯提示已更新', { count: result.tips.length })
            } catch (err) {
              console.error('[interrogationStore] 获取证人审讯提示失败', err)
              set({ witnessWatsonTipsLoading: false })
            }
          },

          // Actions - 专家
          setSelectedExpertId: (expertId) => {
            set({ selectedExpertId: expertId })
            console.debug('[interrogationStore] 设置选中的专家', { expertId })
          },

          addExpertConversationMessage: (message, expertId) => {
            set((state) => ({
              expertConversationsByExpertId: {
                ...state.expertConversationsByExpertId,
                [expertId]: [...(state.expertConversationsByExpertId[expertId] || []), message],
              },
            }))
            console.info('[interrogationStore] 添加专家对话消息', { role: message.role, expertId })
          },

          markExpertReportLoaded: (expertId) => {
            set((state) => ({
              expertReportLoadedById: { ...state.expertReportLoadedById, [expertId]: true },
            }))
            console.info('[interrogationStore] 标记专家报告已加载', { expertId })
          },

          // Actions - 证人/专家提取线索
          extractClueFromActor: async (gameId, payload) => {
            console.info('[interrogationStore] 从角色对话提取线索', { gameId, actorType: payload.actorType, actorId: payload.actorId })
            const apiPayload = {
              actorType: payload.actorType,
              actorId: payload.actorId,
              quotedText: payload.quotedText,
              contextMessages: payload.contextMessages.map((m) => ({ role: m.role, content: m.content })),
              userLabel: payload.userLabel,
            }
            const clue = await gameApi.extractClueFromActor(gameId, apiPayload)
            set((state) => ({ extractedActorClues: [...state.extractedActorClues, clue] }))
            console.info('[interrogationStore] 角色线索已提取', { clueId: clue.id, actorType: payload.actorType })
            return clue
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

          // P2: 出示线索对质
          confrontSuspectWithClue: async (gameId, suspectId, clueId, clueLabel, conversationHistory) => {
            console.info('[interrogationStore] 出示线索对质', { gameId, suspectId, clueId })
            set({ confrontLoading: true })
            try {
              // 先写入"侦探出示线索"消息
              const confrontMessage: ConversationMessage = {
                role: 'user',
                content: `【出示线索】${clueLabel}`,
                timestamp: new Date().toISOString(),
              }
              set((state) => ({
                conversationHistoryBySuspect: {
                  ...state.conversationHistoryBySuspect,
                  [suspectId]: [...(state.conversationHistoryBySuspect[suspectId] || []), confrontMessage],
                },
              }))

              const result = await gameApi.confrontWithClue(gameId, {
                suspectId,
                clueId,
                conversationHistory,
              })

              // 写入嫌疑人回应
              const suspectMsg: ConversationMessage = {
                role: 'suspect',
                content: result.response,
                timestamp: result.conversationMessage?.timestamp || new Date().toISOString(),
              }
              set((state) => ({
                conversationHistoryBySuspect: {
                  ...state.conversationHistoryBySuspect,
                  [suspectId]: [...(state.conversationHistoryBySuspect[suspectId] || []), suspectMsg],
                },
              }))

              // P3: 处理嫌疑人状态迁移
              const stateDelta = result.statusDelta
              if (stateDelta && stateDelta.from !== stateDelta.to) {
                const newState = stateDelta.to as 'calm' | 'pressured' | 'broken'
                set((state) => ({
                  suspectStates: {
                    ...state.suspectStates,
                    [suspectId]: newState,
                  },
                }))
                // 同步到 gameStore（服务端单源）
                useGameStore.getState().patchGameState({
                  suspectStates: {
                    ...useGameStore.getState().gameState?.suspectStates,
                    [suspectId]: newState,
                  },
                })
                console.info('[interrogationStore] 嫌疑人状态迁移', {
                  suspectId,
                  from: stateDelta.from,
                  to: stateDelta.to,
                })
              }

              // 同步线索验证状态到 cluesStore
              if (result.clueAfter) {
                const { useCluesStore } = await import('./cluesStore')
                useCluesStore.getState().addClueFromBackend(result.clueAfter)
              }

              console.info('[interrogationStore] 对质完成', { relevance: result.relevance, clueId, stateDelta })
              set({ confrontLoading: false })
              return result
            } catch (err) {
              console.error('[interrogationStore] 出示线索对质失败', err)
              set({ confrontLoading: false })
              return null
            }
          },

          // P6: Narrative Director
          setNarrativeBlock: (suspectId, block) => {
            set((state) => ({
              lastNarrativeBlock: block,
              suspectPressures: {
                ...state.suspectPressures,
                [suspectId]: block.pressure,
              },
              narrativeEvents: block.narrativeEvents || [],
              suspectStates: block.stateTransition
                ? {
                    ...state.suspectStates,
                    [suspectId]: block.stateTransition.to as 'calm' | 'pressured' | 'broken',
                  }
                : state.suspectStates,
            }))
            console.info('[interrogationStore] 叙事块更新', {
              suspectId,
              pressure: block.pressure,
              events: block.narrativeEvents.length,
              stateTransition: block.stateTransition,
            })
          },

          // Actions - 通用
          resetAll: () => {
            set({
              mode: 'private',
              selectedTab: 'suspects',
              conversationHistoryBySuspect: {},
              selectedSuspectId: null,
              selectedWitnessId: null,
              witnessConversationsByWitnessId: {},
              witnessCredibilityCheck: null,
              witnessWatsonTips: [],
              witnessWatsonTipsLoading: false,
              selectedExpertId: null,
              expertConversationsByExpertId: {},
              expertReportLoadedById: {},
              extractedActorClues: [],
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
              confrontLoading: false,
              suspectStates: {},
              suspectPressures: {},
              lastNarrativeBlock: null,
              narrativeEvents: [],
            })
            console.info('[interrogationStore] 重置所有状态')
          },
        }
      },
      {
        name: 'interrogation-store',
        storage: createJSONStorage(() => createGameScopedStorage('interrogation-store')),
        version: 1,
        migrate: (persistedState: any, version: number) => {
          if (version === 0) {
            // 旧存档补齐证人/专家相关字段默认值
            return {
              ...persistedState,
              selectedTab: 'suspects' as SelectedTab,
              selectedWitnessId: null,
              witnessConversationsByWitnessId: {},
              witnessCredibilityCheck: null,
              witnessWatsonTips: [],
              witnessWatsonTipsLoading: false,
              selectedExpertId: null,
              expertConversationsByExpertId: {},
              expertReportLoadedById: {},
              extractedActorClues: [],
            }
          }
          return persistedState
        },
        partialize: (state) => ({
          mode: state.mode,
          selectedTab: state.selectedTab,
          conversationHistoryBySuspect: state.conversationHistoryBySuspect,
          selectedSuspectId: state.selectedSuspectId,
          selectedWitnessId: state.selectedWitnessId,
          witnessConversationsByWitnessId: state.witnessConversationsByWitnessId,
          selectedExpertId: state.selectedExpertId,
          expertConversationsByExpertId: state.expertConversationsByExpertId,
          expertReportLoadedById: state.expertReportLoadedById,
          groupMessages: state.groupMessages,
          mentionedSuspects: state.mentionedSuspects,
          interjectionCounts: state.interjectionCounts,
          suspectStatements: state.suspectStatements,
          contradictions: state.contradictions,
          suspectStates: state.suspectStates,
        }),
      }
    ),
    { name: 'InterrogationStore' }
  )
)
