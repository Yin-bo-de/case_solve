import type { SceneObject } from '@/types/game'

interface Props {
  object: SceneObject
  onClick: (obj: SceneObject) => void
}

export default function SceneObjectCard({ object, onClick }: Props) {
  return (
    <button
      className="scene-object-card"
      onClick={() => onClick(object)}
      type="button"
    >
      <div className="scene-object-card__name">{object.name}</div>
      <div className="scene-object-card__desc">{object.description}</div>
      {object.hiddenClueIds.length > 0 && (
        <span className="scene-object-card__badge">🔍</span>
      )}
    </button>
  )
}
