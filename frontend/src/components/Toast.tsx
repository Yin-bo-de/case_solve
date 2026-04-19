import { useEffect, useState } from 'react'

interface Props {
  message: string
  duration?: number
  onDismiss: () => void
}

export default function Toast({ message, duration = 2500, onDismiss }: Props) {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false)
      setTimeout(onDismiss, 300)
    }, duration)
    return () => clearTimeout(timer)
  }, [duration, onDismiss])

  return (
    <div className={`toast toast--success ${visible ? 'toast--in' : 'toast--out'}`}>
      <span className="toast__icon">✓</span>
      <span className="toast__message">{message}</span>
      <style>{`
        .toast {
          position: fixed;
          bottom: 2rem;
          left: 50%;
          transform: translateX(-50%) translateY(0);
          display: flex;
          align-items: center;
          gap: 0.6rem;
          padding: 0.7rem 1.4rem;
          border-radius: 6px;
          font-family: 'Georgia', serif;
          font-size: 0.95rem;
          z-index: 9999;
          pointer-events: none;
          transition: opacity 0.3s ease, transform 0.3s ease;
        }
        .toast--success {
          background: rgba(10, 10, 20, 0.92);
          border: 1px solid rgba(212, 175, 55, 0.6);
          color: #d4af37;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6);
        }
        .toast__icon {
          font-size: 1rem;
          color: #4caf50;
        }
        .toast--in {
          opacity: 1;
          transform: translateX(-50%) translateY(0);
        }
        .toast--out {
          opacity: 0;
          transform: translateX(-50%) translateY(8px);
        }
      `}</style>
    </div>
  )
}
