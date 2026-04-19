import { useEffect, useRef } from 'react'
import { gameApi } from '@/services/api'
import { useGameStore } from '@/store/gameStore'
import { StoreManager } from '@/store/storeManager'

console.debug('[useGameSessionSync.ts] 加载模块')

/**
 * 页面级数据同步 Hook。
 * - gameId 与 activeGameId 不一致：清内存 → 后端拉取 → rehydrate 新命名空间
 * - 一致：后台 revalidate（stale-while-revalidate）
 * - 同组件实例内同 gameId 不重复触发
 */
export function useGameSessionSync(gameId: string | undefined) {
  const setGameState = useGameStore((s) => s.setGameState)
  const setLoading = useGameStore((s) => s.setLoading)
  const setError = useGameStore((s) => s.setError)
  const currentGameId = useGameStore((s) => s.gameState?.gameId)
  const loadedRef = useRef<string | null>(null)

  useEffect(() => {
    if (!gameId) return
    if (loadedRef.current === gameId) return

    const needsFullReload = currentGameId !== gameId

    const run = async () => {
      try {
        setLoading(true)
        if (needsFullReload) {
          console.info('[useGameSessionSync] gameId 变更，执行全量同步', { from: currentGameId, to: gameId })
          StoreManager.clearInMemoryGameScopedStores()
          const state = await gameApi.getGameState(gameId)
          setGameState(state)
          await StoreManager.rehydrateGameScopedStores()
        } else {
          console.debug('[useGameSessionSync] revalidate', { gameId })
          const state = await gameApi.getGameState(gameId)
          setGameState(state)
        }
        loadedRef.current = gameId
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : '加载失败'
        console.error('[useGameSessionSync] 加载失败', e)
        setError(message)
      } finally {
        setLoading(false)
      }
    }
    run()
  }, [gameId, currentGameId, setGameState, setLoading, setError])
}
