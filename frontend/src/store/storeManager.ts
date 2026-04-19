import { useGameStore, useCluesStore, useDeductionStore, useWatsonChatStore, useUIStore, useInterrogationStore, useSceneChatStore } from './index'
import { GAME_SCOPED_STORAGE_PREFIX } from './gameScopedStorage'

console.debug('[storeManager.ts] 加载模块')

/**
 * 游戏状态快照
 */
export interface GameSnapshot {
  game: ReturnType<typeof useGameStore.getState>
  clues: ReturnType<typeof useCluesStore.getState>
  deduction: ReturnType<typeof useDeductionStore.getState>
  watsonChat: ReturnType<typeof useWatsonChatStore.getState>
  ui: ReturnType<typeof useUIStore.getState>
}

/**
 * 统一状态管理器
 * 提供全局重置、快照保存/恢复等功能
 */
export class StoreManager {
  /**
   * 重置所有 Store 状态
   * @param options 重置选项
   */
  static resetAll(options?: {
    keepGameState?: boolean
    keepWatsonChat?: boolean
    keepDialogPosition?: boolean
  }) {
    console.info('[StoreManager] 重置所有状态', options)

    const { keepGameState, keepWatsonChat, keepDialogPosition } = options || {}

    // 重置游戏状态
    if (!keepGameState) {
      useGameStore.getState().resetGame()
    }

    // 重置线索状态
    useCluesStore.getState().resetClues()

    // 重置推理状态
    useDeductionStore.getState().resetDeduction()

    // 重置审讯状态
    useInterrogationStore.getState().resetAll()

    // 重置场景聊天
    useSceneChatStore.getState().resetAll()

    // 重置华生聊天
    if (!keepWatsonChat) {
      useWatsonChatStore.getState().clearMessages()
    }

    // 重置 UI 状态
    const currentState = useUIStore.getState()
    useUIStore.getState().resetUI()

    // 恢复对话框位置（如果需要保留）
    if (keepDialogPosition && currentState) {
      useUIStore.getState().setWatsonDialogPosition(currentState.watsonDialogPosition)
    }
  }

  /**
   * 创建当前状态快照
   * @param options 快照选项
   */
  static createSnapshot(options?: {
    includeWatsonChat?: boolean
    includeUI?: boolean
  }): Partial<GameSnapshot> {
    const { includeWatsonChat = true, includeUI = false } = options || {}

    const snapshot: Partial<GameSnapshot> = {
      game: useGameStore.getState(),
      clues: useCluesStore.getState(),
      deduction: useDeductionStore.getState(),
    }

    if (includeWatsonChat) {
      snapshot.watsonChat = useWatsonChatStore.getState()
    }

    if (includeUI) {
      snapshot.ui = useUIStore.getState()
    }

    console.info('[StoreManager] 创建状态快照', {
      keys: Object.keys(snapshot),
    })

    return snapshot
  }

  /**
   * 恢复状态快照
   * @param snapshot 状态快照
   */
  static restoreSnapshot(snapshot: Partial<GameSnapshot>) {
    console.info('[StoreManager] 恢复状态快照', {
      keys: Object.keys(snapshot),
    })

    if (snapshot.game) {
      useGameStore.setState(snapshot.game)
    }

    if (snapshot.clues) {
      useCluesStore.setState(snapshot.clues)
    }

    if (snapshot.deduction) {
      useDeductionStore.setState(snapshot.deduction)
    }

    if (snapshot.watsonChat) {
      useWatsonChatStore.setState(snapshot.watsonChat)
    }

    if (snapshot.ui) {
      useUIStore.setState(snapshot.ui)
    }
  }

  /**
   * 保存快照到 localStorage
   * @param key 存储键
   */
  static saveSnapshotToStorage(key: string, options?: {
    includeWatsonChat?: boolean
    includeUI?: boolean
  }): boolean {
    try {
      const snapshot = this.createSnapshot(options)
      localStorage.setItem(key, JSON.stringify(snapshot))
      console.info('[StoreManager] 快照已保存到 localStorage', { key })
      return true
    } catch (error) {
      console.error('[StoreManager] 保存快照失败', error)
      return false
    }
  }

  /**
   * 从 localStorage 加载快照
   * @param key 存储键
   */
  static loadSnapshotFromStorage(key: string): Partial<GameSnapshot> | null {
    try {
      const data = localStorage.getItem(key)
      if (!data) {
        console.debug('[StoreManager] localStorage 中未找到快照', { key })
        return null
      }

      const snapshot: Partial<GameSnapshot> = JSON.parse(data)
      console.info('[StoreManager] 从 localStorage 加载快照', { key })
      return snapshot
    } catch (error) {
      console.error('[StoreManager] 加载快照失败', error)
      return null
    }
  }

  /**
   * 删除 localStorage 中的快照
   * @param key 存储键
   */
  static deleteSnapshotFromStorage(key: string): boolean {
    try {
      localStorage.removeItem(key)
      console.info('[StoreManager] 已删除 localStorage 中的快照', { key })
      return true
    } catch (error) {
      console.error('[StoreManager] 删除快照失败', error)
      return false
    }
  }

  /**
   * 获取所有 localStorage 中的快照键
   */
  static listSnapshots(): string[] {
    const snapshots: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith('game-snapshot-')) {
        snapshots.push(key)
      }
    }
    return snapshots.sort()
  }

  /**
   * 删除所有 game:* 前缀的 localStorage 条目
   * @param exceptGameId 可选，保留该 gameId 的所有 key
   */
  static clearAllGameSessions(exceptGameId?: string): void {
    const toDelete: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (!key?.startsWith(GAME_SCOPED_STORAGE_PREFIX)) continue
      if (exceptGameId && key.startsWith(`${GAME_SCOPED_STORAGE_PREFIX}${exceptGameId}:`)) continue
      toDelete.push(key)
    }
    toDelete.forEach((k) => localStorage.removeItem(k))
    console.info('[StoreManager] clearAllGameSessions', {
      removed: toDelete.length,
      except: exceptGameId,
    })
  }

  /**
   * 清空所有接入 gameScopedStorage 的内存态
   */
  static clearInMemoryGameScopedStores(): void {
    console.info('[StoreManager] clearInMemoryGameScopedStores')
    useCluesStore.getState().resetClues()
    useDeductionStore.getState().resetDeduction()
    useInterrogationStore.getState().resetAll()
    useWatsonChatStore.getState().clearMessages()
    useSceneChatStore.getState().resetAll()
  }

  /**
   * 触发所有接入 gameScopedStorage 的 store 从当前 activeGameId 命名空间重新 hydrate
   */
  static async rehydrateGameScopedStores(): Promise<void> {
    console.info('[StoreManager] rehydrateGameScopedStores')
    await Promise.all([
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (useCluesStore as any).persist?.rehydrate?.(),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (useDeductionStore as any).persist?.rehydrate?.(),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (useInterrogationStore as any).persist?.rehydrate?.(),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (useWatsonChatStore as any).persist?.rehydrate?.(),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (useSceneChatStore as any).persist?.rehydrate?.(),
    ])
  }

  /**
   * 调试：打印当前所有状态
   */
  static debugPrintAll() {
    console.group('[StoreManager] 当前状态')
    console.log('Game:', useGameStore.getState())
    console.log('Clues:', useCluesStore.getState())
    console.log('Deduction:', useDeductionStore.getState())
    console.log('WatsonChat:', useWatsonChatStore.getState())
    console.log('UI:', useUIStore.getState())
    console.groupEnd()
  }
}

/**
 * Hook 形式的状态管理器
 */
export function useStoreManager() {
  return {
    resetAll: StoreManager.resetAll,
    createSnapshot: StoreManager.createSnapshot,
    restoreSnapshot: StoreManager.restoreSnapshot,
    saveSnapshotToStorage: StoreManager.saveSnapshotToStorage,
    loadSnapshotFromStorage: StoreManager.loadSnapshotFromStorage,
    deleteSnapshotFromStorage: StoreManager.deleteSnapshotFromStorage,
    listSnapshots: StoreManager.listSnapshots,
    debugPrintAll: StoreManager.debugPrintAll,
    clearAllGameSessions: StoreManager.clearAllGameSessions,
    clearInMemoryGameScopedStores: StoreManager.clearInMemoryGameScopedStores,
    rehydrateGameScopedStores: StoreManager.rehydrateGameScopedStores,
  }
}
