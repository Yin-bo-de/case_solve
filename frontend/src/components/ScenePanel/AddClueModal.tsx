import { useState } from 'react'

interface Props {
  defaultLabel?: string
  defaultDescription?: string
  onConfirm: (userLabel: string) => void
  onClose: () => void
}

export default function AddClueModal({ defaultLabel = '', defaultDescription = '', onConfirm, onClose }: Props) {
  const [userLabel, setUserLabel] = useState(defaultLabel)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!userLabel.trim()) return
    onConfirm(userLabel.trim())
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal add-clue-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>📎 添加为线索</h3>
          <button className="modal-close" onClick={onClose} type="button">×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {defaultDescription && (
              <div className="add-clue-modal__hint">
                <span className="add-clue-modal__hint-label">线索内容：</span>
                <p className="add-clue-modal__hint-text">{defaultDescription}</p>
              </div>
            )}
            <div className="form-group">
              <label className="form-label" htmlFor="clue-label">
                线索命名 <span className="required">*</span>
              </label>
              <input
                id="clue-label"
                className="form-input"
                type="text"
                value={userLabel}
                onChange={(e) => setUserLabel(e.target.value)}
                placeholder="例如：书房毒酒"
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
              确认添加
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
