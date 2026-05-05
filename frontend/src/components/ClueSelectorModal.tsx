import { useState, useMemo } from 'react'
import type { Clue } from '@/types/game'

interface Props {
  clues: Clue[]
  onSelect: (clueId: string, clueLabel: string) => void
  onClose: () => void
}

const STATUS_BADGE_CLASS: Record<string, string> = {
  verified: 'clue-status-badge--verified',
  refuted: 'clue-status-badge--refuted',
  unverified: 'clue-status-badge--unverified',
}

const STATUS_LABEL: Record<string, string> = {
  verified: '已验证',
  refuted: '被驳斥',
  unverified: '未验证',
}

export default function ClueSelectorModal({ clues, onSelect, onClose }: Props) {
  const [selectedClueId, setSelectedClueId] = useState<string | null>(null)

  const discoveredClues = useMemo(
    () => clues.filter((c) => c.discovered || c.userGenerated),
    [clues]
  )

  const selectedClue = discoveredClues.find((c) => c.id === selectedClueId)

  const handleConfirm = () => {
    if (!selectedClue) return
    const label = selectedClue.userLabel || selectedClue.description.substring(0, 30)
    onSelect(selectedClue.id, label)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal clue-selector-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>出示线索</h3>
          <button className="modal-close" onClick={onClose} type="button">
            ×
          </button>
        </div>
        <div className="modal-body clue-selector-modal__body">
          {discoveredClues.length === 0 ? (
            <p className="clue-selector-empty">尚未发现任何线索。</p>
          ) : (
            <ul className="clue-selector-list">
              {discoveredClues.map((clue) => {
                const status = clue.verificationStatus || 'unverified'
                const isSelected = selectedClueId === clue.id
                return (
                  <li
                    key={clue.id}
                    className={`clue-selector-item ${isSelected ? 'clue-selector-item--selected' : ''}`}
                    onClick={() => setSelectedClueId(clue.id)}
                  >
                    <div className="clue-selector-item__label">
                      {clue.userLabel || clue.description.substring(0, 40)}
                    </div>
                    <span className={`clue-status-badge ${STATUS_BADGE_CLASS[status] || ''}`}>
                      {STATUS_LABEL[status] || status}
                    </span>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
        <div className="modal-footer clue-selector-modal__footer">
          <button className="modal-btn modal-btn--secondary" onClick={onClose} type="button">
            取消
          </button>
          <button
            className="modal-btn modal-btn--primary"
            onClick={handleConfirm}
            disabled={!selectedClueId}
            type="button"
          >
            确认出示
          </button>
        </div>
      </div>
    </div>
  )
}
