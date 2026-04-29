import { create } from 'zustand'
import { devtools, persist, createJSONStorage } from 'zustand/middleware'
import type React from 'react'

console.debug('[uiStore.ts] 加载模块')

// UI 相关类型
export type ViewMode = 'investigation' | 'interrogation' | 'deduction' | 'conclusion'
export type InterrogationMode = 'private' | 'group'
export type SidebarTab = 'observations' | 'clues' | 'notes'

// 华生对话框位置
export interface DialogPosition {
  x: number
  y: number
}

interface UIStore {
  // 全局 UI 状态
  viewMode: ViewMode
  isLoading: boolean

  // 背景音乐（进入 investigation 页面后全程保持）
  musicStarted: boolean
  musicPlaying: boolean
  startMusic: () => void
  setMusicPlaying: (playing: boolean) => void

  // 华生对话框（统一管理）
  watsonDialogOpen: boolean
  watsonDialogExpanded: boolean
  watsonDialogPosition: DialogPosition

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

  // Actions - 华生对话框
  setWatsonDialogOpen: (isOpen: boolean) => void
  toggleWatsonDialog: () => void
  setWatsonDialogExpanded: (expanded: boolean) => void
  setWatsonDialogPosition: (position: DialogPosition) => void

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

export const useUIStore = create<UIStore>()(
  devtools(
    persist(
      (set) => ({
        // 全局 UI 状态
        viewMode: 'investigation',
        isLoading: false,

        // 背景音乐
        musicStarted: false,
        musicPlaying: false,
        startMusic: () => {
          console.info('[uiStore] 触发背景音乐启动')
          set({ musicStarted: true, musicPlaying: true })
        },
        setMusicPlaying: (playing: boolean) => {
          console.info('[uiStore] 设置背景音乐播放状态', { playing })
          set({ musicPlaying: playing })
        },

        // 华生对话框
        watsonDialogOpen: true,
        watsonDialogExpanded: true,
        watsonDialogPosition: { x: 0, y: 0 },

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

        // Actions - 华生对话框
        setWatsonDialogOpen: (isOpen: boolean) => {
          console.info('[uiStore] 设置华生对话框开关', { isOpen })
          set({ watsonDialogOpen: isOpen })
        },

        toggleWatsonDialog: () => {
          console.debug('[uiStore] 切换华生对话框')
          set((state) => ({ watsonDialogOpen: !state.watsonDialogOpen }))
        },

        setWatsonDialogExpanded: (expanded: boolean) => {
          console.debug('[uiStore] 设置华生对话框展开状态', { expanded })
          set({ watsonDialogExpanded: expanded })
        },

        setWatsonDialogPosition: (position: DialogPosition) => {
          console.debug('[uiStore] 设置华生对话框位置', position)
          set({ watsonDialogPosition: position })
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
            watsonDialogOpen: true,
            watsonDialogExpanded: true,
            watsonDialogPosition: { x: 0, y: 0 },
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
      }),
      {
        name: 'ui-store',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          viewMode: state.viewMode,
          watsonDialogPosition: state.watsonDialogPosition,
        }),
      }
    ),
    { name: 'UIStore' }
  )
)
