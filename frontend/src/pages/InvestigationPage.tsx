import { useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useGameStore, useCluesStore, useUIStore } from '@/store'
import WatsonChatDialog from '@/components/WatsonChatDialog'
import type { Scene } from '@/types/game'
import { useGameSessionSync } from '@/hooks/useGameSessionSync'

console.debug('[InvestigationPage.tsx] 加载模块')

export default function InvestigationPage() {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()

  const { gameState, isLoading, error } = useGameStore()
  const { clues } = useCluesStore()
  const { startMusic } = useUIStore()

  console.debug('[InvestigationPage] 渲染', { gameId })

  // 首次进入 investigation 页面时触发全局背景音乐
  useEffect(() => {
    startMusic()
  }, [startMusic])

  useGameSessionSync(gameId)

  if (isLoading) {
    return (
      <div className="investigation-page investigation-page--loading">
        <div className="loading-spinner">
          <p>正奔赴案发现场...</p>
        </div>
      </div>
    )
  }

  if (error || !gameState) {
    return (
      <div className="investigation-page investigation-page--error">
        <div className="error-message">
          <h2>出了岔子</h2>
          <p>{error || '无法调取档案'}</p>
          <button onClick={() => navigate('/')} type="button">
            返回贝克街
          </button>
        </div>
      </div>
    )
  }

  const scenes: Scene[] = gameState.case?.scenes ?? []

  // 统计每个场景已添加的线索数
  const clueCountByScene = (sceneId: string) =>
    clues.filter((c) => c.sourceType === 'scene' && c.sourceRef === sceneId).length

  return (
    <div className="investigation-page">
      {/* 顶部导航栏 */}
      <header className="investigation-header">
        <div className="header-content">
          <h1 className="header-title">现场勘查</h1>
          <div className="header-info">
            <span className="case-location">{gameState.case?.location}</span>
            <span className="observation-count">已添加线索: {clues.length}</span>
          </div>
        </div>
      </header>

      <main className="investigation-main">
        {/* 案件简述 */}
        <div className="case-summary-banner">
          <p>{gameState.case?.summary}</p>
        </div>

        {/* 场景列表 */}
        <section className="scene-list-section">
          <h2 className="scene-list-section__title">可勘查场景</h2>
          {scenes.length === 0 ? (
            <p className="scene-list-section__empty">
              案件场景尚未生成，请稍候或刷新页面。
            </p>
          ) : (
            <div className="scene-list">
              {scenes.map((scene) => {
                const sceneClueCount = clueCountByScene(scene.id)
                return (
                  <button
                    key={scene.id}
                    className="scene-card"
                    onClick={() => navigate(`/investigation/${gameId}/scene/${scene.id}`)}
                    type="button"
                  >
                    <div className="scene-card__header">
                      <h3 className="scene-card__name">{scene.name}</h3>
                      {sceneClueCount > 0 && (
                        <span className="scene-card__badge">{sceneClueCount} 条线索</span>
                      )}
                    </div>
                    <p className="scene-card__description">{scene.description}</p>
                    <div className="scene-card__footer">
                      <span className="scene-card__npc">NPC：{scene.npcPersona || '未知'}</span>
                      <span className="scene-card__objects">{scene.objects.length} 处可查看</span>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </section>

        {/* 已发现线索面板 */}
        {clues.length > 0 && (
          <section className="discovered-clues-panel">
            <h2>已添加线索 ({clues.length})</h2>
            <ul className="clue-list">
              {clues.map((clue) => (
                <li key={clue.id} className="clue-item">
                  <span className="clue-item__label">{clue.userLabel || clue.description.substring(0, 30)}</span>
                  <span className="clue-item__source">
                    {clue.sourceType === 'scene' ? '📍 现场' : clue.sourceType === 'interrogation' ? '🗣 审讯' : '📋 初始'}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>

      {/* 底部导航 */}
      <footer className="investigation-footer">
        <button className="footer-button footer-button--back" onClick={() => navigate('/')} type="button">
          返回贝克街
        </button>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to={`/deduction/${gameId}`} className="footer-button footer-button--secondary">
            推理板
          </Link>
          <Link to={`/interrogation/${gameId}`} className="footer-button footer-button--secondary">
            传唤嫌疑人
          </Link>
          <Link to={`/conclusion/${gameId}`} className="footer-button footer-button--next">
            指认真凶
          </Link>
        </div>
      </footer>

      <WatsonChatDialog gameId={gameId!} />
    </div>
  )
}
