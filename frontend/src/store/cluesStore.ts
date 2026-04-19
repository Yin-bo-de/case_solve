import { create } from 'zustand'
import { devtools, persist, createJSONStorage } from 'zustand/middleware'
import type { Clue, Observation } from '@/types/game'
import { createGameScopedStorage } from './gameScopedStorage'

console.debug('[cluesStore.ts] 加载模块')

interface CluesStore {
  // 状态
  clues: Clue[]
  observations: Observation[]
  selectedClueIds: string[]

  // Actions
  setClues: (clues: Clue[]) => void
  setObservations: (observations: Observation[]) => void
  addObservation: (observation: Observation) => void
  removeObservation: (observationId: string) => void
  toggleClueSelection: (clueId: string) => void
  clearClueSelection: () => void
  markClueDiscovered: (clueId: string, notes?: string) => void
  /** 从后端返回的线索数据添加或更新（用于场景发现、审讯提取） */
  addClueFromBackend: (clue: Clue) => void
  /** 合并后端返回的线索列表：已有 id 保留本地版本，新 id 追加 */
  mergeClues: (incoming: Clue[]) => void
  resetClues: () => void
}

export const useCluesStore = create<CluesStore>()(
  devtools(
    persist(
      (set) => ({
        clues: [],
        observations: [],
        selectedClueIds: [],

        setClues: (clues: Clue[]) => {
          console.info('[cluesStore] 设置线索列表', { count: clues.length })
          set({ clues })
        },

        setObservations: (observations: Observation[]) => {
          console.info('[cluesStore] 设置观察记录列表', { count: observations.length })
          set({ observations })
        },

        addObservation: (observation: Observation) => {
          console.info('[cluesStore] 添加观察记录', { observationId: observation.id })
          set((state) => ({
            observations: [...state.observations, observation],
          }))
        },

        removeObservation: (observationId: string) => {
          console.info('[cluesStore] 删除观察记录', { observationId })
          set((state) => ({
            observations: state.observations.filter((o) => o.id !== observationId),
          }))
        },

        toggleClueSelection: (clueId: string) => {
          console.debug('[cluesStore] 切换线索选择', { clueId })
          set((state) => {
            const isSelected = state.selectedClueIds.includes(clueId)
            return {
              selectedClueIds: isSelected
                ? state.selectedClueIds.filter((id) => id !== clueId)
                : [...state.selectedClueIds, clueId],
            }
          })
        },

        clearClueSelection: () => {
          console.debug('[cluesStore] 清除线索选择')
          set({ selectedClueIds: [] })
        },

        markClueDiscovered: (clueId: string, notes?: string) => {
          console.info('[cluesStore] 标记线索为已发现', { clueId, notes })
          set((state) => ({
            clues: state.clues.map((clue) =>
              clue.id === clueId
                ? { ...clue, discovered: true, discoveryNotes: notes }
                : clue
            ),
          }))
        },

        addClueFromBackend: (clue: Clue) => {
          console.info('[cluesStore] 从后端添加线索', { clueId: clue.id, userLabel: clue.userLabel })
          set((state) => {
            const existing = state.clues.find((c) => c.id === clue.id)
            if (existing) {
              // 已有线索则更新（标记 discovered、补充 userLabel）
              return {
                clues: state.clues.map((c) => (c.id === clue.id ? { ...c, ...clue } : c)),
              }
            }
            return { clues: [...state.clues, clue] }
          })
        },

        mergeClues: (incoming: Clue[]) => {
          if (!incoming || incoming.length === 0) return
          set((state) => {
            const existingIds = new Set(state.clues.map((c) => c.id))
            const toAdd = incoming.filter((c) => !existingIds.has(c.id))
            if (toAdd.length === 0) return state
            console.info('[cluesStore] 合并后端线索', { incoming: incoming.length, added: toAdd.length })
            return { clues: [...state.clues, ...toAdd] }
          })
        },

        resetClues: () => {
          console.info('[cluesStore] 重置线索')
          set({
            clues: [],
            observations: [],
            selectedClueIds: [],
          })
        },
      }),
      {
        name: 'clues-store',
        storage: createJSONStorage(() => createGameScopedStorage('clues-store')),
        partialize: (state) => ({
          clues: state.clues,
          observations: state.observations,
        }),
      }
    ),
    { name: 'CluesStore' }
  )
)
