import { useState } from 'react'
import type { Clue } from '@/types/game'

interface Props {
  selectedClues: Clue[]
  onClose: () => void
  onSubmit: (conclusion: string) => Promise<void>
}

export default function CombineReasoningModal({ selectedClues, onClose, onSubmit }: Props) {
  const [conclusion, setConclusion] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!conclusion.trim() || isSubmitting) return
    setIsSubmitting(true)
    setError(null)
    try {
      await onSubmit(conclusion.trim())
    } catch (err) {
      console.error('[CombineReasoningModal] 提交推理失败', err)
      setError('提交失败，请稍后再试')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal combine-reasoning-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>✨ 组合推理</h3>
          <button className="modal-close" onClick={onClose} type="button">×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="combine-reasoning-modal__clues">
              <p className="combine-reasoning-modal__clues-title">基于以下 {selectedClues.length} 条线索：</p>
              <ul>
                {selectedClues.map((c) => (
                  <li key={c.id} className="combine-reasoning-modal__clue-item">
                    📎 {c.userLabel || c.description.substring(0, 40)}
                  </li>
                ))}
              </ul>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="conclusion-input">
                你的推理结论 <span className="required">*</span>
              </label>
              <textarea
                id="conclusion-input"
                className="form-textarea"
                value={conclusion}
                onChange={(e) => setConclusion(e.target.value)}
                placeholder="根据以上线索，你推断出……"
                rows={4}
                autoFocus
              />
            </div>
            {error && <p className="form-error">{error}</p>}
          </div>
          <div className="modal-footer">
            <button
              type="submit"
              className="action-button"
              disabled={!conclusion.trim() || isSubmitting}
            >
              {isSubmitting ? '裁决官审核中…' : '提交推理'}
            </button>
            <button
              type="button"
              className="action-button action-button--secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
