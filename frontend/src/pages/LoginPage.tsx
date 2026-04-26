import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { redemptionApi } from '@/services/api'
import { setRedemptionSession } from '@/utils/redemptionSession'

console.debug('[LoginPage] 模块加载')

/** 将用户输入自动格式化为 XXXX-XXXX-XXXX，最多保留 14 个可打印字符 */
function formatCode(raw: string): string {
  const cleaned = raw.replace(/[^A-Za-z0-9]/g, '').toUpperCase().slice(0, 12)
  const parts = [cleaned.slice(0, 4), cleaned.slice(4, 8), cleaned.slice(8, 12)].filter(Boolean)
  return parts.join('-')
}

export default function LoginPage() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  console.debug('[LoginPage] 渲染登录页面')

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCode(e.target.value)
    setCode(formatted)
    setError(null)
  }

  const handleVerify = async () => {
    const trimmed = code.trim()
    if (!trimmed) {
      setError('请输入兑换码')
      inputRef.current?.focus()
      return
    }
    if (trimmed.length < 14) {
      setError('兑换码格式错误，应为 XXXX-XXXX-XXXX')
      inputRef.current?.focus()
      return
    }

    console.info('[LoginPage] 验证兑换码', { code: `${trimmed.slice(0, 4)}***` })
    setIsLoading(true)
    setError(null)

    try {
      const result = await redemptionApi.verify(trimmed)

      if (!result.success || !result.gameId) {
        setError(result.message || '兑换码无效，请检查后重试')
        return
      }

      setRedemptionSession({
        gameId: result.gameId,
        code: trimmed,
        remainingUses: result.remainingUses,
        validatedAt: new Date().toISOString(),
      })

      console.info('[LoginPage] 验证成功，跳转至开始页', { gameId: result.gameId, remainingUses: result.remainingUses })
      navigate('/start')
    } catch (err) {
      console.error('[LoginPage] 验证请求失败', err)
      setError('验证失败，请检查网络后重试')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isLoading) {
      handleVerify()
    }
  }

  return (
    <div className="login-page">
      {/* 壁灯装饰（复用 StartPage 样式） */}
      <div className="gaslight-wall-lamp gaslight-wall-lamp--left" />
      <div className="gaslight-wall-lamp gaslight-wall-lamp--right" />

      <div className="login-page__content">
        <h1 className="login-page__title">贝克街221B</h1>
        <p className="login-page__subtitle">
          伦敦，1895年。迷雾笼罩的都市中，一桩离奇命案正待阁下侦破...
        </p>

        <div className="login-page__card">
          <div className="login-page__card-header">
            <span className="login-page__card-icon">🔑</span>
            <h2 className="login-page__card-title">凭证验证</h2>
          </div>
          <p className="login-page__card-desc">
            请输入您的探案资格凭证以进入案件档案室
          </p>

          <div className="login-page__field">
            <label htmlFor="redeem-code" className="login-page__label">
              兑换码
            </label>
            <input
              id="redeem-code"
              ref={inputRef}
              type="text"
              className={`login-page__input${error ? ' login-page__input--error' : ''}`}
              placeholder="XXXX-XXXX-XXXX"
              value={code}
              onChange={handleCodeChange}
              onKeyDown={handleKeyDown}
              maxLength={14}
              autoFocus
              autoComplete="off"
              spellCheck={false}
            />
            {error && (
              <p className="login-page__error">{error}</p>
            )}
          </div>

          <button
            className="login-page__button"
            onClick={handleVerify}
            disabled={isLoading}
            type="button"
          >
            {isLoading ? '验证中...' : '验证凭证，着手探案'}
          </button>
        </div>
      </div>
    </div>
  )
}
