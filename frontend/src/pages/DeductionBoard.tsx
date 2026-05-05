import { useState, useMemo, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useDeductionStore, useCluesStore, useGameStore } from '@/store'
import ReasoningRecordCard from '@/components/ReasoningRecordCard'
import { useGameSessionSync } from '@/hooks/useGameSessionSync'
import CombineReasoningModal from '@/components/CombineReasoningModal'
import AccusationModal from '@/components/AccusationModal'
import WatsonChatDialog from '@/components/WatsonChatDialog'
import CluePreviewModal from '@/components/CluePreviewModal'

console.debug('[DeductionBoard.tsx] 加载模块')

export default function DeductionBoard() {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()

  const {
    reasoningRecords,
    selectedClueIds,
    filter,
    toggleClue,
    setFilter,
    submitReasoning,
    markImportant,
    deleteRecord,
    accuse,
  } = useDeductionStore()

  const { clues } = useCluesStore()
  const { gameState, isLoading, error } = useGameStore()

  const [showCombineModal, setShowCombineModal] = useState(false)
  const [showAccuseModal, setShowAccuseModal] = useState(false)
  const [previewedClueId, setPreviewedClueId] = useState<string | null>(null)

  console.debug('[DeductionBoard.tsx] 渲染', { gameId, clueCount: clues.length, recordCount: reasoningRecords.length })

  useGameSessionSync(gameId)

  const filteredRecords = useMemo(() => {
    if (filter === 'all') return reasoningRecords
    return reasoningRecords.filter((r) => r.verificationResult === filter)
  }, [reasoningRecords, filter])

  const correctRecords = useMemo(
    () => reasoningRecords.filter((r) => r.verificationResult === 'correct'),
    [reasoningRecords]
  )

  const canAccuse = correctRecords.length > 0
  const selectedClues = useMemo(
    () => clues.filter((c) => selectedClueIds.includes(c.id)),
    [clues, selectedClueIds]
  )

  const previewedClue = useMemo(
    () => clues.find((c) => c.id === previewedClueId) ?? null,
    [clues, previewedClueId]
  )

  const handleSubmitReasoning = useCallback(
    async (conclusion: string) => {
      if (!gameId) return
      await submitReasoning(gameId, selectedClueIds, conclusion)
      setShowCombineModal(false)
    },
    [gameId, selectedClueIds, submitReasoning]
  )

  const handleAccuse = useCallback(
    async (suspectId: string, recordIds: string[]) => {
      if (!gameId) return
      const result = await accuse(gameId, suspectId, recordIds)
      setShowAccuseModal(false)
      navigate(`/conclusion/${gameId}`, { state: { accusationResult: result } })
    },
    [gameId, accuse, navigate]
  )

  if (isLoading) {
    return (
      <div className="deduction-board deduction-board--loading">
        <div className="loading-spinner">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="deduction-board deduction-board--error">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate(`/investigation/${gameId}`)}>返回勘查</button>
      </div>
    )
  }

  return (
    <div className="deduction-board">
      <header className="deduction-board__header">
        <h1 className="deduction-board__title">演绎推理板</h1>
        <div className="deduction-board__nav">
          <Link to={`/investigation/${gameId}`} className="deduction-board__link">← 返回勘查</Link>
          <Link to={`/interrogation/${gameId}`} className="deduction-board__link">审讯室 →</Link>
        </div>
      </header>

      <div className="deduction-board__content">
        {/* 左栏：线索列表 */}
        <aside className="deduction-board__clues">
          <h2 className="deduction-board__section-title">📋 线索列表</h2>
          {clues.length === 0 ? (
            <p className="deduction-board__empty">
              尚无线索，请先在场景中探查或审讯嫌疑人。
            </p>
          ) : (
            <ul className="clue-list clue-list--deduction">
              {clues.map((c) => (
                <li
                  key={c.id}
                  className={`clue-item clue-item--deduction ${selectedClueIds.includes(c.id) ? 'clue-item--selected' : ''} ${previewedClueId === c.id ? 'clue-item--previewed' : ''}`}
                  onClick={() => setPreviewedClueId(c.id)}
                >
                  <span
                    className="clue-item__check"
                    onClick={(e) => { e.stopPropagation(); toggleClue(c.id) }}
                  >
                    {selectedClueIds.includes(c.id) ? '☑' : '☐'}
                  </span>
                  <span className="clue-item__label">
                    {c.userLabel || c.description.substring(0, 30)}
                  </span>
                  <span className="clue-item__source">
                    {c.sourceType === 'scene' ? '📍' : c.sourceType === 'interrogation' ? '🗣' : '📋'}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <div className="deduction-board__clues-footer">
            <span>已选 {selectedClueIds.length} 条</span>
            <button
              className="action-button"
              disabled={selectedClueIds.length === 0}
              onClick={() => setShowCombineModal(true)}
              type="button"
            >
              ✨ 组合推理
            </button>
          </div>
        </aside>

        {/* 主栏：推理记录 */}
        <main className="deduction-board__records">
          <header className="deduction-board__records-header">
            <h2 className="deduction-board__section-title">📝 推理记录</h2>
            {/* P4: 推理类型统计条 */}
            <div className="stats-bar">
              <div className="stat-item">
                <span className="font-semibold text-blue-700">事实推理</span>
                <span className="text-2xl font-bold text-blue-900">
                  {reasoningRecords.filter((r) => r.nodeType === 'fact').length}
                </span>
              </div>
              <div className="stat-item">
                <span className="font-semibold text-purple-700">对质推理</span>
                <span className="text-2xl font-bold text-purple-900">
                  {reasoningRecords.filter((r) => r.nodeType === 'interrogation').length}
                </span>
              </div>
              <div className="stat-item">
                <span className="font-semibold text-gray-700">混合推理</span>
                <span className="text-2xl font-bold text-gray-900">
                  {reasoningRecords.filter((r) => r.nodeType === 'mixed').length}
                </span>
              </div>
            </div>
            <div className="filter-tabs">
              {(['all', 'correct', 'wrong'] as const).map((f) => (
                <button
                  key={f}
                  className={`filter-tab ${filter === f ? 'filter-tab--active' : ''}`}
                  onClick={() => setFilter(f)}
                  type="button"
                >
                  {f === 'all' ? '全部' : f === 'correct' ? '✅ 正确' : '❌ 错误'}
                  {f !== 'all' && (
                    <span className="filter-tab__count">
                      {reasoningRecords.filter((r) => r.verificationResult === f).length}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </header>

          {filteredRecords.length === 0 ? (
            <div className="deduction-board__records-empty">
              {filter === 'all'
                ? '尚无推理记录。选择线索后点击"✨ 组合推理"开始。'
                : `无${filter === 'correct' ? '正确' : '错误'}推理记录。`}
            </div>
          ) : (
            <ul className="reasoning-records-list">
              {filteredRecords.map((r, i) => (
                <li key={r.id}>
                  <ReasoningRecordCard
                    index={filteredRecords.length - i}
                    record={r}
                    clues={clues}
                    onMarkImportant={() => markImportant(r.id)}
                    onDelete={() => gameId && deleteRecord(gameId, r.id)}
                  />
                </li>
              ))}
            </ul>
          )}
        </main>
      </div>

      {/* 指认凶手浮动按钮 */}
      <button
        className={`deduction-board__accuse-fab ${canAccuse ? 'deduction-board__accuse-fab--active' : ''}`}
        disabled={!canAccuse}
        onClick={() => setShowAccuseModal(true)}
        type="button"
        title={canAccuse ? '点击指认凶手' : '需要至少一条正确推理记录'}
      >
        🔍 指认凶手
      </button>

      {showCombineModal && (
        <CombineReasoningModal
          selectedClues={selectedClues}
          onClose={() => setShowCombineModal(false)}
          onSubmit={handleSubmitReasoning}
        />
      )}

      {showAccuseModal && gameState?.case && gameId && (
        <AccusationModal
          gameId={gameId}
          suspects={gameState.case.suspects}
          records={correctRecords}
          onSubmit={handleAccuse}
          onClose={() => setShowAccuseModal(false)}
        />
      )}

      <WatsonChatDialog gameId={gameId!} />

      {previewedClue && (
        <CluePreviewModal
          clue={previewedClue}
          onClose={() => setPreviewedClueId(null)}
        />
      )}
    </div>
  )
}
