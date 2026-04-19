import { useState } from 'react'
import type { Suspect, ReasoningRecord } from '@/types/game'

interface Props {
  suspects: Suspect[]
  records: ReasoningRecord[]  // 仅 correct 的推理记录
  onSubmit: (suspectId: string, recordIds: string[]) => Promise<void>
  onClose: () => void
}

export default function AccusationModal({ suspects, records, onSubmit, onClose }: Props) {
  const [suspectId, setSuspectId] = useState('')
  const [selectedRecordIds, setSelectedRecordIds] = useState<string[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const toggleRecord = (id: string) => {
    setSelectedRecordIds((prev) =>
      prev.includes(id)
        ? prev.filter((r) => r !== id)
        : prev.length < 3
        ? [...prev, id]
        : prev
    )
  }

  const canSubmit =
    suspectId &&
    selectedRecordIds.length >= 1 &&
    selectedRecordIds.length <= 3 &&
    !isSubmitting

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return
    setIsSubmitting(true)
    setError(null)
    try {
      await onSubmit(suspectId, selectedRecordIds)
    } catch (err) {
      console.error('[AccusationModal] 指认失败', err)
      setError('指认失败，请稍后再试')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal accusation-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>🔍 指认凶手</h3>
          <button className="modal-close" onClick={onClose} type="button">×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label" htmlFor="suspect-select">选择你要指认的嫌疑人</label>
              <select
                id="suspect-select"
                className="form-select"
                value={suspectId}
                onChange={(e) => setSuspectId(e.target.value)}
              >
                <option value="">-- 请选择 --</option>
                {suspects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                选择 1-3 条推理记录作为指控依据
                <span className="accusation-modal__record-count">（已选 {selectedRecordIds.length}/3）</span>
              </label>
              {records.length === 0 ? (
                <p className="accusation-modal__no-records">
                  尚无已验证正确的推理记录，请先在推理板提交推理。
                </p>
              ) : (
                <ul className="accusation-modal__records">
                  {records.map((r) => (
                    <li
                      key={r.id}
                      className={`accusation-modal__record-item ${selectedRecordIds.includes(r.id) ? 'selected' : ''}`}
                      onClick={() => toggleRecord(r.id)}
                    >
                      <span className="accusation-modal__record-check">
                        {selectedRecordIds.includes(r.id) ? '✓' : '○'}
                      </span>
                      <span className="accusation-modal__record-content">{r.content}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {error && <p className="form-error">{error}</p>}
          </div>
          <div className="modal-footer">
            <button
              type="submit"
              className="action-button action-button--danger"
              disabled={!canSubmit}
            >
              {isSubmitting ? '正在宣判…' : '确认指认'}
            </button>
            <button
              type="button"
              className="action-button action-button--secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              再想想
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
