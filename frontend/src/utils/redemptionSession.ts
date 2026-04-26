// 兑换码会话工具函数，使用 localStorage 轻量持久化
import type { RedemptionSession } from '@/types/redemption'

const SESSION_KEY = 'redemption-session'

export function getRedemptionSession(): RedemptionSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return null
    return JSON.parse(raw) as RedemptionSession
  } catch {
    return null
  }
}

export function setRedemptionSession(session: RedemptionSession): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function clearRedemptionSession(): void {
  localStorage.removeItem(SESSION_KEY)
}
