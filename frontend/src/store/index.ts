// 重新导出所有 store
export { useGameStore } from './gameStore'
export { useCluesStore } from './cluesStore'
export { useDeductionStore } from './deductionStore'
export { useUIStore } from './uiStore'
export { useWatsonChatStore } from './watsonChatStore'
export { useInterrogationStore } from './interrogationStore'

// 导出类型
export type {
  InterrogationMode,
  GroupMessage,
  MentionedSuspect,
} from './interrogationStore'

// 导出状态管理器
export { StoreManager, useStoreManager } from './storeManager'
export type { GameSnapshot } from './storeManager'
