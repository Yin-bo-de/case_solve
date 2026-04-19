import type { WatsonTip } from '@/types/game'

interface Props {
  tips: WatsonTip[]
  isLoading: boolean
}

const TYPE_ICON: Record<string, string> = {
  suggestion: '💡',
  contradiction: '⚠️',
  question_template: '❓',
}

export default function WatsonTipsPanel({ tips, isLoading }: Props) {
  if (!isLoading && tips.length === 0) return null

  return (
    <aside className="watson-tips-panel">
      <div className="watson-tips-panel__header">
        <span className="watson-tips-panel__avatar">👨‍⚕️</span>
        <h3 className="watson-tips-panel__title">华生的提示</h3>
      </div>
      {isLoading ? (
        <div className="watson-tips-panel__loading">华生正在思考…</div>
      ) : (
        <ul className="watson-tips-panel__list">
          {tips.map((tip, i) => (
            <li key={i} className={`watson-tips-panel__item watson-tips-panel__item--${tip.type}`}>
              <span className="watson-tips-panel__icon">{TYPE_ICON[tip.type] ?? '🔍'}</span>
              <span className="watson-tips-panel__text">{tip.text}</span>
            </li>
          ))}
        </ul>
      )}
    </aside>
  )
}
