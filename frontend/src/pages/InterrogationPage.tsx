import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { GameState, Suspect } from '@/types/game'
import { gameApi, type ConversationMessage, type LieDetectionResult } from '@/services/api'

// 审讯模式
type InterrogationMode = 'private' | 'group'

// 华生消息类型
interface WatsonMessage {
  id: string
  content: string
  type: 'question' | 'hint' | 'observation' | 'encouragement'
  timestamp: Date
}

export default function InterrogationPage() {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()

  const [gameState, setGameState] = useState<GameState | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<InterrogationMode>('private')
  const [selectedSuspect, setSelectedSuspect] = useState<Suspect | null>(null)
  const [question, setQuestion] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>([])
  const [lieDetection, setLieDetection] = useState<LieDetectionResult | null>(null)

  // 华生相关状态
  const [watsonMessages, setWatsonMessages] = useState<WatsonMessage[]>([])
  const [showWatsonDialog, setShowWatsonDialog] = useState(true)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  console.debug('[InterrogationPage] 渲染审讯页面', { gameId, mode })

  // 添加华生消息
  const addWatsonMessage = useCallback((content: string, type: WatsonMessage['type'] = 'question') => {
    const message: WatsonMessage = {
      id: `watson-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      content,
      type,
      timestamp: new Date(),
    }
    console.info('[InterrogationPage] 华生消息', { content, type })
    setWatsonMessages(prev => [...prev, message])
  }, [])

  // 滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversationHistory, watsonMessages])

  // 加载游戏状态
  useEffect(() => {
    if (!gameId) return

    const loadGame = async () => {
      console.info('[InterrogationPage] 加载游戏状态', { gameId })
      setIsLoading(true)
      setError(null)

      try {
        const state = await gameApi.getGameState(gameId)
        console.info('[InterrogationPage] 游戏状态加载成功', state)
        setGameState(state)

        // 默认选择第一个嫌疑人
        if (state.case?.suspects && state.case.suspects.length > 0) {
          setSelectedSuspect(state.case.suspects[0])
        }

        // 显示华生欢迎消息
        setTimeout(() => {
          addWatsonMessage(
            '好的，老朋友。现在我们来和这些嫌疑人谈谈。记住，仔细观察他们的反应——有时候肢体语言比语言更能说明问题。',
            'encouragement'
          )
        }, 500)
      } catch (err) {
        console.error('[InterrogationPage] 加载游戏失败', err)
        setError(err instanceof Error ? err.message : '加载游戏失败')
      } finally {
        setIsLoading(false)
      }
    }

    loadGame()
  }, [gameId, addWatsonMessage])

  // 切换嫌疑人
  const handleSuspectSelect = (suspect: Suspect) => {
    console.debug('[InterrogationPage] 选择嫌疑人', { suspectId: suspect.id, suspectName: suspect.name })
    setSelectedSuspect(suspect)
    setConversationHistory([])
    setLieDetection(null)

    // 华生主动提问
    if (Math.random() > 0.3) {
      const questions = [
        `让我们问问${suspect.name}昨晚在哪里。`,
        `或许我们应该了解一下${suspect.name}和死者的关系。`,
        `我很好奇${suspect.name}对这起案件有什么看法。`,
      ]
      const randomIndex = Math.floor(Math.random() * questions.length)
      addWatsonMessage(questions[randomIndex], 'question')
    }
  }

  // 发送问题
  const handleSendQuestion = async () => {
    if (!gameId || !selectedSuspect || !question.trim() || isProcessing) return

    console.info('[InterrogationPage] 发送问题', { suspectId: selectedSuspect.id, question })
    setIsProcessing(true)

    try {
      // 添加用户问题到对话历史
      const userMessage: ConversationMessage = {
        role: 'user',
        content: question,
        timestamp: new Date().toISOString(),
      }
      setConversationHistory(prev => [...prev, userMessage])

      // 调用API
      const response = await gameApi.askSuspectQuestion(
        gameId,
        selectedSuspect.id,
        question,
        conversationHistory,
        mode === 'private',
        mode === 'group'
          ? (gameState?.case?.suspects?.map(s => s.id).filter(id => id !== selectedSuspect.id) || [])
          : []
      )

      // 添加嫌疑人回复到对话历史
      const suspectMessage: ConversationMessage = {
        role: 'suspect',
        content: response.response,
        timestamp: new Date().toISOString(),
      }
      setConversationHistory(prev => [...prev, suspectMessage])

      // 设置谎言检测结果
      setLieDetection(response.lie_detection)

      // 华生评论
      if (response.lie_detection.lie_detected && response.lie_detection.microexpression) {
        setTimeout(() => {
          addWatsonMessage(
            `你注意到了吗？${selectedSuspect.name}${response.lie_detection.microexpression}。我觉得${response.lie_detection.notes}。`,
            'observation'
          )
        }, 800)
      } else if (Math.random() > 0.5) {
        setTimeout(() => {
          const comments = [
            '这回答有点意思。你怎么看？',
            '我不确定是否完全相信这个说法。',
            '我们应该继续追问这个话题。',
            '让我想想...这和我们知道的其他信息一致吗？',
          ]
          const randomIndex = Math.floor(Math.random() * comments.length)
          addWatsonMessage(comments[randomIndex], 'hint')
        }, 1000)
      }

      // 清空输入
      setQuestion('')
    } catch (err) {
      console.error('[InterrogationPage] 发送问题失败', err)
      setError(err instanceof Error ? err.message : '发送问题失败')
    } finally {
      setIsProcessing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="interrogation-page interrogation-page--loading">
        <div className="loading-spinner">
          <p>正在进入审讯室...</p>
        </div>
      </div>
    )
  }

  if (error || !gameState) {
    return (
      <div className="interrogation-page interrogation-page--error">
        <div className="error-message">
          <h2>出错了</h2>
          <p>{error || '无法加载游戏'}</p>
          <button onClick={() => navigate('/')} type="button">
            返回贝克街
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="interrogation-page">
      {/* 顶部导航栏 */}
      <header className="interrogation-header">
        <div className="header-content">
          <h1 className="header-title">
            {mode === 'private' ? '单独审讯' : '全体质询'}
          </h1>
          <div className="header-info">
            <span className="mode-toggle">
              <button
                className={`mode-button ${mode === 'private' ? 'mode-button--active' : ''}`}
                onClick={() => setMode('private')}
                type="button"
              >
                密室问话
              </button>
              <button
                className={`mode-button ${mode === 'group' ? 'mode-button--active' : ''}`}
                onClick={() => setMode('group')}
                type="button"
                disabled
              >
                圆桌对峙 (开发中)
              </button>
            </span>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="interrogation-main">
        {/* 嫌疑人列表 */}
        <aside className="suspects-panel">
          <div className="panel-header">
            <h3>嫌疑人</h3>
          </div>
          <div className="panel-content">
            <ul className="suspect-list">
              {gameState.case?.suspects?.map(suspect => (
                <li
                  key={suspect.id}
                  className={`suspect-item ${selectedSuspect?.id === suspect.id ? 'suspect-item--selected' : ''}`}
                  onClick={() => handleSuspectSelect(suspect)}
                >
                  <div className="suspect-avatar">
                    {suspect.isGuilty ? '🔪' : '👤'}
                  </div>
                  <div className="suspect-info">
                    <div className="suspect-name">{suspect.name}</div>
                    <div className="suspect-age">{suspect.age}岁</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        {/* 审讯对话区 */}
        <section className="interrogation-room">
          {selectedSuspect ? (
            <>
              {/* 嫌疑人信息 */}
              <div className="current-suspect">
                <div className="suspect-header">
                  <div className="suspect-avatar-large">
                    {selectedSuspect.isGuilty ? '🔪' : '👤'}
                  </div>
                  <div className="suspect-details">
                    <h2>{selectedSuspect.name}</h2>
                    <p className="suspect-background">{selectedSuspect.background}</p>
                    <div className="suspect-tags">
                      {selectedSuspect.personalityTraits?.map((trait: string, i: number) => (
                        <span key={i} className="personality-tag">{trait}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* 对话历史 */}
              <div className="conversation-area">
                <div className="conversation-messages">
                  {conversationHistory.length === 0 ? (
                    <div className="no-messages">
                      <p>开始询问{selectedSuspect.name}吧。</p>
                    </div>
                  ) : (
                    conversationHistory.map((msg, idx) => (
                      <div key={idx} className={`message message--${msg.role}`}>
                        <div className="message-avatar">
                          {msg.role === 'user' ? '🔍' : selectedSuspect.isGuilty ? '🔪' : '👤'}
                        </div>
                        <div className="message-content">
                          <div className="message-sender">
                            {msg.role === 'user' ? '你' : selectedSuspect.name}
                          </div>
                          <div className="message-text">{msg.content}</div>
                          {msg.timestamp && (
                            <div className="message-time">
                              {new Date(msg.timestamp).toLocaleTimeString()}
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                  {lieDetection && (
                    <div className={`lie-detection lie-detection--${lieDetection.lie_detected ? 'warning' : 'ok'}`}>
                      <div className="lie-detection-icon">
                        {lieDetection.lie_detected ? '⚠️' : '✓'}
                      </div>
                      <div className="lie-detection-content">
                        <div className="lie-detection-title">
                          {lieDetection.lie_detected ? '检测到可能的谎言' : '言辞一致'}
                        </div>
                        {lieDetection.microexpression && (
                          <div className="lie-detection-microexpression">
                            微表情: {lieDetection.microexpression}
                          </div>
                        )}
                        <div className="lie-detection-confidence">
                          置信度: {(lieDetection.confidence * 100).toFixed(0)}%
                        </div>
                        <div className="lie-detection-notes">{lieDetection.notes}</div>
                      </div>
                    </div>
                  )}
                  {isProcessing && (
                    <div className="message message--suspect">
                      <div className="message-avatar">
                        {selectedSuspect.isGuilty ? '🔪' : '👤'}
                      </div>
                      <div className="message-content">
                        <div className="suspect-typing">
                          <span className="typing-dot"></span>
                          <span className="typing-dot"></span>
                          <span className="typing-dot"></span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* 输入区 */}
                <div className="question-input-area">
                  <input
                    type="text"
                    className="question-input"
                    placeholder={`询问${selectedSuspect.name}...`}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSendQuestion()
                      }
                    }}
                    disabled={isProcessing}
                  />
                  <button
                    className="send-button"
                    onClick={handleSendQuestion}
                    disabled={!question.trim() || isProcessing}
                    type="button"
                  >
                    发送
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="no-suspect-selected">
              <p>请选择一个嫌疑人开始审讯</p>
            </div>
          )}
        </section>
      </main>

      {/* 华生对话框 */}
      <div className={`watson-dialog ${showWatsonDialog ? 'watson-dialog--open' : ''}`}>
        <div className="watson-dialog__header">
          <div className="watson-avatar">
            <span className="watson-avatar__icon">👨‍⚕️</span>
          </div>
          <div className="watson-info">
            <h4 className="watson-name">约翰·华生</h4>
            <span className="watson-status">在线</span>
          </div>
          <button
            className="watson-dialog__toggle"
            onClick={() => setShowWatsonDialog(!showWatsonDialog)}
            type="button"
          >
            {showWatsonDialog ? '−' : '+'}
          </button>
        </div>

        {showWatsonDialog && (
          <div className="watson-dialog__content">
            <div className="watson-messages">
              {watsonMessages.length === 0 ? (
                <div className="watson-welcome">
                  <p>华生医生会在这里给你提示和建议。</p>
                </div>
              ) : (
                watsonMessages.map(msg => (
                  <div key={msg.id} className={`watson-message watson-message--${msg.type}`}>
                    <div className="watson-message__content">{msg.content}</div>
                    <div className="watson-message__time">
                      {msg.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* 底部导航 */}
      <footer className="interrogation-footer">
        <button
          className="footer-button footer-button--back"
          onClick={() => navigate(`/investigation/${gameId}`)}
          type="button"
        >
          返回勘查现场
        </button>
        <div className="footer-progress">
          <span>已审讯: {gameState.interviewedSuspectIds?.length || 0} / {gameState.case?.suspects?.length || 0}</span>
        </div>
        <button
          className="footer-button footer-button--next"
          disabled={true}
          type="button"
        >
          下一步: 推理链条 (开发中)
        </button>
      </footer>

      {/* 审讯页面样式 */}
      <style>{`
        .interrogation-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          background: linear-gradient(180deg, #0f0f23 0%, #1a1a2e 100%);
          color: #e8e8e8;
        }

        .interrogation-page--loading,
        .interrogation-page--error {
          align-items: center;
          justify-content: center;
        }

        .loading-spinner,
        .error-message {
          text-align: center;
          padding: 2rem;
        }

        .error-message h2 {
          color: #dc3545;
          margin-bottom: 1rem;
        }

        .error-message button {
          margin-top: 1.5rem;
          padding: 0.75rem 2rem;
          background: #d4af37;
          color: #1a1a2e;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-family: 'Georgia', serif;
        }

        /* 顶部导航栏 */
        .interrogation-header {
          background: rgba(0, 0, 0, 0.5);
          border-bottom: 2px solid #d4af37;
          padding: 1rem 2rem;
        }

        .header-content {
          max-width: 1400px;
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .header-title {
          font-size: 1.75rem;
          color: #d4af37;
        }

        .mode-toggle {
          display: flex;
          gap: 0.5rem;
        }

        .mode-button {
          padding: 0.5rem 1rem;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid #333;
          color: #a0a0a0;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.3s ease;
          font-family: 'Georgia', serif;
        }

        .mode-button:hover:not(:disabled) {
          border-color: #d4af37;
          color: #d4af37;
        }

        .mode-button--active {
          border-color: #d4af37;
          background: rgba(212, 175, 55, 0.15);
          color: #d4af37;
        }

        .mode-button:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        /* 主内容区 */
        .interrogation-main {
          flex: 1;
          display: flex;
          gap: 1rem;
          padding: 1.5rem;
          max-width: 1400px;
          width: 100%;
          margin: 0 auto;
        }

        /* 嫌疑人面板 */
        .suspects-panel {
          width: 280px;
          background: rgba(0, 0, 0, 0.4);
          border: 1px solid #333;
          border-radius: 8px;
          display: flex;
          flex-direction: column;
        }

        .panel-header {
          padding: 1rem 1.25rem;
          border-bottom: 1px solid #333;
        }

        .panel-header h3 {
          color: #d4af37;
          font-size: 1.1rem;
        }

        .panel-content {
          flex: 1;
          padding: 1rem;
          overflow-y: auto;
        }

        .suspect-list {
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .suspect-item {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.75rem;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid #2a2a3a;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .suspect-item:hover {
          border-color: #d4af37;
          background: rgba(212, 175, 55, 0.1);
        }

        .suspect-item--selected {
          border-color: #d4af37;
          background: rgba(212, 175, 55, 0.15);
        }

        .suspect-avatar {
          width: 40px;
          height: 40px;
          background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
        }

        .suspect-info {
          flex: 1;
        }

        .suspect-name {
          color: #d4af37;
          font-weight: bold;
          font-size: 0.95rem;
        }

        .suspect-age {
          color: #666;
          font-size: 0.85rem;
        }

        /* 审讯室 */
        .interrogation-room {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .no-suspect-selected {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #666;
          font-size: 1.2rem;
        }

        /* 当前嫌疑人 */
        .current-suspect {
          background: rgba(0, 0, 0, 0.4);
          border: 1px solid #333;
          border-radius: 8px;
          padding: 1.5rem;
        }

        .suspect-header {
          display: flex;
          gap: 1.5rem;
          align-items: flex-start;
        }

        .suspect-avatar-large {
          width: 80px;
          height: 80px;
          background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 2.5rem;
          flex-shrink: 0;
        }

        .suspect-details {
          flex: 1;
        }

        .suspect-details h2 {
          color: #d4af37;
          font-size: 1.75rem;
          margin-bottom: 0.5rem;
        }

        .suspect-background {
          color: #a0a0a0;
          line-height: 1.6;
          margin-bottom: 1rem;
        }

        .suspect-tags {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .personality-tag {
          padding: 0.25rem 0.75rem;
          background: rgba(212, 175, 55, 0.1);
          border: 1px solid rgba(212, 175, 55, 0.3);
          border-radius: 12px;
          color: #d4af37;
          font-size: 0.85rem;
        }

        /* 对话区 */
        .conversation-area {
          flex: 1;
          display: flex;
          flex-direction: column;
          background: rgba(0, 0, 0, 0.4);
          border: 1px solid #333;
          border-radius: 8px;
          overflow: hidden;
        }

        .conversation-messages {
          flex: 1;
          padding: 1.5rem;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .no-messages {
          text-align: center;
          color: #666;
          padding: 2rem 0;
        }

        .message {
          display: flex;
          gap: 1rem;
          animation: messageSlideIn 0.3s ease;
        }

        @keyframes messageSlideIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .message--user {
          flex-direction: row-reverse;
        }

        .message-avatar {
          width: 40px;
          height: 40px;
          background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
          flex-shrink: 0;
        }

        .message--user .message-avatar {
          background: linear-gradient(135deg, #4a90d9 0%, #2d6cb3 100%);
        }

        .message-content {
          max-width: 70%;
        }

        .message-sender {
          color: #666;
          font-size: 0.85rem;
          margin-bottom: 0.25rem;
        }

        .message--user .message-sender {
          text-align: right;
        }

        .message-text {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid #333;
          border-radius: 8px;
          padding: 0.75rem 1rem;
          color: #e8e8e8;
          line-height: 1.6;
        }

        .message--user .message-text {
          background: rgba(74, 144, 217, 0.1);
          border-color: rgba(74, 144, 217, 0.3);
        }

        .message-time {
          color: #555;
          font-size: 0.75rem;
          margin-top: 0.25rem;
        }

        .message--user .message-time {
          text-align: right;
        }

        /* 嫌疑人流打字 */
        .suspect-typing {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.75rem 1rem;
        }

        .typing-dot {
          width: 8px;
          height: 8px;
          background: #d4af37;
          border-radius: 50%;
          animation: typingBounce 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: 0s; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typingBounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-8px); }
        }

        /* 谎言检测 */
        .lie-detection {
          display: flex;
          gap: 1rem;
          padding: 1rem;
          border-radius: 8px;
          margin-top: 0.5rem;
        }

        .lie-detection--warning {
          background: rgba(255, 152, 0, 0.1);
          border: 1px solid rgba(255, 152, 0, 0.3);
        }

        .lie-detection--ok {
          background: rgba(76, 175, 80, 0.1);
          border: 1px solid rgba(76, 175, 80, 0.3);
        }

        .lie-detection-icon {
          font-size: 1.5rem;
        }

        .lie-detection-content {
          flex: 1;
        }

        .lie-detection-title {
          color: #ff9800;
          font-weight: bold;
          margin-bottom: 0.5rem;
        }

        .lie-detection--ok .lie-detection-title {
          color: #4caf50;
        }

        .lie-detection-microexpression {
          color: #a0a0a0;
          font-style: italic;
          margin-bottom: 0.25rem;
        }

        .lie-detection-confidence {
          color: #888;
          font-size: 0.9rem;
          margin-bottom: 0.25rem;
        }

        .lie-detection-notes {
          color: #a0a0a0;
          font-size: 0.9rem;
        }

        /* 输入区 */
        .question-input-area {
          display: flex;
          gap: 0.75rem;
          padding: 1rem 1.5rem;
          border-top: 1px solid #333;
          background: rgba(0, 0, 0, 0.3);
        }

        .question-input {
          flex: 1;
          padding: 0.75rem 1rem;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid #333;
          border-radius: 6px;
          color: #e8e8e8;
          font-size: 1rem;
          font-family: 'Georgia', serif;
          transition: all 0.3s ease;
        }

        .question-input:focus {
          outline: none;
          border-color: #d4af37;
          background: rgba(255, 255, 255, 0.08);
        }

        .question-input::placeholder {
          color: #666;
        }

        .send-button {
          padding: 0.75rem 1.5rem;
          background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
          color: #1a1a2e;
          border: none;
          border-radius: 6px;
          font-size: 1rem;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s ease;
          font-family: 'Georgia', serif;
        }

        .send-button:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4);
        }

        .send-button:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        /* 华生对话框 */
        .watson-dialog {
          position: fixed;
          bottom: 2rem;
          right: 2rem;
          width: 360px;
          background: linear-gradient(180deg, #1a1a2e 0%, #0f0f23 100%);
          border: 2px solid #d4af37;
          border-radius: 12px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
          z-index: 100;
          overflow: hidden;
          transition: all 0.3s ease;
        }

        .watson-dialog--open {
          width: 380px;
        }

        .watson-dialog__header {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1rem 1.25rem;
          background: rgba(212, 175, 55, 0.1);
          border-bottom: 1px solid #333;
        }

        .watson-avatar {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 0 16px rgba(212, 175, 55, 0.3);
        }

        .watson-avatar__icon {
          font-size: 1.75rem;
        }

        .watson-info {
          flex: 1;
        }

        .watson-name {
          color: #d4af37;
          font-size: 1.1rem;
          margin-bottom: 0.25rem;
        }

        .watson-status {
          color: #666;
          font-size: 0.85rem;
        }

        .watson-dialog__toggle {
          background: rgba(212, 175, 55, 0.1);
          border: 1px solid #d4af37;
          color: #d4af37;
          width: 2rem;
          height: 2rem;
          border-radius: 50%;
          cursor: pointer;
          font-size: 1.25rem;
          font-weight: bold;
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'Georgia', serif;
          transition: all 0.3s ease;
        }

        .watson-dialog__toggle:hover {
          background: rgba(212, 175, 55, 0.2);
        }

        .watson-dialog__content {
          max-height: 300px;
          display: flex;
          flex-direction: column;
        }

        .watson-messages {
          flex: 1;
          overflow-y: auto;
          padding: 1rem 1.25rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .watson-welcome {
          text-align: center;
          color: #666;
          padding: 1rem 0;
        }

        .watson-message {
          background: rgba(212, 175, 55, 0.08);
          border-left: 3px solid #d4af37;
          padding: 0.75rem 1rem;
          border-radius: 0 8px 8px 0;
          animation: messageSlideIn 0.3s ease;
        }

        .watson-message--question {
          background: rgba(33, 150, 243, 0.08);
          border-left-color: #2196f3;
        }

        .watson-message--hint {
          background: rgba(255, 152, 0, 0.08);
          border-left-color: #ff9800;
        }

        .watson-message--observation {
          background: rgba(76, 175, 80, 0.08);
          border-left-color: #4caf50;
        }

        .watson-message--encouragement {
          background: rgba(156, 39, 176, 0.08);
          border-left-color: #9c27b0;
        }

        .watson-message__content {
          color: #e8e8e8;
          line-height: 1.6;
          font-size: 0.95rem;
          margin-bottom: 0.5rem;
        }

        .watson-message__time {
          color: #666;
          font-size: 0.75rem;
          text-align: right;
        }

        .watson-typing {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.5rem 1rem;
        }

        /* 底部导航 */
        .interrogation-footer {
          background: rgba(0, 0, 0, 0.5);
          border-top: 2px solid #333;
          padding: 1rem 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .footer-button {
          padding: 0.75rem 1.5rem;
          border-radius: 6px;
          font-size: 1rem;
          cursor: pointer;
          font-family: 'Georgia', serif;
          transition: all 0.3s ease;
        }

        .footer-button--back {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid #555;
          color: #a0a0a0;
        }

        .footer-button--back:hover {
          border-color: #888;
          color: #fff;
        }

        .footer-button--next {
          background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
          border: none;
          color: #1a1a2e;
          font-weight: bold;
        }

        .footer-button--next:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4);
        }

        .footer-button:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .footer-progress {
          color: #a0a0a0;
          font-size: 1rem;
        }
      `}</style>
    </div>
  )
}
