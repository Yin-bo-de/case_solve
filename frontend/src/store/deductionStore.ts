import { create } from 'zustand'
import { devtools, persist, createJSONStorage } from 'zustand/middleware'
import type { DeductionChain, Inference, Hypothesis, ReasoningRecord } from '@/types/game'
import { gameApi } from '@/services/api'

console.debug('[deductionStore.ts] 加载模块')

interface DeductionStore {
  // 旧推理链（保留，供旧版兼容读取）
  deductionChain: DeductionChain | null

  // 新：推理记录列表（经 Oracle 验证的 Inference）
  reasoningRecords: ReasoningRecord[]

  // 新：线索选择（供推理板使用）
  selectedClueIds: string[]

  // 新：过滤器
  filter: 'all' | 'correct' | 'wrong'

  // 旧兼容：推理/假设选择
  selectedObservationIds: string[]
  selectedInferenceIds: string[]
  expandedHypothesisId: string | null

  // Actions - 推理链（旧版兼容）
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

  // Actions - 新推理记录
  /** 提交组合推理，经 OracleAgent 验证后存入 reasoningRecords */
  submitReasoning: (gameId: string, clueIds: string[], conclusion: string) => Promise<ReasoningRecord>
  toggleClue: (id: string) => void
  setFilter: (f: 'all' | 'correct' | 'wrong') => void
  markImportant: (recordId: string) => void
  deleteRecord: (gameId: string, recordId: string) => Promise<void>
  /** 指认凶手，需提供 1-3 条推理记录 id */
  accuse: (gameId: string, suspectId: string, recordIds: string[]) => Promise<any>

  resetDeduction: () => void
}

export const useDeductionStore = create<DeductionStore>()(
  devtools(
    persist(
      (set) => ({
        deductionChain: null,
        reasoningRecords: [],
        selectedClueIds: [],
        filter: 'all',
        selectedObservationIds: [],
        selectedInferenceIds: [],
        expandedHypothesisId: null,

        // ── 旧版兼容方法 ──────────────────────────────────────────────

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
          console.info('[deductionStore] 更新推理', { inferenceId })
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
          console.info('[deductionStore] 更新假设', { hypothesisId })
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
          set((state) => {
            const isSelected = state.selectedObservationIds.includes(observationId)
            return {
              selectedObservationIds: isSelected
                ? state.selectedObservationIds.filter((id) => id !== observationId)
                : [...state.selectedObservationIds, observationId],
            }
          })
        },

        clearObservationSelection: () => set({ selectedObservationIds: [] }),

        toggleInferenceSelection: (inferenceId: string) => {
          set((state) => {
            const isSelected = state.selectedInferenceIds.includes(inferenceId)
            return {
              selectedInferenceIds: isSelected
                ? state.selectedInferenceIds.filter((id) => id !== inferenceId)
                : [...state.selectedInferenceIds, inferenceId],
            }
          })
        },

        clearInferenceSelection: () => set({ selectedInferenceIds: [] }),

        setExpandedHypothesis: (hypothesisId: string | null) => {
          set({ expandedHypothesisId: hypothesisId })
        },

        setConclusion: (conclusion: string) => {
          set((state) => ({
            deductionChain: state.deductionChain
              ? { ...state.deductionChain, conclusion, updatedAt: new Date().toISOString() }
              : null,
          }))
        },

        setFinalAccusation: (suspectId: string) => {
          set((state) => ({
            deductionChain: state.deductionChain
              ? { ...state.deductionChain, finalAccusation: suspectId, updatedAt: new Date().toISOString() }
              : null,
          }))
        },

        // ── 新推理记录方法 ────────────────────────────────────────────

        submitReasoning: async (gameId: string, clueIds: string[], conclusion: string) => {
          console.info('[deductionStore] 提交推理', { gameId, clueIds, conclusion: conclusion.substring(0, 40) })
          const result = await gameApi.submitReasoning(gameId, clueIds, conclusion)
          const record: ReasoningRecord = {
            id: result.inference.id,
            content: result.inference.content,
            clueIds: result.inference.clueIds ?? clueIds,
            verificationResult: result.verificationResult,
            oracleExplanation: result.explanation,
            confidence: result.score,
            createdAt: result.inference.createdAt,
            userMarkedImportant: false,
          }
          set((state) => ({
            reasoningRecords: [...state.reasoningRecords, record],
            selectedClueIds: [],
          }))
          console.info('[deductionStore] 推理记录已添加', { recordId: record.id, verdict: record.verificationResult })
          return record
        },

        toggleClue: (id: string) => {
          console.debug('[deductionStore] 切换线索选择', { id })
          set((state) => {
            const selected = state.selectedClueIds.includes(id)
            return {
              selectedClueIds: selected
                ? state.selectedClueIds.filter((c) => c !== id)
                : [...state.selectedClueIds, id],
            }
          })
        },

        setFilter: (f: 'all' | 'correct' | 'wrong') => {
          console.info('[deductionStore] 设置过滤器', { filter: f })
          set({ filter: f })
        },

        markImportant: (recordId: string) => {
          console.info('[deductionStore] 标记重要', { recordId })
          set((state) => ({
            reasoningRecords: state.reasoningRecords.map((r) =>
              r.id === recordId ? { ...r, userMarkedImportant: !r.userMarkedImportant } : r
            ),
          }))
        },

        deleteRecord: async (gameId: string, recordId: string) => {
          console.info('[deductionStore] 删除推理记录', { gameId, recordId })
          await gameApi.deleteInference(gameId, recordId)
          set((state) => ({
            reasoningRecords: state.reasoningRecords.filter((r) => r.id !== recordId),
          }))
          console.info('[deductionStore] 推理记录已删除', { recordId })
        },

        accuse: async (gameId: string, suspectId: string, recordIds: string[]) => {
          console.info('[deductionStore] 指认凶手', { gameId, suspectId, recordIds })
          const result = await gameApi.makeAccusation(gameId, suspectId, recordIds)
          console.info('[deductionStore] 指认结果', { isCorrect: (result as any).isCorrect })
          return result
        },

        resetDeduction: () => {
          console.info('[deductionStore] 重置推理')
          set({
            deductionChain: null,
            reasoningRecords: [],
            selectedClueIds: [],
            filter: 'all',
            selectedObservationIds: [],
            selectedInferenceIds: [],
            expandedHypothesisId: null,
          })
        },
      }),
      {
        name: 'deduction-store',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          deductionChain: state.deductionChain,
          reasoningRecords: state.reasoningRecords,
        }),
      }
    ),
    { name: 'DeductionStore' }
  )
)
