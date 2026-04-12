import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { GameDifficulty, GameState } from '@/types/game'
import { gameApi } from '@/services/api'

const DIFFICULTY_LABELS: Record<GameDifficulty, string> = {
  easy: '简单',
  classic: '经典',
  hardcore: '硬核',
}

const DIFFICULTY_DESCRIPTIONS: Record<GameDifficulty, string> = {
  easy: '线索明显，华生主动提示，适合初次体验',
  classic: '难度适中，平衡挑战与体验',
  hardcore: '线索隐蔽，华生少言，适合推理高手',
}

export default function StartPage() {
  const navigate = useNavigate()
  const [selectedDifficulty, setSelectedDifficulty] = useState<GameDifficulty>('classic')
  const [isLoading, setIsLoading] = useState(false)
  const [gameState, setGameState] = useState<GameState | null>(null)
  const [error, setError] = useState<string | null>(null)

  console.debug('[StartPage] 渲染起始页面', { selectedDifficulty, isLoading })

  const handleStartGame = async () => {
    console.info('[StartPage] 开始新游戏', { difficulty: selectedDifficulty })
    setIsLoading(true)
    setError(null)

    try {
      // 创建新游戏
      const state = await gameApi.createNewGame(selectedDifficulty)
      console.info('[StartPage] 游戏创建成功', state)
      setGameState(state)

      // 短暂显示案件信息后跳转到勘查页面
      setTimeout(() => {
        console.info('[StartPage] 跳转到勘查页面', { gameId: state.gameId })
        navigate(`/investigation/${state.gameId}`)
      }, 3000)
    } catch (err) {
      console.error('[StartPage] 创建游戏失败', err)
      setError(err instanceof Error ? err.message : '创建游戏失败，请稍后重试')
    } finally {
      setIsLoading(false)
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
    </div>
  )
}
