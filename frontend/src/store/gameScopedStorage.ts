import type { StateStorage } from 'zustand/middleware'
import { useGameStore } from './gameStore'

console.debug('[gameScopedStorage.ts] 加载模块')

export const GAME_SCOPED_STORAGE_PREFIX = 'game:'

/**
 * 返回 Zustand 兼容的 StateStorage，
 * 实际 localStorage key 命名空间化为 `game:${activeGameId}:${storeName}`。
 * 无 activeGameId 时读写均 no-op，避免产生无主数据。
 */
export function createGameScopedStorage(storeName: string): StateStorage {
  const buildKey = (): string | null => {
    const gameId = useGameStore.getState().gameState?.gameId
    if (!gameId) return null
    return `${GAME_SCOPED_STORAGE_PREFIX}${gameId}:${storeName}`
  }

  return {
    getItem: (_key: string) => {
      const full = buildKey()
      if (!full) {
        console.debug(`[gameScopedStorage:${storeName}] getItem 跳过：无 activeGameId`)
        return null
      }
      return localStorage.getItem(full)
    },
    setItem: (_key: string, value: string) => {
      const full = buildKey()
      if (!full) {
        console.warn(`[gameScopedStorage:${storeName}] setItem 跳过：无 activeGameId`)
        return
      }
      localStorage.setItem(full, value)
    },
    removeItem: (_key: string) => {
      const full = buildKey()
      if (!full) return
      localStorage.removeItem(full)
    },
  }
}
