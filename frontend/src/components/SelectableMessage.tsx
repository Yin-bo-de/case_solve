import { useState } from 'react'

interface TooltipPos {
  x: number
  y: number
}

interface Props {
  text: string
  senderName?: string
  onExtract: (selectedText: string) => void
}

export function SelectableMessage({ text, senderName, onExtract }: Props) {
  const [selection, setSelection] = useState('')
  const [tooltipPos, setTooltipPos] = useState<TooltipPos | null>(null)

  const handleMouseUp = () => {
    const sel = window.getSelection()
    const t = sel?.toString().trim() ?? ''
    if (t.length > 5) {
      const range = sel!.getRangeAt(0).getBoundingClientRect()
      setSelection(t)
      setTooltipPos({ x: range.left, y: range.top - 36 })
    } else {
      setSelection('')
      setTooltipPos(null)
    }
  }

  const handleExtract = () => {
    if (selection) {
      onExtract(selection)
      setSelection('')
      setTooltipPos(null)
      window.getSelection()?.removeAllRanges()
    }
  }

  return (
    <div className="selectable-message" onMouseUp={handleMouseUp}>
      {senderName && <div className="message-sender">{senderName}</div>}
      <p className="message-text selectable-message__text">{text}</p>
      {tooltipPos && (
        <button
          className="extract-clue-tooltip"
          style={{ position: 'fixed', left: tooltipPos.x, top: tooltipPos.y }}
          onClick={handleExtract}
          type="button"
          onMouseDown={(e) => e.preventDefault()}
        >
          📎 生成线索
        </button>
      )}
    </div>
  )
}
