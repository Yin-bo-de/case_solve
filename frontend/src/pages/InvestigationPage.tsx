import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { GameState, Observation } from '@/types/game'
import { gameApi } from '@/services/api'

// 华生消息类型
interface WatsonMessage {
  id: string
  content: string
  type: 'observation' | 'hint' | 'welcome' | 'encouragement'
  timestamp: Date
}

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

// 空闲检测时长（毫秒）
const IDLE_TIMEOUT = 30000 // 30秒无操作后触发提示

export default function InvestigationPage() {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()

  const [gameState, setGameState] = useState<GameState | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedArea, setSelectedArea] = useState<InvestigationArea | null>(null)
  const [observations, setObservations] = useState<Observation[]>([])
  const [showObservations, setShowObservations] = useState(false)
  const [areas, setAreas] = useState<InvestigationArea[]>([])

  // 华生相关状态
  const [watsonMessages, setWatsonMessages] = useState<WatsonMessage[]>([])
  const [isWatsonTyping, setIsWatsonTyping] = useState(false)
  const [showWatsonDialog, setShowWatsonDialog] = useState(true)

  // 空闲检测相关
  const lastActivityRef = useRef<number>(Date.now())
  const idleTimerRef = useRef<number | null>(null)
  const hasShownIdleHintRef = useRef(false)

  console.debug('[InvestigationPage] 渲染勘查页面', { gameId })

  // 添加华生消息
  const addWatsonMessage = useCallback((content: string, type: WatsonMessage['type'] = 'observation') => {
    const message: WatsonMessage = {
      id: `watson-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      content,
      type,
      timestamp: new Date(),
    }
    console.info('[InvestigationPage] 华生消息', { content, type })
    setWatsonMessages(prev => [...prev, message])
  }, [])

  // 请求华生观察评论
  const requestWatsonObservationComment = useCallback(async (observation: Observation) => {
    if (!gameId) return

    try {
      setIsWatsonTyping(true)
      console.info('[InvestigationPage] 请求华生观察评论', { observationId: observation.id })

      const response = await gameApi.getWatsonObservationComment(gameId, observation)
      addWatsonMessage(response.comment, 'observation')
    } catch (err) {
      console.warn('[InvestigationPage] 获取华生评论失败', err)
    } finally {
      setIsWatsonTyping(false)
    }
  }, [gameId, addWatsonMessage])

  // 请求华生空闲提示
  const requestWatsonIdleHint = useCallback(async () => {
    if (!gameId || hasShownIdleHintRef.current) return

    try {
      setIsWatsonTyping(true)
      console.info('[InvestigationPage] 请求华生空闲提示')

      const response = await gameApi.getWatsonHint(
        gameId,
        'idle',
        observations.length,
        areas.filter(a => a.examined).length,
        areas.length
      )

      if (response.hint) {
        addWatsonMessage(response.hint, 'hint')
        hasShownIdleHintRef.current = true
      }
    } catch (err) {
      console.warn('[InvestigationPage] 获取华生提示失败', err)
    } finally {
      setIsWatsonTyping(false)
    }
  }, [gameId, observations.length, areas, addWatsonMessage])

  // 记录用户活动
  const recordActivity = useCallback(() => {
    lastActivityRef.current = Date.now()
    hasShownIdleHintRef.current = false
  }, [])

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

    const loadGame = async () => {
      console.info('[InvestigationPage] 加载游戏状态', { gameId })
      setIsLoading(true)
      setError(null)

      try {
        const state = await gameApi.getGameState(gameId)
        console.info('[InvestigationPage] 游戏状态加载成功', state)
        setGameState(state)
        initializeAreas()

        // 显示华生欢迎消息
        setTimeout(() => {
          addWatsonMessage(
            '老朋友，我们到了。这就是案发现场。仔细看看周围，任何细节都可能是重要的线索。',
            'welcome'
          )
        }, 500)
      } catch (err) {
        console.error('[InvestigationPage] 加载游戏失败', err)
        setError(err instanceof Error ? err.message : '加载游戏失败')
      } finally {
        setIsLoading(false)
      }
    }

    loadGame()
  }, [gameId, addWatsonMessage])

  // 空闲检测
  useEffect(() => {
    if (isLoading) return

    const checkIdle = () => {
      const now = Date.now()
      const idleTime = now - lastActivityRef.current

      if (idleTime >= IDLE_TIMEOUT && !hasShownIdleHintRef.current) {
        console.debug('[InvestigationPage] 检测到用户空闲，请求华生提示')
        requestWatsonIdleHint()
      }
    }

    idleTimerRef.current = window.setInterval(checkIdle, 5000)

    return () => {
      if (idleTimerRef.current) {
        window.clearInterval(idleTimerRef.current)
      }
    }
  }, [isLoading, requestWatsonIdleHint])

  // 处理点击勘查区域
  const handleAreaClick = (area: InvestigationArea) => {
    console.debug('[InvestigationPage] 点击勘查区域', { areaId: area.id, areaName: area.name })
    recordActivity()

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
    setObservations(prev => [...prev, newObservation])

    setSelectedArea({ ...area, examined: true })

    // 请求华生对这个观察的评论（有一定概率，不是每次都说话）
    if (Math.random() > 0.3) {
      requestWatsonObservationComment(newObservation)
    }
  }

  // 关闭区域详情
  const closeAreaDetail = () => {
    console.debug('[InvestigationPage] 关闭区域详情')
    recordActivity()
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
    <div className="investigation-page" onClick={recordActivity}>
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

      {/* 华生对话框 */}
      <div className={`watson-dialog ${showWatsonDialog ? 'watson-dialog--open' : ''}`}>
        <div className="watson-dialog__header">
          <div className="watson-avatar">
            <span className="watson-avatar__icon">👨‍⚕️</span>
          </div>
          <div className="watson-info">
            <h4 className="watson-name">约翰·华生</h4>
            <span className="watson-status">{isWatsonTyping ? '正在思考...' : '在线'}</span>
          </div>
          <button
            className="watson-dialog__toggle"
            onClick={() => setShowWatsonDialog(!showWatsonDialog)}
            type="button"
          >
            {showWatsonDialog ? '−' : '+'}
          </button>
        </div>

        {showWatsonDialog && (
          <div className="watson-dialog__content">
            <div className="watson-messages">
              {watsonMessages.length === 0 ? (
                <div className="watson-welcome">
                  <p>华生医生会在这里给你提示和建议。</p>
                </div>
              ) : (
                watsonMessages.map(msg => (
                  <div key={msg.id} className={`watson-message watson-message--${msg.type}`}>
                    <div className="watson-message__content">{msg.content}</div>
                    <div className="watson-message__time">
                      {msg.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                ))
              )}
              {isWatsonTyping && (
                <div className="watson-typing">
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

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
        <button className="footer-button footer-button--next" disabled={observations.length === 0} type="button">
          下一步: 审讯嫌疑人
        </button>
      </footer>
    </div>
  )
}
