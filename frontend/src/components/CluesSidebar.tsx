import { useState } from 'react'
import { useCluesStore } from '@/store'
import CluePreviewModal from '@/components/CluePreviewModal'
import type { Clue } from '@/types/game'

interface CluesSidebarProps {
  title?: string
  emptyHint?: string
  className?: string
}

const SOURCE_EMOJI: Record<NonNullable<Clue['sourceType']>, string> = {
  scene: '📍',
  interrogation: '🗣',
  witness: '🗣',
  expert: '🔬',
  initial: '📋',
}

const VERIFICATION_BADGE: Record<NonNullable<Clue['verificationStatus']>, string> = {
  verified: '✓',
  refuted: '✗',
  unverified: '⚠️',
}

export default function CluesSidebar({
  title = '📋 线索列表',
  emptyHint = '尚无线索，请先在场景中探查或审讯嫌疑人。',
  className,
}: CluesSidebarProps) {
  const { clues } = useCluesStore()
  const [previewedClue, setPreviewedClue] = useState<Clue | null>(null)

  return (
    <div className={`clues-sidebar${className ? ` ${className}` : ''}`}>
      <h3 className="clues-sidebar__title">{title}</h3>

      {clues.length === 0 ? (
        <p className="clues-sidebar__empty">{emptyHint}</p>
      ) : (
        <ul className="clue-list--deduction clues-sidebar__list">
          {clues.map((clue) => {
            const sourceEmoji = clue.sourceType ? (SOURCE_EMOJI[clue.sourceType] ?? '📋') : '📋'
            const verBadge = clue.verificationStatus
              ? VERIFICATION_BADGE[clue.verificationStatus]
              : null
            const label = clue.userLabel || clue.description.substring(0, 30)

            return (
              <li
                key={clue.id}
                className={`clue-item--deduction${previewedClue?.id === clue.id ? ' clue-item--previewed' : ''}`}
                onClick={() => setPreviewedClue(clue)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && setPreviewedClue(clue)}
              >
                <span className="clue-item__source">{sourceEmoji}</span>
                <span className="clue-item__label">{label}</span>
                {verBadge && (
                  <span className="clue-item__verification">{verBadge}</span>
                )}
              </li>
            )
          })}
        </ul>
      )}

      {previewedClue && (
        <CluePreviewModal clue={previewedClue} onClose={() => setPreviewedClue(null)} />
      )}
    </div>
  )
}
