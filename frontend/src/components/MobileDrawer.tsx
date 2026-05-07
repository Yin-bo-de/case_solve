import { useEffect, useCallback } from 'react'
import './MobileDrawer.css'

interface MobileDrawerProps {
  open: boolean
  onClose: () => void
  position?: 'bottom' | 'right' | 'left'
  height?: string
  title?: string
  children: React.ReactNode
}

export default function MobileDrawer({
  open,
  onClose,
  position = 'bottom',
  height = '70dvh',
  title,
  children,
}: MobileDrawerProps) {
  const handleEsc = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    },
    [onClose]
  )

  useEffect(() => {
    if (open) {
      document.addEventListener('keydown', handleEsc)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = ''
    }
  }, [open, handleEsc])

  if (!open) return null

  return (
    <>
      <div className="mobile-drawer__backdrop" onClick={onClose} />
      <div
        className={`mobile-drawer mobile-drawer--${position}`}
        style={position === 'bottom' ? { height } : undefined}
        role="dialog"
        aria-modal="true"
      >
        <div className="mobile-drawer__handle" />
        {title && (
          <div className="mobile-drawer__header">
            <h3 className="mobile-drawer__title">{title}</h3>
            <button className="mobile-drawer__close" onClick={onClose} type="button" aria-label="关闭">
              ✕
            </button>
          </div>
        )}
        <div className="mobile-drawer__content">{children}</div>
      </div>
    </>
  )
}
