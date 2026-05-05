import type { ReasoningRecord, Clue } from '@/types/game'

interface Props {
  index: number
  record: ReasoningRecord
  clues: Clue[]
  onMarkImportant: () => void
  onDelete: () => void
}

const VERDICT_BADGE: Record<string, { icon: string; label: string; className: string }> = {
  correct:  { icon: '✅', label: '正确',   className: 'verdict-badge--correct'  },
  wrong:    { icon: '❌', label: '错误',   className: 'verdict-badge--wrong'    },
  partial:  { icon: '⚠️', label: '部分正确', className: 'verdict-badge--partial' },
}

// P4: 推理节点类型
const NODE_TYPE_BADGE: Record<string, { label: string; className: string }> = {
  fact:          { label: '基于事实', className: 'node-type-badge--fact' },
  interrogation: { label: '基于对质', className: 'node-type-badge--interrogation' },
  mixed:         { label: '混合推理', className: 'node-type-badge--mixed' },
}

export default function ReasoningRecordCard({ index, record, clues, onMarkImportant, onDelete }: Props) {
  const badge = record.verificationResult ? VERDICT_BADGE[record.verificationResult] : null
  const nodeTypeBadge = record.nodeType ? NODE_TYPE_BADGE[record.nodeType] : null
  const relatedClues = clues.filter((c) => record.clueIds?.includes(c.id))

  return (
    <div className={`reasoning-record-card ${record.userMarkedImportant ? 'reasoning-record-card--important' : ''}`}>
      <div className="reasoning-record-card__header">
        <span className="reasoning-record-card__index">#{index}</span>
        {nodeTypeBadge && (
          <span className={`node-type-badge ${nodeTypeBadge.className}`}>
            {nodeTypeBadge.label}
          </span>
        )}
        {badge && (
          <span className={`verdict-badge ${badge.className}`}>
            {badge.icon} {badge.label}
          </span>
        )}
        <div className="reasoning-record-card__actions">
          <button
            className={`reasoning-record-card__action-btn ${record.userMarkedImportant ? 'active' : ''}`}
            onClick={onMarkImportant}
            title="标记重要"
            type="button"
          >
            ⭐
          </button>
          <button
            className="reasoning-record-card__action-btn reasoning-record-card__action-btn--delete"
            onClick={onDelete}
            title="删除"
            type="button"
          >
            🗑
          </button>
        </div>
      </div>

      {/* 关联线索 chip */}
      {relatedClues.length > 0 && (
        <div className="reasoning-record-card__clues">
          {relatedClues.map((c) => (
            <span key={c.id} className="clue-chip">{c.userLabel || c.description.substring(0, 20)}</span>
          ))}
        </div>
      )}

      <p className="reasoning-record-card__content">{record.content}</p>

      {record.oracleExplanation && (
        <div className="reasoning-record-card__explanation">
          <span className="reasoning-record-card__explanation-label">裁决官：</span>
          {record.oracleExplanation}
        </div>
      )}

      <div className="reasoning-record-card__footer">
        <span className="reasoning-record-card__time">
          {new Date(record.createdAt).toLocaleTimeString()}
        </span>
        <span className="reasoning-record-card__score">
          得分：{Math.round(record.confidence * 100)}%
        </span>
      </div>
    </div>
  )
}
