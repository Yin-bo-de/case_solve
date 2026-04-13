import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import type { Observation } from '@/types/game'
import { gameApi } from '@/services/api'
import { useGameStore, useCluesStore } from '@/store'
import WatsonChatDialog from '@/components/WatsonChatDialog'

// 现场可点击区域定义
interface InvestigationArea {
  id: string
  name: string
  description: string
  x: number // 位置百分比
  y: number
  width: number
  height: number
  examined: boolean
}

export default function InvestigationPage() {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()

  // 使用 Zustand stores
  const {
    gameState,
    isLoading,
    error,
    setGameState,
    setLoading,
    setError
  } = useGameStore()

  const {
    observations,
    addObservation
  } = useCluesStore()

  // 本地 UI 状态
  const [selectedArea, setSelectedArea] = useState<InvestigationArea | null>(null)
  const [showObservations, setShowObservations] = useState(false)
  const [areas, setAreas] = useState<InvestigationArea[]>([])

  console.debug('[InvestigationPage] 渲染勘查页面', { gameId, useStore: true })

  // 初始化现场区域
  const initializeAreas = () => {
    const newAreas: InvestigationArea[] = [
      {
        id: 'area-desk',
        name: '书桌',
        description: '一张老旧的橡木书桌，上面散落着文件和物品。',
        x: 60,
        y: 55,
        width: 25,
        height: 20,
        examined: false,
      },
      {
        id: 'area-fireplace',
        name: '壁炉',
        description: '大理石壁炉，里面有未烧尽的灰烬。',
        x: 10,
        y: 40,
        width: 20,
        height: 25,
        examined: false,
      },
      {
        id: 'area-body',
        name: '尸体位置',
        description: '地毯上用白粉笔勾勒出的尸体轮廓。',
        x: 35,
        y: 60,
        width: 20,
        height: 15,
        examined: false,
      },
      {
        id: 'area-window',
        name: '窗户',
        description: '一扇朝向街道的落地窗，窗帘半拉着。',
        x: 75,
        y: 20,
        width: 20,
        height: 30,
        examined: false,
      },
      {
        id: 'area-carpet',
        name: '地毯',
        description: '厚重的波斯地毯，有些地方看起来被移动过。',
        x: 25,
        y: 70,
        width: 40,
        height: 20,
        examined: false,
      },
      {
        id: 'area-corner',
        name: '角落',
        description: '房间阴暗的角落，有什么东西在闪闪发光。',
        x: 5,
        y: 75,
        width: 15,
        height: 15,
        examined: false,
      },
    ]
    setAreas(newAreas)
  }

  // 加载游戏状态
  useEffect(() => {
    if (!gameId) return

    // 如果 store 中已有数据且 gameId 匹配，直接使用
    if (gameState && (gameState as any).gameId === gameId) {
      console.debug('[InvestigationPage] 使用 store 中已有的游戏状态')
      initializeAreas()
      return
    }

    const loadGame = async () => {
      console.info('[InvestigationPage] 从 API 加载游戏状态', { gameId })
      setLoading(true)
      setError(null)

      try {
        const state = await gameApi.getGameState(gameId)
        console.info('[InvestigationPage] 游戏状态加载成功', state)
        setGameState(state)
        initializeAreas()
      } catch (err) {
        console.error('[InvestigationPage] 加载游戏失败', err)
        setError(err instanceof Error ? err.message : '加载游戏失败')
      } finally {
        setLoading(false)
      }
    }

    loadGame()
  }, [gameId, gameState, setGameState, setLoading, setError])

  // 处理点击勘查区域
  const handleAreaClick = (area: InvestigationArea) => {
    console.debug('[InvestigationPage] 点击勘查区域', { areaId: area.id, areaName: area.name })

    if (!gameState?.case) return

    // 标记区域为已勘查
    const updatedAreas = areas.map(a =>
      a.id === area.id ? { ...a, examined: true } : a
    )
    setAreas(updatedAreas)

    // 查找该区域相关的线索
    const relatedClues = gameState.case.clues.filter(
      clue => clue.location?.includes(area.name) || clue.location?.includes(area.id)
    )

    // 创建观察记录
    const newObservation: Observation = {
      id: `obs-${Date.now()}-${area.id}`,
      description: `在${area.name}发现：${area.description}`,
      location: area.name,
      timestamp: new Date().toISOString(),
      relatedClueIds: relatedClues.map(c => c.id),
      notes: relatedClues.length > 0 ? `发现 ${relatedClues.length} 个相关线索` : undefined,
    }

    console.info('[InvestigationPage] 记录新观察', newObservation)
    addObservation(newObservation)

    setSelectedArea({ ...area, examined: true })
  }

  // 关闭区域详情
  const closeAreaDetail = () => {
    console.debug('[InvestigationPage] 关闭区域详情')
    setSelectedArea(null)
  }

  if (isLoading) {
    return (
      <div className="investigation-page investigation-page--loading">
        <div className="loading-spinner">
          <p>正在进入案发现场...</p>
        </div>
      </div>
    )
  }

  if (error || !gameState) {
    return (
      <div className="investigation-page investigation-page--error">
        <div className="error-message">
          <h2>出错了</h2>
          <p>{error || '无法加载游戏'}</p>
          <button onClick={() => navigate('/')} type="button">
            返回贝克街
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="investigation-page">
      {/* 顶部导航栏 */}
      <header className="investigation-header">
        <div className="header-content">
          <h1 className="header-title">现场勘查</h1>
          <div className="header-info">
            <span className="case-location">{gameState.case?.location}</span>
            <span className="observation-count">
              观察记录: {observations.length}
            </span>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="investigation-main">
        {/* 案发现场场景 */}
        <div className="crime-scene">
          <div className="crime-scene__background">
            {/* 场景背景 */}
            <div className="scene-wall scene-wall--back" />
            <div className="scene-floor" />

            {/* 可点击区域 */}
            {areas.map(area => (
              <button
                key={area.id}
                className={`investigation-area ${area.examined ? 'investigation-area--examined' : ''}`}
                style={{
                  left: `${area.x}%`,
                  top: `${area.y}%`,
                  width: `${area.width}%`,
                  height: `${area.height}%`,
                }}
                onClick={() => handleAreaClick(area)}
                type="button"
              >
                <span className="area-label">{area.name}</span>
                {area.examined && <span className="area-checkmark">✓</span>}
              </button>
            ))}
          </div>

          {/* 场景说明 */}
          <div className="scene-description">
            <h2>{gameState.case?.location}</h2>
            <p>{gameState.case?.summary}</p>
          </div>
        </div>

        {/* 观察笔记面板 */}
        <aside className={`observation-panel ${showObservations ? 'observation-panel--open' : ''}`}>
          <div className="panel-header">
            <h3>观察笔记</h3>
            <button
              className="panel-toggle"
              onClick={() => setShowObservations(!showObservations)}
              type="button"
            >
              {showObservations ? '收起' : '展开'}
            </button>
          </div>

          <div className="panel-content">
            {observations.length === 0 ? (
              <p className="no-observations">还没有记录任何观察，点击场景中的区域开始勘查吧。</p>
            ) : (
              <ul className="observation-list">
                {observations.map(obs => (
                  <li key={obs.id} className="observation-item">
                    <div className="observation-location">{obs.location}</div>
                    <div className="observation-description">{obs.description}</div>
                    <div className="observation-time">
                      {new Date(obs.timestamp).toLocaleTimeString()}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>
      </main>

      {/* 区域详情弹窗 */}
      {selectedArea && (
        <div className="area-modal-overlay" onClick={closeAreaDetail}>
          <div className="area-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedArea.name}</h2>
              <button className="modal-close" onClick={closeAreaDetail} type="button">
                ×
              </button>
            </div>
            <div className="modal-content">
              <p className="area-description">{selectedArea.description}</p>

              {/* 显示相关线索 */}
              {gameState.case && (
                <div className="related-clues">
                  <h3>发现的线索</h3>
                  {(() => {
                    const clues = gameState.case!.clues.filter(
                      clue =>
                        clue.location?.includes(selectedArea.name) ||
                        clue.location?.includes(selectedArea.id)
                    )
                    console.debug('[InvestigationPage] 查找相关线索', {
                      area: selectedArea.name,
                      allClues: gameState.case!.clues.map(c => ({ id: c.id, location: c.location })),
                      foundClues: clues.map(c => c.id),
                    })
                    if (clues.length === 0) {
                      return <p className="no-clues">这里暂时没有发现明显的线索。</p>
                    }
                    return (
                      <ul className="clue-list">
                        {clues.map(clue => (
                          <li key={clue.id} className={`clue-item ${clue.isRedHerring ? 'clue-item--red-herring' : ''}`}>
                            <span className="clue-type">[{clue.clueType}]</span>
                            <span className="clue-description">{clue.description}</span>
                          </li>
                        ))}
                      </ul>
                    )
                  })()}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button onClick={closeAreaDetail} className="modal-button" type="button">
                继续勘查
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 底部导航 */}
      <footer className="investigation-footer">
        <button className="footer-button footer-button--back" onClick={() => navigate('/')} type="button">
          返回贝克街
        </button>
        <div className="footer-progress">
          <span>勘查进度: {areas.filter(a => a.examined).length} / {areas.length}</span>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Link
            to={`/deduction/${gameId}`}
            className="footer-button footer-button--secondary"
          >
            推理板
          </Link>
          <Link
            to={`/interrogation/${gameId}`}
            className={`footer-button footer-button--secondary ${observations.length === 0 ? 'disabled-link' : ''}`}
            aria-disabled={observations.length === 0}
            onClick={(e) => {
              if (observations.length === 0) {
                e.preventDefault()
              }
            }}
          >
            审讯嫌疑人
          </Link>
          <Link
            to={`/conclusion/${gameId}`}
            className="footer-button footer-button--next"
          >
            指认凶手
          </Link>
        </div>
      </footer>

      {/* 华生全程对话框 */}
      <WatsonChatDialog gameId={gameId!} />
    </div>
  )
}
