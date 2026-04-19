import { useState, useMemo } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useGameStore, useCluesStore } from '@/store'
import type { Scene } from '@/types/game'
import { useGameSessionSync } from '@/hooks/useGameSessionSync'
import SceneObjectCard from '@/components/ScenePanel/SceneObjectCard'
import SceneChat from '@/components/ScenePanel/SceneChat'
import WatsonChatDialog from '@/components/WatsonChatDialog'

const PLACEHOLDER_IMG = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"%3E%3Crect width="400" height="300" fill="%231a1a2e"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23c9a05c" font-size="18" font-family="Georgia"%3E维多利亚时代场景%3C/text%3E%3C/svg%3E'

export default function ScenePage() {
  const { gameId, sceneId } = useParams<{ gameId: string; sceneId: string }>()
  const navigate = useNavigate()
  const { gameState, isLoading, error } = useGameStore()
  const { clues } = useCluesStore()

  const [activeObjectId, setActiveObjectId] = useState<string | null>(null)

  console.debug('[ScenePage] 渲染', { gameId, sceneId })

  useGameSessionSync(gameId)

  const scene = useMemo<Scene | null>(
    () => gameState?.case?.scenes?.find((s) => s.id === sceneId) ?? null,
    [gameState?.case?.scenes, sceneId]
  )

  if (isLoading) {
    return (
      <div className="scene-page scene-page--loading">
        <div className="loading-spinner">正在进入场景……</div>
      </div>
    )
  }

  if (error || !scene) {
    return (
      <div className="scene-page scene-page--error">
        <div className="error-message">
          <h2>无法进入该场景</h2>
          <p>{error || '场景不存在'}</p>
          <button onClick={() => navigate(`/investigation/${gameId}`)} type="button">
            返回勘查
          </button>
        </div>
      </div>
    )
  }

  const activeObject = scene.objects.find((o) => o.id === activeObjectId)
  // 当前场景已添加的线索数
  const sceneClueCount = clues.filter(
    (c) => c.sourceType === 'scene' && c.sourceRef === sceneId
  ).length

  return (
    <div className="scene-page">
      {/* 顶部导航 */}
      <header className="scene-page__header">
        <Link to={`/investigation/${gameId}`} className="scene-page__back-btn">
          ← 返回场景列表
        </Link>
        <h1 className="scene-page__title">{scene.name}</h1>
        <span className="scene-page__clue-count">已添加线索: {sceneClueCount}</span>
      </header>

      <div className="scene-page__body">
        {/* 左栏：可交互对象列表 */}
        <aside className="scene-page__objects">
          <h2 className="scene-page__section-title">可查看之物</h2>
          <div className="scene-page__objects-list">
            {scene.objects.map((obj) => (
              <SceneObjectCard
                key={obj.id}
                object={obj}
                onClick={(o) => setActiveObjectId(o.id === activeObjectId ? null : o.id)}
              />
            ))}
          </div>
          {activeObject && (
            <div className="scene-page__object-detail">
              <h3>{activeObject.name}</h3>
              <p>{activeObject.description}</p>
              {activeObject.searchHints.length > 0 && (
                <ul className="scene-page__hints">
                  {activeObject.searchHints.map((hint, i) => (
                    <li key={i}>💡 {hint}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </aside>

        {/* 中栏：场景氛围 */}
        <main className="scene-page__atmosphere">
          <img
            src={scene.atmosphereImage || PLACEHOLDER_IMG}
            alt={scene.name}
            className="scene-page__atmosphere-img"
          />
          <div className="scene-page__atmosphere-info">
            <p className="scene-page__npc-persona">NPC：{scene.npcPersona}</p>
            <p className="scene-page__description">{scene.description}</p>
          </div>
        </main>

        {/* 右栏：与场景 NPC 对话 */}
        <section className="scene-page__chat-section">
          <h2 className="scene-page__section-title">探查此处</h2>
          {gameId && sceneId && (
            <SceneChat gameId={gameId} sceneId={sceneId} />
          )}
        </section>
      </div>

      <WatsonChatDialog gameId={gameId!} />
    </div>
  )
}
