import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { gameApi } from '@/services/api'
import type { GameState, DeductionChain, Inference, Hypothesis } from '@/types/game'

console.debug('[DeductionBoard.tsx] 加载模块')

interface DeductionBoardProps {
}

type SelectionMode = 'observations' | 'none'
type VerificationMode = { hypothesisId: string; isVerified: boolean } | null

interface LogicGap {
  type: string
  target_type?: string
  target_id?: string
  description: string
  unused_count?: number
}

const DeductionBoard: React.FC<DeductionBoardProps> = () => {
  const { gameId } = useParams<{ gameId: string }>()
  console.debug('[DeductionBoard.tsx] 渲染组件', { gameId })

  const [gameState, setGameState] = useState<GameState | null>(null)
  const [deductionChain, setDeductionChain] = useState<DeductionChain | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [selectedObservationIds, setSelectedObservationIds] = useState<string[]>([])
  const [selectionMode, setSelectionMode] = useState<SelectionMode>('none')
  const [newInferenceContent, setNewInferenceContent] = useState('')
  const [showInferenceForm, setShowInferenceForm] = useState(false)

  const [selectedInferenceIds, setSelectedInferenceIds] = useState<string[]>([])
  const [newHypothesisTitle, setNewHypothesisTitle] = useState('')
  const [newHypothesisDescription, setNewHypothesisDescription] = useState('')
  const [selectedSuspectId, setSelectedSuspectId] = useState<string | null>(null)
  const [showHypothesisForm, setShowHypothesisForm] = useState(false)

  const [watsonFeedback, setWatsonFeedback] = useState<{ feedback: string; suggestions: string[]; logic_gaps?: LogicGap[] } | null>(null)
  const [showWatsonFeedback, setShowWatsonFeedback] = useState(false)

  const [expandedHypothesisId, setExpandedHypothesisId] = useState<string | null>(null)
  const [verificationMode, setVerificationMode] = useState<VerificationMode>(null)
  const [verificationNotes, setVerificationNotes] = useState('')

  const loadData = useCallback(async () => {
    if (!gameId) return

    console.info('[DeductionBoard.tsx] 加载数据', { gameId })
    setLoading(true)
    setError(null)

    try {
      const [gameStateData, deductionData] = await Promise.all([
        gameApi.getGameState(gameId),
        gameApi.getDeductionChain(gameId),
      ])

      console.debug('[DeductionBoard.tsx] 数据加载完成', { gameStateData, deductionData })
      setGameState(gameStateData)
      setDeductionChain(deductionData)
    } catch (err) {
      console.error('[DeductionBoard.tsx] 加载数据失败', err)
      setError('加载数据失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [gameId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const toggleObservationSelection = (observationId: string) => {
    console.debug('[DeductionBoard.tsx] 切换观察选择', { observationId })
    setSelectedObservationIds(prev => {
      if (prev.includes(observationId)) {
        return prev.filter(id => id !== observationId)
      } else {
        return [...prev, observationId]
      }
    })
  }

  const startObservationSelection = () => {
    console.info('[DeductionBoard.tsx] 开始选择观察')
    setSelectionMode('observations')
    setSelectedObservationIds([])
    setShowInferenceForm(false)
  }

  const cancelSelection = () => {
    console.info('[DeductionBoard.tsx] 取消选择')
    setSelectionMode('none')
    setSelectedObservationIds([])
    setSelectedInferenceIds([])
    setShowInferenceForm(false)
    setShowHypothesisForm(false)
    setVerificationMode(null)
    setVerificationNotes('')
  }

  const confirmObservationSelection = () => {
    console.info('[DeductionBoard.tsx] 确认观察选择', { selectedObservationIds })
    setSelectionMode('none')
    setShowInferenceForm(true)
    setNewInferenceContent('')
  }

  const handleCreateInference = async () => {
    if (!gameId || !newInferenceContent.trim() || selectedObservationIds.length === 0) return

    console.info('[DeductionBoard.tsx] 创建推理', { content: newInferenceContent, observationIds: selectedObservationIds })

    try {
      const newInference = await gameApi.createInference(
        gameId,
        newInferenceContent.trim(),
        selectedObservationIds
      )

      console.debug('[DeductionBoard.tsx] 推理创建成功', { newInference })

      setDeductionChain(prev => prev ? {
        ...prev,
        inferences: [...prev.inferences, newInference],
        updatedAt: new Date().toISOString()
      } : null)

      setShowInferenceForm(false)
      setSelectedObservationIds([])
      setNewInferenceContent('')

      console.info('[DeductionBoard.tsx] 推理创建完成')
    } catch (err) {
      console.error('[DeductionBoard.tsx] 创建推理失败', err)
      setError('创建推理失败，请稍后重试')
    }
  }

  const toggleInferenceSelection = (inferenceId: string) => {
    console.debug('[DeductionBoard.tsx] 切换推理选择', { inferenceId })
    setSelectedInferenceIds(prev => {
      if (prev.includes(inferenceId)) {
        return prev.filter(id => id !== inferenceId)
      } else {
        return [...prev, inferenceId]
      }
    })
  }

  const startHypothesisCreation = () => {
    console.info('[DeductionBoard.tsx] 开始创建假设')
    setSelectedInferenceIds([])
    setShowHypothesisForm(true)
    setNewHypothesisTitle('')
    setNewHypothesisDescription('')
    setSelectedSuspectId(null)
  }

  const handleCreateHypothesis = async () => {
    if (!gameId || !newHypothesisTitle.trim() || !newHypothesisDescription.trim() || selectedInferenceIds.length === 0) return

    console.info('[DeductionBoard.tsx] 创建假设', {
      title: newHypothesisTitle,
      description: newHypothesisDescription,
      inferenceIds: selectedInferenceIds,
      suspectId: selectedSuspectId
    })

    try {
      const newHypothesis = await gameApi.createHypothesis(
        gameId,
        newHypothesisTitle.trim(),
        newHypothesisDescription.trim(),
        selectedInferenceIds,
        selectedSuspectId || undefined
      )

      console.debug('[DeductionBoard.tsx] 假设创建成功', { newHypothesis })

      setDeductionChain(prev => prev ? {
        ...prev,
        hypotheses: [...prev.hypotheses, newHypothesis],
        updatedAt: new Date().toISOString()
      } : null)

      setShowHypothesisForm(false)
      setSelectedInferenceIds([])
      setNewHypothesisTitle('')
      setNewHypothesisDescription('')
      setSelectedSuspectId(null)

      console.info('[DeductionBoard.tsx] 假设创建完成')
    } catch (err) {
      console.error('[DeductionBoard.tsx] 创建假设失败', err)
      setError('创建假设失败，请稍后重试')
    }
  }

  const handleDeleteInference = async (inferenceId: string) => {
    if (!gameId) return

    console.info('[DeductionBoard.tsx] 删除推理', { inferenceId })

    try {
      await gameApi.deleteInference(gameId, inferenceId)

      setDeductionChain(prev => prev ? {
        ...prev,
        inferences: prev.inferences.filter(i => i.id !== inferenceId),
        updatedAt: new Date().toISOString()
      } : null)

      console.info('[DeductionBoard.tsx] 推理删除完成')
    } catch (err) {
      console.error('[DeductionBoard.tsx] 删除推理失败', err)
      setError('删除推理失败，请稍后重试')
    }
  }

  const handleDeleteHypothesis = async (hypothesisId: string) => {
    if (!gameId) return

    console.info('[DeductionBoard.tsx] 删除假设', { hypothesisId })

    try {
      await gameApi.deleteHypothesis(gameId, hypothesisId)

      setDeductionChain(prev => prev ? {
        ...prev,
        hypotheses: prev.hypotheses.filter(h => h.id !== hypothesisId),
        updatedAt: new Date().toISOString()
      } : null)

      if (expandedHypothesisId === hypothesisId) {
        setExpandedHypothesisId(null)
      }

      console.info('[DeductionBoard.tsx] 假设删除完成')
    } catch (err) {
      console.error('[DeductionBoard.tsx] 删除假设失败', err)
      setError('删除假设失败，请稍后重试')
    }
  }

  const handleGetWatsonFeedback = async () => {
    if (!gameId || !deductionChain) return

    console.info('[DeductionBoard.tsx] 获取华生反馈')

    try {
      const feedback = await gameApi.getWatsonDeductionFeedback(
        gameId,
        deductionChain.inferences.map(i => i.id),
        deductionChain.hypotheses.map(h => h.id)
      )

      console.debug('[DeductionBoard.tsx] 华生反馈获取成功', { feedback })
      setWatsonFeedback(feedback)
      setShowWatsonFeedback(true)
    } catch (err) {
      console.error('[DeductionBoard.tsx] 获取华生反馈失败', err)
      setError('获取华生反馈失败，请稍后重试')
    }
  }

  const toggleHypothesisExpand = (hypothesisId: string) => {
    console.debug('[DeductionBoard.tsx] 切换假设展开', { hypothesisId })
    setExpandedHypothesisId(prev => prev === hypothesisId ? null : hypothesisId)
  }

  const startVerification = (hypothesisId: string, isVerified: boolean) => {
    console.info('[DeductionBoard.tsx] 开始验证假设', { hypothesisId, isVerified })
    setVerificationMode({ hypothesisId, isVerified })
    setVerificationNotes('')
  }

  const handleVerifyHypothesis = async () => {
    if (!gameId || !verificationMode) return

    console.info('[DeductionBoard.tsx] 验证假设', {
      hypothesisId: verificationMode.hypothesisId,
      isVerified: verificationMode.isVerified,
      notes: verificationNotes
    })

    try {
      const updatedHypothesis = await gameApi.verifyHypothesis(
        gameId,
        verificationMode.hypothesisId,
        verificationMode.isVerified,
        verificationNotes.trim() || undefined
      )

      console.debug('[DeductionBoard.tsx] 假设验证成功', { updatedHypothesis })

      setDeductionChain(prev => prev ? {
        ...prev,
        hypotheses: prev.hypotheses.map(h =>
          h.id === verificationMode.hypothesisId ? updatedHypothesis : h
        ),
        updatedAt: new Date().toISOString()
      } : null)

      setVerificationMode(null)
      setVerificationNotes('')

      console.info('[DeductionBoard.tsx] 假设验证完成')
    } catch (err) {
      console.error('[DeductionBoard.tsx] 验证假设失败', err)
      setError('验证假设失败，请稍后重试')
    }
  }

  const getSupportingEvidenceForHypothesis = (hypothesis: Hypothesis): string[] => {
    if (!deductionChain) return []
    const evidence: string[] = []
    for (const inference of deductionChain.inferences) {
      if (hypothesis.inferenceIds.includes(inference.id)) {
        evidence.push(...inference.supportingEvidence)
      }
    }
    return evidence
  }

  const getRelatedInferencesForHypothesis = (hypothesis: Hypothesis): Inference[] => {
    if (!deductionChain) return []
    return deductionChain.inferences.filter(i => hypothesis.inferenceIds.includes(i.id))
  }

  const selectedObservations = deductionChain?.observations.filter(o =>
    selectedObservationIds.includes(o.id)
  ) || []

  if (loading) {
    return (
      <div className="deduction-board loading">
        <div className="loading-spinner">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="deduction-board error">
        <div className="error-message">{error}</div>
        <button onClick={loadData}>重试</button>
      </div>
    )
  }

  return (
    <div className="deduction-board">
      <div className="deduction-board__header">
        <h1 className="deduction-board__title">演绎推理板</h1>
        <div className="deduction-board__nav">
          <Link to={`/investigation/${gameId}`} className="deduction-board__link">
            ← 返回现场勘查
          </Link>
          <Link to={`/interrogation/${gameId}`} className="deduction-board__link">
            审讯室 →
          </Link>
        </div>
      </div>

      <div className="deduction-board__content">
        <div className="deduction-board__sidebar">
          <h2 className="section-title">观察记录</h2>

          <div className="action-bar">
            {selectionMode === 'none' && (
              <button
                className="action-button"
                onClick={startObservationSelection}
                disabled={(deductionChain?.observations.length || 0) === 0}
              >
                选择观察创建推理
              </button>
            )}
          </div>

          {selectionMode === 'observations' && (
            <div className="selection-bar">
              <div className="selection-bar__text">
                已选择 {selectedObservationIds.length} 条观察记录
              </div>
              <div className="selection-bar__actions">
                <button
                  className="action-button"
                  onClick={confirmObservationSelection}
                  disabled={selectedObservationIds.length === 0}
                >
                  继续创建推理
                </button>
                <button
                  className="action-button action-button--secondary"
                  onClick={cancelSelection}
                >
                  取消
                </button>
              </div>
            </div>
          )}

          <div className="observations-list">
            {deductionChain?.observations.length === 0 ? (
              <div className="empty-state">
                暂无观察记录，请先在现场勘查中收集线索
              </div>
            ) : (
              deductionChain?.observations.map(observation => (
                <div
                  key={observation.id}
                  className={`observation-card ${
                    selectedObservationIds.includes(observation.id) ? 'observation-card--selected' : ''
                  }`}
                  onClick={() => selectionMode === 'observations' && toggleObservationSelection(observation.id)}
                >
                  <div className="observation-card__location">
                    📍 {observation.location}
                  </div>
                  <div className="observation-card__description">
                    {observation.description}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="deduction-board__main">
          {showWatsonFeedback && watsonFeedback && (
            <div className="watson-feedback">
              <h3 className="watson-feedback__title">华生的见解</h3>
              <div className="watson-feedback__content">
                {watsonFeedback.feedback}
              </div>
              {watsonFeedback.suggestions.length > 0 && (
                <ul className="watson-feedback__suggestions">
                  {watsonFeedback.suggestions.map((suggestion, index) => (
                    <li key={index} className="watson-feedback__suggestion">
                      {suggestion}
                    </li>
                  ))}
                </ul>
              )}
              <button
                className="action-button action-button--secondary"
                onClick={() => setShowWatsonFeedback(false)}
              >
                关闭
              </button>
            </div>
          )}

          {showInferenceForm && (
            <div className="form-container">
              <h3 className="form-title">创建新推理</h3>

              <div className="selected-items-preview">
                <div className="selected-items-title">基于以下观察：</div>
                {selectedObservations.map(observation => (
                  <div key={observation.id} className="selected-item">
                    • {observation.description}
                  </div>
                ))}
              </div>

              <div className="form-group">
                <label className="form-label">你的推理：</label>
                <textarea
                  className="form-textarea"
                  value={newInferenceContent}
                  onChange={(e) => setNewInferenceContent(e.target.value)}
                  placeholder="基于以上观察，你的推理是什么？"
                />
              </div>

              <div className="form-actions">
                <button
                  className="action-button"
                  onClick={handleCreateInference}
                  disabled={!newInferenceContent.trim()}
                >
                  创建推理
                </button>
                <button
                  className="action-button action-button--secondary"
                  onClick={() => {
                    setShowInferenceForm(false)
                    setSelectedObservationIds([])
                    setNewInferenceContent('')
                  }}
                >
                  取消
                </button>
              </div>
            </div>
          )}

          {showHypothesisForm && (
            <div className="form-container">
              <h3 className="form-title">创建新假设</h3>

              <div className="selected-items-preview">
                <div className="selected-items-title">请选择推理作为基础（可多选）：</div>
                {deductionChain?.inferences.length === 0 ? (
                  <div className="empty-state">暂无推理，请先创建推理</div>
                ) : (
                  deductionChain?.inferences.map(inference => (
                    <div
                      key={inference.id}
                      className={`selected-item ${
                        selectedInferenceIds.includes(inference.id) ? 'selected-item--selected' : ''
                      }`}
                      onClick={() => toggleInferenceSelection(inference.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      {selectedInferenceIds.includes(inference.id) ? '✓ ' : '○ '}
                      {inference.content}
                    </div>
                  ))
                )}
              </div>

              <div className="form-group">
                <label className="form-label">假设标题：</label>
                <input
                  className="form-input"
                  type="text"
                  value={newHypothesisTitle}
                  onChange={(e) => setNewHypothesisTitle(e.target.value)}
                  placeholder="简洁地描述这个假设"
                />
              </div>

              <div className="form-group">
                <label className="form-label">假设详情：</label>
                <textarea
                  className="form-textarea"
                  value={newHypothesisDescription}
                  onChange={(e) => setNewHypothesisDescription(e.target.value)}
                  placeholder="详细描述你的假设"
                />
              </div>

              <div className="form-group">
                <label className="form-label">关联嫌疑人（可选）：</label>
                <select
                  className="form-select"
                  value={selectedSuspectId || ''}
                  onChange={(e) => setSelectedSuspectId(e.target.value || null)}
                >
                  <option value="">不关联特定嫌疑人</option>
                  {gameState?.case?.suspects.map(suspect => (
                    <option key={suspect.id} value={suspect.id}>
                      {suspect.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-actions">
                <button
                  className="action-button"
                  onClick={handleCreateHypothesis}
                  disabled={!newHypothesisTitle.trim() || !newHypothesisDescription.trim() || selectedInferenceIds.length === 0}
                >
                  创建假设
                </button>
                <button
                  className="action-button action-button--secondary"
                  onClick={cancelSelection}
                >
                  取消
                </button>
              </div>
            </div>
          )}

          <div className="inferences-section">
            <div className="action-bar">
              <h2 className="section-title">推理节点</h2>
              <div style={{ marginLeft: 'auto' }}>
                <button
                  className="action-button"
                  onClick={startObservationSelection}
                  disabled={(deductionChain?.observations.length || 0) === 0}
                >
                  + 新建推理
                </button>
              </div>
            </div>

            <div className="inferences-grid">
              {deductionChain?.inferences.length === 0 ? (
                <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                  暂无推理节点，请选择观察记录开始推理
                </div>
              ) : (
                deductionChain?.inferences.map(inference => (
                  <div
                    key={inference.id}
                    className={`inference-card ${
                      selectedInferenceIds.includes(inference.id) ? 'inference-card--selected' : ''
                    }`}
                    onClick={() => showHypothesisForm && toggleInferenceSelection(inference.id)}
                  >
                    <div className="inference-card__header">
                      <span className="inference-card__confidence">
                        置信度: {Math.round(inference.confidence * 100)}%
                      </span>
                      <button
                        className="inference-card__delete"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteInference(inference.id)
                        }}
                      >
                        ×
                      </button>
                    </div>
                    <div className="inference-card__content">
                      {inference.content}
                    </div>
                    <div className="inference-card__sources">
                      基于 {inference.observationIds.length} 条观察
                      {inference.supportingEvidence.length > 0 && (
                        <div>支持证据: {inference.supportingEvidence.length} 条</div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="hypotheses-section">
            <div className="action-bar">
              <h2 className="section-title">假设</h2>
              <div style={{ marginLeft: 'auto' }}>
                <button
                  className="action-button"
                  onClick={startHypothesisCreation}
                  disabled={(deductionChain?.inferences.length || 0) === 0}
                >
                  + 新建假设
                </button>
                <button
                  className="action-button action-button--secondary"
                  onClick={handleGetWatsonFeedback}
                  disabled={!deductionChain || (deductionChain.inferences.length === 0 && deductionChain.hypotheses.length === 0)}
                >
                  🧐 咨询华生
                </button>
              </div>
            </div>

            {/* 逻辑缺口提示 */}
            {watsonFeedback?.logic_gaps && watsonFeedback.logic_gaps.length > 0 && (
              <div className="logic-gaps">
                <h3 className="logic-gaps__title">🔍 检测到的逻辑缺口</h3>
                <ul className="logic-gaps__list">
                  {watsonFeedback.logic_gaps.map((gap, index) => (
                    <li key={index} className="logic-gaps__item">
                      {gap.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="hypotheses-grid">
              {deductionChain?.hypotheses.length === 0 ? (
                <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                  暂无假设，请基于推理节点创建假设
                </div>
              ) : (
                deductionChain?.hypotheses.map(hypothesis => {
                  const relatedSuspect = gameState?.case?.suspects.find(
                    s => s.id === hypothesis.suspectId
                  )
                  const isExpanded = expandedHypothesisId === hypothesis.id
                  const supportingEvidence = getSupportingEvidenceForHypothesis(hypothesis)
                  const relatedInferences = getRelatedInferencesForHypothesis(hypothesis)
                  const isVerifying = verificationMode?.hypothesisId === hypothesis.id

                  return (
                    <div key={hypothesis.id} className={`hypothesis-card ${isExpanded ? 'hypothesis-card--expanded' : ''}`}>
                      <div className="hypothesis-card__header" onClick={() => toggleHypothesisExpand(hypothesis.id)}>
                        <div>
                          <div className="hypothesis-card__title">
                            {hypothesis.title}
                          </div>
                          {relatedSuspect && (
                            <div className="hypothesis-card__suspect">
                              嫌疑人: {relatedSuspect.name}
                            </div>
                          )}
                        </div>
                        <div className="hypothesis-card__actions">
                          <span className="hypothesis-card__expand-icon">
                            {isExpanded ? '▼' : '▶'}
                          </span>
                          <button
                            className="hypothesis-card__delete"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteHypothesis(hypothesis.id)
                            }}
                          >
                            ×
                          </button>
                        </div>
                      </div>
                      <div className="hypothesis-card__description">
                        {hypothesis.description}
                      </div>

                      {/* 展开内容 */}
                      {isExpanded && (
                        <div className="hypothesis-card__details">
                          {/* 支持证据 */}
                          {supportingEvidence.length > 0 && (
                            <div className="evidence-section">
                              <h4 className="evidence-section__title evidence-section__title--supporting">
                                ✓ 支持证据
                              </h4>
                              <ul className="evidence-list">
                                {supportingEvidence.map((evidence, idx) => (
                                  <li key={idx} className="evidence-item evidence-item--supporting">
                                    {evidence}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* 基于的推理 */}
                          <div className="evidence-section">
                            <h4 className="evidence-section__title">📊 基于的推理</h4>
                            <ul className="evidence-list">
                              {relatedInferences.map((inference) => (
                                <li key={inference.id} className="evidence-item">
                                  {inference.content}
                                  <span className="evidence-item__confidence">
                                    (置信度: {Math.round(inference.confidence * 100)}%)
                                  </span>
                                </li>
                              ))}
                            </ul>
                          </div>

                          {/* 验证状态 */}
                          {!isVerifying ? (
                            <div className="verification-section">
                              <h4 className="verification-section__title">验证状态</h4>
                              <div className={`hypothesis-card__status hypothesis-card__status--large ${
                                hypothesis.isVerified
                                  ? 'hypothesis-card__status--verified'
                                  : 'hypothesis-card__status--unverified'
                              }`}>
                                {hypothesis.isVerified ? '✓ 已验证' : '○ 待验证'}
                              </div>
                              {hypothesis.verificationNotes && (
                                <div className="verification-notes">
                                  <strong>验证笔记:</strong> {hypothesis.verificationNotes}
                                </div>
                              )}
                              <div className="verification-actions">
                                <button
                                  className="action-button action-button--small"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    startVerification(hypothesis.id, true)
                                  }}
                                >
                                  ✓ 标记为已验证
                                </button>
                                <button
                                  className="action-button action-button--small action-button--secondary"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    startVerification(hypothesis.id, false)
                                  }}
                                >
                                  ✗ 标记为未验证
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="verification-form">
                              <h4 className="verification-form__title">
                                {verificationMode.isVerified ? '验证假设' : '撤销验证'}
                              </h4>
                              <textarea
                                className="form-textarea"
                                value={verificationNotes}
                                onChange={(e) => setVerificationNotes(e.target.value)}
                                placeholder="添加验证笔记（可选）"
                                onClick={(e) => e.stopPropagation()}
                              />
                              <div className="verification-form__actions">
                                <button
                                  className="action-button action-button--small"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleVerifyHypothesis()
                                  }}
                                >
                                  确认
                                </button>
                                <button
                                  className="action-button action-button--small action-button--secondary"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setVerificationMode(null)
                                    setVerificationNotes('')
                                  }}
                                >
                                  取消
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {!isExpanded && (
                        <>
                          <div className="hypothesis-card__sources">
                            基于 {hypothesis.inferenceIds.length} 条推理
                            {supportingEvidence.length > 0 && ` · ${supportingEvidence.length} 条支持证据`}
                          </div>
                          <div className={`hypothesis-card__status ${
                            hypothesis.isVerified
                              ? 'hypothesis-card__status--verified'
                              : 'hypothesis-card__status--unverified'
                          }`}>
                            {hypothesis.isVerified ? '✓ 已验证' : '○ 待验证'}
                            {hypothesis.supportScore > 0 && ` · 支持度: ${hypothesis.supportScore.toFixed(1)}`}
                          </div>
                        </>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DeductionBoard
