import { useState } from 'react'

interface Props {
  quotedText: string
  onConfirm: (userLabel: string) => void
  onClose: () => void
}

export default function ExtractClueModal({ quotedText, onConfirm, onClose }: Props) {
  const [userLabel, setUserLabel] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!userLabel.trim()) return
    onConfirm(userLabel.trim())
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal extract-clue-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>📎 从审讯提取线索</h3>
          <button className="modal-close" onClick={onClose} type="button">×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="extract-clue-modal__quoted">
              <span className="extract-clue-modal__quoted-label">引用片段：</span>
              <blockquote className="extract-clue-modal__quote">"{quotedText}"</blockquote>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="extract-label">
                线索命名 <span className="required">*</span>
              </label>
              <input
                id="extract-label"
                className="form-input"
                type="text"
                value={userLabel}
                onChange={(e) => setUserLabel(e.target.value)}
                placeholder="例如：管家的不在场证明"
                autoFocus
              />
            </div>
          </div>
          <div className="modal-footer">
            <button
              type="submit"
              className="action-button"
              disabled={!userLabel.trim()}
            >
              保存线索
            </button>
            <button type="button" className="action-button action-button--secondary" onClick={onClose}>
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
