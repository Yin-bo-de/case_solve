import { useEffect, useRef, useState } from 'react'

interface TypewriterProps {
  text: string
  speed?: number
  onDone?: () => void
  className?: string
}

/**
 * 逐字打字机组件。点击容器可立即跳到全文，避免长文本等待。
 */
export default function Typewriter({ text, speed = 35, onDone, className }: TypewriterProps) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const indexRef = useRef(0)
  const onDoneRef = useRef(onDone)
  onDoneRef.current = onDone

  useEffect(() => {
    console.debug('[Typewriter] mount', { length: text.length })
    setDisplayed('')
    setDone(false)
    indexRef.current = 0

    intervalRef.current = setInterval(() => {
      indexRef.current += 1
      const next = text.slice(0, indexRef.current)
      setDisplayed(next)

      if (indexRef.current >= text.length) {
        clearInterval(intervalRef.current!)
        intervalRef.current = null
        setDone(true)
        console.debug('[Typewriter] done', { length: text.length })
        onDoneRef.current?.()
      }
    }, speed)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [text, speed])

  const skipToEnd = () => {
    if (done) return
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setDisplayed(text)
    setDone(true)
    console.debug('[Typewriter] done (skipped)', { length: text.length })
    onDoneRef.current?.()
  }

  return (
    <span
      className={className}
      onClick={skipToEnd}
      style={{ cursor: done ? 'default' : 'pointer' }}
    >
      {displayed}
    </span>
  )
}
