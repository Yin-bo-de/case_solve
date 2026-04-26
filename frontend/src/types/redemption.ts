// 兑换码相关类型定义

export interface RedemptionVerifyRequest {
  code: string
}

export interface RedemptionVerifyResponse {
  success: boolean
  remainingUses: number
  message: string
}

export interface RedemptionGenerateResponse {
  code: string
  maxUses: number
  usedCount: number
  createdAt: string
}

/** localStorage 中持久化的兑换码会话信息 */
export interface RedemptionSession {
  code: string
  remainingUses: number
  validatedAt: string
}
