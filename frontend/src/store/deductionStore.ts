import { create } from 'zustand'
import type { DeductionChain, Inference, Hypothesis } from '@/types/game'

console.debug('[deductionStore.ts] 加载模块')

interface DeductionStore {
  // 状态
  deductionChain: DeductionChain | null
  selectedObservationIds: string[]
  selectedInferenceIds: string[]
  expandedHypothesisId: string | null

  // Actions
  setDeductionChain: (chain: DeductionChain) => void
  addInference: (inference: Inference) => void
  updateInference: (inferenceId: string, updates: Partial<Inference>) => void
  removeInference: (inferenceId: string) => void
  addHypothesis: (hypothesis: Hypothesis) => void
  updateHypothesis: (hypothesisId: string, updates: Partial<Hypothesis>) => void
  removeHypothesis: (hypothesisId: string) => void
  toggleObservationSelection: (observationId: string) => void
  clearObservationSelection: () => void
  toggleInferenceSelection: (inferenceId: string) => void
  clearInferenceSelection: () => void
  setExpandedHypothesis: (hypothesisId: string | null) => void
  setConclusion: (conclusion: string) => void
  setFinalAccusation: (suspectId: string) => void
  resetDeduction: () => void
}

export const useDeductionStore = create<DeductionStore>((set) => {
  console.debug('[deductionStore] 初始化 store')

  return {
    deductionChain: null,
    selectedObservationIds: [],
    selectedInferenceIds: [],
    expandedHypothesisId: null,

    setDeductionChain: (chain: DeductionChain) => {
      console.info('[deductionStore] 设置推理链条', { chainId: chain.id })
      set({ deductionChain: chain })
    },

    addInference: (inference: Inference) => {
      console.info('[deductionStore] 添加推理', { inferenceId: inference.id })
      set((state) => ({
        deductionChain: state.deductionChain
          ? {
              ...state.deductionChain,
              inferences: [...state.deductionChain.inferences, inference],
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    updateInference: (inferenceId: string, updates: Partial<Inference>) => {
      console.info('[deductionStore] 更新推理', { inferenceId, updates })
      set((state) => ({
        deductionChain: state.deductionChain
          ? {
              ...state.deductionChain,
              inferences: state.deductionChain.inferences.map((inf) =>
                inf.id === inferenceId ? { ...inf, ...updates } : inf
              ),
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    removeInference: (inferenceId: string) => {
      console.info('[deductionStore] 删除推理', { inferenceId })
      set((state) => ({
        deductionChain: state.deductionChain
          ? {
              ...state.deductionChain,
              inferences: state.deductionChain.inferences.filter((inf) => inf.id !== inferenceId),
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    addHypothesis: (hypothesis: Hypothesis) => {
      console.info('[deductionStore] 添加假设', { hypothesisId: hypothesis.id })
      set((state) => ({
        deductionChain: state.deductionChain
          ? {
              ...state.deductionChain,
              hypotheses: [...state.deductionChain.hypotheses, hypothesis],
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    updateHypothesis: (hypothesisId: string, updates: Partial<Hypothesis>) => {
      console.info('[deductionStore] 更新假设', { hypothesisId, updates })
      set((state) => ({
        deductionChain: state.deductionChain
          ? {
              ...state.deductionChain,
              hypotheses: state.deductionChain.hypotheses.map((hyp) =>
                hyp.id === hypothesisId ? { ...hyp, ...updates } : hyp
              ),
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    removeHypothesis: (hypothesisId: string) => {
      console.info('[deductionStore] 删除假设', { hypothesisId })
      set((state) => ({
        deductionChain: state.deductionChain
          ? {
              ...state.deductionChain,
              hypotheses: state.deductionChain.hypotheses.filter((hyp) => hyp.id !== hypothesisId),
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    toggleObservationSelection: (observationId: string) => {
      console.debug('[deductionStore] 切换观察选择', { observationId })
      set((state) => {
        const isSelected = state.selectedObservationIds.includes(observationId)
        return {
          selectedObservationIds: isSelected
            ? state.selectedObservationIds.filter((id) => id !== observationId)
            : [...state.selectedObservationIds, observationId],
        }
      })
    },

    clearObservationSelection: () => {
      console.debug('[deductionStore] 清除观察选择')
      set({ selectedObservationIds: [] })
    },

    toggleInferenceSelection: (inferenceId: string) => {
      console.debug('[deductionStore] 切换推理选择', { inferenceId })
      set((state) => {
        const isSelected = state.selectedInferenceIds.includes(inferenceId)
        return {
          selectedInferenceIds: isSelected
            ? state.selectedInferenceIds.filter((id) => id !== inferenceId)
            : [...state.selectedInferenceIds, inferenceId],
        }
      })
    },

    clearInferenceSelection: () => {
      console.debug('[deductionStore] 清除推理选择')
      set({ selectedInferenceIds: [] })
    },

    setExpandedHypothesis: (hypothesisId: string | null) => {
      console.debug('[deductionStore] 设置展开的假设', { hypothesisId })
      set({ expandedHypothesisId: hypothesisId })
    },

    setConclusion: (conclusion: string) => {
      console.info('[deductionStore] 设置结论', { conclusion })
      set((state) => ({
        deductionChain: state.deductionChain
          ? {
              ...state.deductionChain,
              conclusion,
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    setFinalAccusation: (suspectId: string) => {
      console.info('[deductionStore] 设置最终指认', { suspectId })
      set((state) => ({
        deductionChain: state.deductionChain
          ? {
              ...state.deductionChain,
              finalAccusation: suspectId,
              updatedAt: new Date().toISOString(),
            }
          : null,
      }))
    },

    resetDeduction: () => {
      console.info('[deductionStore] 重置推理链条')
      set({
        deductionChain: null,
        selectedObservationIds: [],
        selectedInferenceIds: [],
        expandedHypothesisId: null,
      })
    },
  }
})
