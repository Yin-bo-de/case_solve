import { useState, useEffect, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { gameApi } from '@/services/api'
import type {
  GameState,
  ConclusionReadiness,
  AccusationResult,
  CaseReveal,
  DeductionChain
} from '@/types/game'
import WatsonChatDialog from '@/components/WatsonChatDialog'

console.debug('[ConclusionPage.tsx] 加载模块')

type ConclusionStep = 'select' | 'reasoning' | 'reveal'

interface ConclusionPageProps {
}

const ConclusionPage: React.FC<ConclusionPageProps> = () => {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()
  console.debug('[ConclusionPage.tsx] 渲染组件', { gameId })

  const [gameState, setGameState] = useState<GameState | null>(null)
  const [readiness, setReadiness] = useState<ConclusionReadiness | null>(null)
  const [accusationResult, setAccusationResult] = useState<AccusationResult | null>(null)
  const [caseReveal, setCaseReveal] = useState<CaseReveal | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState<ConclusionStep>('select')
  const [selectedSuspectId, setSelectedSuspectId] = useState<string | null>(null)
  const [reasoningSteps, setReasoningSteps] = useState<string[]>([])
  const [newReasoningStep, setNewReasoningStep] = useState('')
  const [showReveal, setShowReveal] = useState(false)

  const loadData = useCallback(async () => {
    if (!gameId) return

    console.info('[ConclusionPage.tsx] 加载数据', { gameId })
    setLoading(true)
    setError(null)

    try {
      const [gameStateData, deductionData, readinessData] = await Promise.all([
        gameApi.getGameState(gameId),
        gameApi.getDeductionChain(gameId),
        gameApi.checkConclusionReadiness(gameId),
      ])

      console.debug('[ConclusionPage.tsx] 数据加载完成', { gameStateData, deductionData, readinessData })
      setGameState(gameStateData)
      setReadiness(readinessData)

      // 自动填充推理步骤
      const autoSteps = buildReasoningSteps(deductionData)
      setReasoningSteps(autoSteps)
    } catch (err) {
      console.error('[ConclusionPage.tsx] 加载数据失败', err)
      setError('加载数据失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [gameId])

  const buildReasoningSteps = (chain: DeductionChain): string[] => {
    const steps: string[] = []

    // 添加观察作为第一步
    if (chain.observations.length > 0) {
      steps.push(`我在案发现场收集了 ${chain.observations.length} 条重要线索...`)
    }

    // 添加推理节点
    chain.inferences.forEach((inf, index) => {
      steps.push(`${index + 1}. ${inf.content}`)
    })

    // 添加假设
    chain.hypotheses.forEach((hyp) => {
      if (hyp.isVerified) {
        steps.push(`最终假设: ${hyp.title}`)
      }
    })

    return steps
  }

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleSelectSuspect = (suspectId: string) => {
    console.info('[ConclusionPage.tsx] 选择嫌疑人', { suspectId })
    setSelectedSuspectId(suspectId)
  }

  const addReasoningStep = () => {
    if (!newReasoningStep.trim()) return
    console.info('[ConclusionPage.tsx] 添加推理步骤', { step: newReasoningStep })
    setReasoningSteps(prev => [...prev, newReasoningStep.trim()])
    setNewReasoningStep('')
  }

  const removeReasoningStep = (index: number) => {
    console.info('[ConclusionPage.tsx] 删除推理步骤', { index })
    setReasoningSteps(prev => prev.filter((_, i) => i !== index))
  }

  const goToReasoning = () => {
    if (!selectedSuspectId) return
    console.info('[ConclusionPage.tsx] 进入推理步骤展示', { selectedSuspectId })
    setCurrentStep('reasoning')
  }

  const goToSelect = () => {
    console.info('[ConclusionPage.tsx] 返回选择凶手')
    setCurrentStep('select')
  }

  const makeAccusation = async () => {
    if (!gameId || !selectedSuspectId) return

    console.info('[ConclusionPage.tsx] 指认凶手', { gameId, suspectId: selectedSuspectId, reasoningSteps })
    setLoading(true)
    setError(null)

    try {
      const result = await gameApi.makeAccusation(gameId, selectedSuspectId, reasoningSteps)
      console.debug('[ConclusionPage.tsx] 指认结果', result)
      setAccusationResult(result)
      setCurrentStep('reveal')

      if (result.isCorrect) {
        // 如果正确，获取完整案件真相
        const reveal = await gameApi.getCaseReveal(gameId)
        console.debug('[ConclusionPage.tsx] 案件真相', reveal)
        setCaseReveal(reveal)
      }
    } catch (err) {
      console.error('[ConclusionPage.tsx] 指认失败', err)
      setError('指认失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const goBackToInvestigation = () => {
    console.info('[ConclusionPage.tsx] 返回继续调查')
    if (gameId) {
      navigate(`/investigation/${gameId}`)
    }
  }

  const playAgain = () => {
    console.info('[ConclusionPage.tsx] 再玩一局')
    navigate('/')
  }

  if (loading) {
    return (
      <div className="conclusion-page loading">
        <div className="loading-spinner">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="conclusion-page error">
        <div className="error-message">{error}</div>
        <button className="button" onClick={loadData}>重试</button>
      </div>
    )
  }

  if (!gameState || !gameState.case || !readiness) {
    return (
      <div className="conclusion-page error">
        <div className="error-message">无法获取游戏数据</div>
      </div>
    )
  }

  if (!readiness.isReady && currentStep !== 'reveal') {
    return (
      <div className="conclusion-page not-ready">
        <div className="not-ready-container">
          <h2 className="not-ready-title">还没到结案的时候...</h2>
          <div className="not-ready-message">{readiness.reason}</div>
          <div className="readiness-stats">
            <div className="stat">
              <span className="stat-label">已收集观察:</span>
              <span className="stat-value">{readiness.observationsCount}/{readiness.minimumObservations}</span>
            </div>
            <div className="stat">
              <span className="stat-label">推理节点:</span>
              <span className="stat-value">{readiness.inferencesCount}</span>
            </div>
            <div className="stat">
              <span className="stat-label">假设数量:</span>
              <span className="stat-value">{readiness.hypothesesCount}</span>
            </div>
          </div>
          <div className="not-ready-actions">
            <Link to={`/investigation/${gameId}`} className="button button--secondary">
              返回继续调查
            </Link>
            <button
              className="button button--primary"
              onClick={() => setCurrentStep('select')}
            >
              还是要结案
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="conclusion-page">
      <div className="conclusion-container">
        <h1 className="conclusion-title">⚖️ 结案：演绎法展示</h1>

        {/* 步骤指示器 */}
        <div className="step-indicator">
          <div className={`step ${currentStep === 'select' ? 'active' : ''} ${currentStep !== 'select' ? 'completed' : ''}`}>
            1. 选择凶手
          </div>
          <div className="step-separator"></div>
          <div className={`step ${currentStep === 'reasoning' ? 'active' : ''} ${currentStep === 'reveal' ? 'completed' : ''}`}>
            2. 陈述推理
          </div>
          <div className="step-separator"></div>
          <div className={`step ${currentStep === 'reveal' ? 'active' : ''}`}>
            3. 戏剧性揭露
          </div>
        </div>

        {/* 第一步：选择凶手 */}
        {currentStep === 'select' && (
          <div className="step-content select-suspect">
            <h2 className="step-title">【第一步：选择凶手】</h2>
            <p className="step-description">请指出你认为的真凶：</p>

            <div className="suspect-grid">
              {gameState.case.suspects.map((suspect) => (
                <div
                  key={suspect.id}
                  className={`suspect-card ${selectedSuspectId === suspect.id ? 'selected' : ''}`}
                  onClick={() => handleSelectSuspect(suspect.id)}
                >
                  <div className="suspect-avatar">
                    {suspect.name.charAt(0)}
                  </div>
                  <div className="suspect-info">
                    <h3 className="suspect-name">{suspect.name}</h3>
                    <p className="suspect-age">{suspect.age}岁</p>
                    <p className="suspect-background">{suspect.background}</p>
                  </div>
                  {selectedSuspectId === suspect.id && (
                    <div className="selected-badge">✓ 已选择</div>
                  )}
                </div>
              ))}
            </div>

            <div className="step-actions">
              <Link to={`/investigation/${gameId}`} className="button button--secondary">
                🔙 继续调查
              </Link>
              <button
                className="button button--primary"
                disabled={!selectedSuspectId}
                onClick={goToReasoning}
              >
                下一步 →
              </button>
            </div>
          </div>
        )}

        {/* 第二步：陈述推理过程 */}
        {currentStep === 'reasoning' && (
          <div className="step-content reasoning">
            <h2 className="step-title">【第二步：陈述推理过程】</h2>
            <p className="step-description">像福尔摩斯那样一步步展示你的推理：</p>

            <div className="selected-suspect-summary">
              <span className="label">你选择的凶手：</span>
              <span className="suspect-name">
                {gameState.case.suspects.find(s => s.id === selectedSuspectId)?.name}
              </span>
            </div>

            <div className="reasoning-steps">
              <h3 className="subsection-title">📝 让我从最开始说起...</h3>
              <div className="steps-list">
                {reasoningSteps.map((step, index) => (
                  <div key={index} className="reasoning-step">
                    <span className="step-number">{index + 1}.</span>
                    <span className="step-content">{step}</span>
                    <button
                      className="remove-step-btn"
                      onClick={() => removeReasoningStep(index)}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>

              <div className="add-step-form">
                <input
                  type="text"
                  className="input"
                  placeholder="添加推理步骤..."
                  value={newReasoningStep}
                  onChange={(e) => setNewReasoningStep(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addReasoningStep()}
                />
                <button className="button button--small" onClick={addReasoningStep}>
                  + 添加
                </button>
              </div>
            </div>

            <div className="step-actions">
              <button className="button button--secondary" onClick={goToSelect}>
                ← 上一步
              </button>
              <button
                className="button button--primary"
                onClick={makeAccusation}
                disabled={loading}
              >
                {loading ? '指认中...' : '⚖️ 指认凶手'}
              </button>
            </div>
          </div>
        )}

        {/* 第三步：戏剧性揭露 */}
        {currentStep === 'reveal' && accusationResult && (
          <div className="step-content reveal">
            <div className={`accusation-result ${accusationResult.isCorrect ? 'correct' : 'incorrect'}`}>
              {accusationResult.isCorrect ? (
                <>
                  <div className="result-icon">🎭</div>
                  <h2 className="result-title">完美的推理，老朋友！</h2>
                </>
              ) : (
                <>
                  <div className="result-icon">🤔</div>
                  <h2 className="result-title">我觉得这里有些问题...</h2>
                </>
              )}

              <div className="watson-feedback">
                <span className="watson-label">【华生】：</span>
                <span className="watson-text">{accusationResult.watsonFeedback}</span>
              </div>

              {!accusationResult.isCorrect && (
                <div className="mistake-info">
                  <p>错误次数：{accusationResult.mistakesMade}/{accusationResult.maxMistakes}</p>
                  {accusationResult.canContinue ? (
                    <button className="button button--secondary" onClick={goBackToInvestigation}>
                      🔙 返回继续调查
                    </button>
                  ) : (
                    <div className="game-over">
                      <p>很遗憾，你已经用完了所有机会...</p>
                      {caseReveal && (
                        <button
                          className="button button--primary"
                          onClick={() => setShowReveal(true)}
                        >
                          查看真相
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 完整案件真相 */}
            {(accusationResult.isCorrect || showReveal) && caseReveal && (
              <div className="case-reveal">
                <h3 className="reveal-title">📜 完整案件真相</h3>

                <div className="reveal-section">
                  <h4>死者</h4>
                  <p><strong>{caseReveal.victim.name}</strong></p>
                  <p>{caseReveal.victim.background}</p>
                  <p>死因：{caseReveal.victim.causeOfDeath}</p>
                  <p>死亡时间：{caseReveal.victim.timeOfDeath}</p>
                </div>

                {caseReveal.trueMurderer && (
                  <div className="reveal-section">
                    <h4>真凶</h4>
                    <p><strong>{caseReveal.trueMurderer.name}</strong> ({caseReveal.trueMurderer.age}岁)</p>
                    <p>{caseReveal.trueMurderer.background}</p>
                    <p><strong>动机：</strong>{caseReveal.trueMurderer.motive}</p>
                    {caseReveal.trueMurderer.secrets.length > 0 && (
                      <p><strong>秘密：</strong>{caseReveal.trueMurderer.secrets.join('；')}</p>
                    )}
                  </div>
                )}

                <div className="reveal-section">
                  <h4>作案手法</h4>
                  <p>{caseReveal.murderMethod}</p>
                </div>

                <div className="reveal-section">
                  <h4>案件总结</h4>
                  <p>{caseReveal.caseSummary}</p>
                </div>

                <div className="reveal-section">
                  <h4>关键线索</h4>
                  <ul>
                    {caseReveal.keyClues.map((clue) => (
                      <li key={clue.id}>{clue.description}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            <div className="final-actions">
              <button className="button button--primary" onClick={playAgain}>
                🔄 再玩一局
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 华生对话框 */}
      <WatsonChatDialog gameId={gameId!} />
    </div>
  )
}

export default ConclusionPage
