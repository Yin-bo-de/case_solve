import { create } from 'zustand'
import { devtools, persist, createJSONStorage } from 'zustand/middleware'
import type { Clue, Observation } from '@/types/game'

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
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          clues: state.clues,
          observations: state.observations,
        }),
      }
    ),
    { name: 'CluesStore' }
  )
)
