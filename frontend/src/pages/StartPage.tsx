import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import type { GameDifficulty } from '@/types/game'
import { gameApi } from '@/services/api'
import { useGameStore } from '@/store'
import WatsonChatDialog from '@/components/WatsonChatDialog'

const DIFFICULTY_LABELS: Record<GameDifficulty, string> = {
  easy: '简单',
  classic: '经典',
  hardcore: '硬核',
}

const DIFFICULTY_DESCRIPTIONS: Record<GameDifficulty, string> = {
  easy: '线索明显，华生主动提示，适合初次体验',
  classic: '难度适中，平衡挑战与体验',
  hardcore: '线索隐蔽，华生几乎沉默，适合推理高手',
}

const DIFFICULTY_STATS: Record<GameDifficulty, { clues: string; watson: string; mistakes: string }> = {
  easy:     { clues: '线索明显度 70%', watson: '华生活跃度 80%', mistakes: '错误机会 3 次' },
  classic:  { clues: '线索明显度 50%', watson: '华生活跃度 50%', mistakes: '错误机会 2 次' },
  hardcore: { clues: '线索明显度 30%', watson: '华生活跃度 20%', mistakes: '错误机会 1 次' },
}

export default function StartPage() {
  const navigate = useNavigate()
  const [selectedDifficulty, setSelectedDifficulty] = useState<GameDifficulty>('classic')
  const {
    gameState,
    isLoading,
    error,
    setGameState,
    setLoading,
    setError,
    resetGame
  } = useGameStore()

  console.debug('[StartPage] 渲染起始页面', { selectedDifficulty, isLoading })

  // 组件挂载时重置游戏状态
  useEffect(() => {
    console.debug('[StartPage] 组件挂载，重置游戏状态')
    resetGame()
  }, [resetGame])

  const handleStartGame = async () => {
    console.info('[StartPage] 开始新游戏', { difficulty: selectedDifficulty })
    setLoading(true)
    setError(null)

    try {
      // 创建新游戏
      const state = await gameApi.createNewGame(selectedDifficulty)
      console.info('[StartPage] 游戏创建成功', state)

      // 保存到全局 store
      setGameState(state)

      // 获取有效的 gameId（支持两种命名格式）
      const gameId = (state as any).gameId || (state as any).game_id
      if (!gameId) {
        throw new Error('游戏创建成功但 ID 缺失')
      }

      // 短暂显示案件信息后跳转到勘查页面
      setTimeout(() => {
        console.info('[StartPage] 跳转到勘查页面', { gameId })
        navigate(`/investigation/${gameId}`)
      }, 3000)
    } catch (err) {
      console.error('[StartPage] 创建游戏失败', err)
      setError(err instanceof Error ? err.message : '创建游戏失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="start-page">
      <div className="start-page__content">
        <h1 className="start-page__title">贝克街221B</h1>
        <p className="start-page__subtitle">
          伦敦，1895年。迷雾笼罩的城市中，一桩谋杀案 awaits...
        </p>

        {error && (
          <div className="start-page__error">
            <p>{error}</p>
          </div>
        )}

        {gameState ? (
          <div className="start-page__case-preview">
            <h2>案件加载中...</h2>
            {gameState.case && (
              <>
                <p className="case-preview__location">{gameState.case.location}</p>
                <p className="case-preview__victim">死者: {gameState.case.victimName}</p>
                <p className="case-preview__summary">{gameState.case.summary}</p>
              </>
            )}
          </div>
        ) : (
          <>
            <div className="start-page__difficulty">
              <h3>选择难度</h3>
              <div className="difficulty-options">
                {(Object.keys(DIFFICULTY_LABELS) as GameDifficulty[]).map((difficulty) => (
                  <button
                    key={difficulty}
                    className={`difficulty-option ${
                      selectedDifficulty === difficulty ? 'difficulty-option--selected' : ''
                    }`}
                    onClick={() => {
                      console.debug('[StartPage] 选择难度', difficulty)
                      setSelectedDifficulty(difficulty)
                    }}
                    type="button"
                  >
                    <span className="difficulty-option__label">
                      {DIFFICULTY_LABELS[difficulty]}
                    </span>
                    <span className="difficulty-option__description">
                      {DIFFICULTY_DESCRIPTIONS[difficulty]}
                    </span>
                    <span className="difficulty-option__stats">
                      {Object.values(DIFFICULTY_STATS[difficulty]).map((stat) => (
                        <span key={stat} className="difficulty-option__stat-tag">{stat}</span>
                      ))}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <button
              className="start-page__start-button"
              onClick={handleStartGame}
              disabled={isLoading}
              type="button"
            >
              {isLoading ? '准备中...' : '开始新案件'}
            </button>
          </>
        )}
      </div>

      {/* 华生对话框 */}
      {gameState && (
        <WatsonChatDialog gameId={gameState.gameId} />
      )}
    </div>
  )
}
