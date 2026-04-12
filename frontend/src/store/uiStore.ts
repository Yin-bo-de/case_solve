import { create } from 'zustand'
import type React from 'react'

console.debug('[uiStore.ts] 加载模块')

// UI 相关类型
export type ViewMode = 'investigation' | 'interrogation' | 'deduction' | 'conclusion'
export type InterrogationMode = 'private' | 'group'
export type SidebarTab = 'observations' | 'clues' | 'notes'

interface UIStore {
  // 全局 UI 状态
  viewMode: ViewMode
  isLoading: boolean
  showWatsonDialog: boolean
  isWatsonDialogExpanded: boolean

  // 勘查页面 UI
  selectedAreaId: string | null
  showAreaDetails: boolean
  investigationSidebarTab: SidebarTab

  // 审讯页面 UI
  interrogationMode: InterrogationMode
  selectedSuspectId: string | null
  showSuspectSelector: boolean

  // 推理板 UI
  showInferenceForm: boolean
  showHypothesisForm: boolean
  showWatsonFeedback: boolean

  // 模态框
  showModal: boolean
  modalContent: React.ReactNode | null

  // Actions - 全局
  setViewMode: (mode: ViewMode) => void
  setIsLoading: (isLoading: boolean) => void
  toggleWatsonDialog: () => void
  setWatsonDialogExpanded: (expanded: boolean) => void

  // Actions - 勘查页面
  setSelectedAreaId: (areaId: string | null) => void
  setShowAreaDetails: (show: boolean) => void
  setInvestigationSidebarTab: (tab: SidebarTab) => void

  // Actions - 审讯页面
  setInterrogationMode: (mode: InterrogationMode) => void
  setSelectedSuspectId: (suspectId: string | null) => void
  setShowSuspectSelector: (show: boolean) => void

  // Actions - 推理板
  setShowInferenceForm: (show: boolean) => void
  setShowHypothesisForm: (show: boolean) => void
  setShowWatsonFeedback: (show: boolean) => void

  // Actions - 模态框
  openModal: (content: React.ReactNode) => void
  closeModal: () => void

  // Reset
  resetUI: () => void
}

export const useUIStore = create<UIStore>((set) => {
  console.debug('[uiStore] 初始化 store')

  return {
    // 全局 UI 状态
    viewMode: 'investigation',
    isLoading: false,
    showWatsonDialog: true,
    isWatsonDialogExpanded: true,

    // 勘查页面 UI
    selectedAreaId: null,
    showAreaDetails: false,
    investigationSidebarTab: 'observations',

    // 审讯页面 UI
    interrogationMode: 'private',
    selectedSuspectId: null,
    showSuspectSelector: true,

    // 推理板 UI
    showInferenceForm: false,
    showHypothesisForm: false,
    showWatsonFeedback: false,

    // 模态框
    showModal: false,
    modalContent: null,

    // Actions - 全局
    setViewMode: (mode: ViewMode) => {
      console.debug('[uiStore] 设置视图模式', { mode })
      set({ viewMode: mode })
    },

    setIsLoading: (isLoading: boolean) => {
      console.debug('[uiStore] 设置加载状态', { isLoading })
      set({ isLoading })
    },

    toggleWatsonDialog: () => {
      console.debug('[uiStore] 切换华生对话框')
      set((state) => ({ showWatsonDialog: !state.showWatsonDialog }))
    },

    setWatsonDialogExpanded: (expanded: boolean) => {
      console.debug('[uiStore] 设置华生对话框展开状态', { expanded })
      set({ isWatsonDialogExpanded: expanded })
    },

    // Actions - 勘查页面
    setSelectedAreaId: (areaId: string | null) => {
      console.debug('[uiStore] 设置选中区域', { areaId })
      set({ selectedAreaId: areaId })
    },

    setShowAreaDetails: (show: boolean) => {
      console.debug('[uiStore] 设置显示区域详情', { show })
      set({ showAreaDetails: show })
    },

    setInvestigationSidebarTab: (tab: SidebarTab) => {
      console.debug('[uiStore] 设置勘查侧边栏标签', { tab })
      set({ investigationSidebarTab: tab })
    },

    // Actions - 审讯页面
    setInterrogationMode: (mode: InterrogationMode) => {
      console.debug('[uiStore] 设置审讯模式', { mode })
      set({ interrogationMode: mode })
    },

    setSelectedSuspectId: (suspectId: string | null) => {
      console.debug('[uiStore] 设置选中嫌疑人', { suspectId })
      set({ selectedSuspectId: suspectId })
    },

    setShowSuspectSelector: (show: boolean) => {
      console.debug('[uiStore] 设置显示嫌疑人选择器', { show })
      set({ showSuspectSelector: show })
    },

    // Actions - 推理板
    setShowInferenceForm: (show: boolean) => {
      console.debug('[uiStore] 设置显示推理表单', { show })
      set({ showInferenceForm: show })
    },

    setShowHypothesisForm: (show: boolean) => {
      console.debug('[uiStore] 设置显示假设表单', { show })
      set({ showHypothesisForm: show })
    },

    setShowWatsonFeedback: (show: boolean) => {
      console.debug('[uiStore] 设置显示华生反馈', { show })
      set({ showWatsonFeedback: show })
    },

    // Actions - 模态框
    openModal: (content: React.ReactNode) => {
      console.debug('[uiStore] 打开模态框')
      set({ showModal: true, modalContent: content })
    },

    closeModal: () => {
      console.debug('[uiStore] 关闭模态框')
      set({ showModal: false, modalContent: null })
    },

    // Reset
    resetUI: () => {
      console.info('[uiStore] 重置UI状态')
      set({
        viewMode: 'investigation',
        isLoading: false,
        showWatsonDialog: true,
        isWatsonDialogExpanded: true,
        selectedAreaId: null,
        showAreaDetails: false,
        investigationSidebarTab: 'observations',
        interrogationMode: 'private',
        selectedSuspectId: null,
        showSuspectSelector: true,
        showInferenceForm: false,
        showHypothesisForm: false,
        showWatsonFeedback: false,
        showModal: false,
        modalContent: null,
      })
    },
  }
})
