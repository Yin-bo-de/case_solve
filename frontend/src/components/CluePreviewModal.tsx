import type { Clue } from '@/types/game'

interface Props {
  clue: Clue
  onClose: () => void
}

const CLUE_TYPE_MAP: Record<string, string> = {
  physical: '🔍 物证',
  testimonial: '🗣 证词',
  forensic: '🧪 法医',
}

const SOURCE_TYPE_MAP: Record<string, string> = {
  scene: '📍 场景勘查',
  interrogation: '🗣 审讯',
  initial: '📋 初始线索',
}

const VERIFICATION_STATUS_MAP: Record<string, { label: string; className: string }> = {
  verified: { label: '✅ 已验证', className: 'clue-preview-badge--verified' },
  refuted: { label: '❌ 已被驳斥', className: 'clue-preview-badge--refuted' },
  unverified: { label: '⚪ 未验证', className: 'clue-preview-badge--unverified' },
}

export default function CluePreviewModal({ clue, onClose }: Props) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal clue-preview-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{clue.userLabel || clue.description.substring(0, 30)}</h3>
          <button className="modal-close" onClick={onClose} type="button">×</button>
        </div>
        <div className="modal-body clue-preview-modal__body">
          {/* 完整描述 */}
          <div className="clue-preview-field">
            <span className="clue-preview-field__label">完整描述</span>
            <p className="clue-preview-field__value">{clue.description}</p>
          </div>

          {/* 验证状态 */}
          {clue.verificationStatus && (
            <div className="clue-preview-field">
              <span className="clue-preview-field__label">验证状态</span>
              <span className={`clue-preview-badge ${VERIFICATION_STATUS_MAP[clue.verificationStatus]?.className || ''}`}>
                {VERIFICATION_STATUS_MAP[clue.verificationStatus]?.label || clue.verificationStatus}
              </span>
            </div>
          )}

          {/* 线索类型 */}
          <div className="clue-preview-field">
            <span className="clue-preview-field__label">线索类型</span>
            <span className="clue-preview-field__value">
              {CLUE_TYPE_MAP[clue.clueType] ?? clue.clueType}
            </span>
          </div>

          {/* 发现地点 */}
          {clue.location && (
            <div className="clue-preview-field">
              <span className="clue-preview-field__label">发现地点</span>
              <span className="clue-preview-field__value">{clue.location}</span>
            </div>
          )}

          {/* 来源 */}
          {clue.sourceType && (
            <div className="clue-preview-field">
              <span className="clue-preview-field__label">来源</span>
              <span className="clue-preview-field__value">
                {SOURCE_TYPE_MAP[clue.sourceType] ?? clue.sourceType}
                {clue.sourceRef && ` — ${clue.sourceRef}`}
              </span>
            </div>
          )}

          {/* 引用原文 */}
          {clue.quotedText && (
            <div className="clue-preview-field">
              <span className="clue-preview-field__label">引用原文</span>
              <blockquote className="clue-preview-quote">
                &ldquo;{clue.quotedText}&rdquo;
              </blockquote>
            </div>
          )}

          {/* 发现记录 */}
          {clue.discoveryNotes && (
            <div className="clue-preview-field">
              <span className="clue-preview-field__label">发现记录</span>
              <p className="clue-preview-field__value clue-preview-field__value--notes">
                {clue.discoveryNotes}
              </p>
            </div>
          )}

          {/* 验证备注 */}
          {clue.verificationNotes && (
            <div className="clue-preview-field">
              <span className="clue-preview-field__label">验证备注</span>
              <p className="clue-preview-field__value clue-preview-field__value--notes">
                {clue.verificationNotes}
              </p>
            </div>
          )}

          {/* 验证来源 */}
          {clue.verifiedBy && (
            <div className="clue-preview-field">
              <span className="clue-preview-field__label">验证来源</span>
              <span className="clue-preview-field__value">{clue.verifiedBy}</span>
            </div>
          )}

          {/* Meta badges */}
          {clue.userGenerated && (
            <div className="clue-preview-meta">
              <span className="clue-preview-badge clue-preview-badge--user">🧑 用户线索</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
