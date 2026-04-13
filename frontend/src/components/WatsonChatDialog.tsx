import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useDrag } from '@/hooks/useDrag'
import { useWatsonChatStore } from '@/store'
import { useGameStore } from '@/store'
import type { QuickQuestion, GamePhase } from '@/types/game'

console.debug('[WatsonChatDialog.tsx] 加载模块')

interface WatsonChatDialogProps {
  gameId: string
}

// 快捷提问配置
const QUICK_QUESTIONS: QuickQuestion[] = [
  // 开局阶段
  { label: '这个案子你怎么看？', message: '这个案子你怎么看？', phase: ['start'] },
  { label: '我们先做什么？', message: '我们先做什么？', phase: ['start'] },

  // 勘查阶段
  { label: '我们现在该勘查哪里？', message: '我们现在该勘查哪里？', phase: ['investigation'] },
  { label: '这条线索意味着什么？', message: '这条线索意味着什么？', phase: ['investigation'] },
  { label: '总结一下已发现的线索', message: '总结一下已发现的线索', phase: ['investigation'] },

  // 推理阶段
  { label: '我们的推理完整吗？', message: '我们的推理完整吗？', phase: ['deduction'] },
  { label: '这个推论合理吗？', message: '这个推论合理吗？', phase: ['deduction'] },
  { label: '指出逻辑缺口', message: '指出逻辑缺口', phase: ['deduction'] },

  // 质询阶段
  { label: '我们应该先审问谁？', message: '我们应该先审问谁？', phase: ['interrogation'] },
  { label: '你觉得他在说谎吗？', message: '你觉得他在说谎吗？', phase: ['interrogation'] },
  { label: '证词有什么矛盾？', message: '证词有什么矛盾？', phase: ['interrogation'] },

  // 结案阶段
  { label: '我们的证据足够吗？', message: '我们的证据足够吗？', phase: ['conclusion'] },
  { label: '你觉得谁是凶手？', message: '你觉得谁是凶手？', phase: ['conclusion'] },
  { label: '回顾一下探案过程', message: '回顾一下探案过程', phase: ['conclusion'] },
]

export default function WatsonChatDialog({ gameId }: WatsonChatDialogProps) {
  const {
    messages,
    isLoading,
    error,
    isDialogOpen,
    isDialogExpanded,
    sendMessage,
    fetchHistory,
    setDialogOpen,
    setDialogExpanded,
  } = useWatsonChatStore()

  const gameState = useGameStore((state) => state.gameState)
  const currentPhase = gameState?.phase || 'start'

  const [inputMessage, setInputMessage] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  console.info('[WatsonChatDialog] 渲染组件', { gameId, currentPhase, messageCount: messages.length })

  // 计算对话框的初始位置（从右下角开始）
  const initialDragPosition = useMemo(() => {
    return { x: 0, y: 0 }
  }, [])

  // 初始化拖拽 Hook
  const {
    dragRef,
    dragStyle,
    isDragging,
    dragHandleProps,
    setPosition,
  } = useDrag({
    initialPosition: initialDragPosition,
    boundary: { padding: 20 }
  })

  // 组件挂载后，根据初始的 bottom/right 计算 transform 位置
  useEffect(() => {
    if (dragRef.current) {
      const rect = dragRef.current.getBoundingClientRect()
      const initialX = window.innerWidth - rect.width - 32
      const initialY = window.innerHeight - rect.height - 32
      setPosition({ x: initialX, y: initialY })
    }
  }, [setPosition])

  // 组件挂载时获取对话历史
  useEffect(() => {
    if (gameId) {
      console.info('[WatsonChatDialog] 获取对话历史', { gameId })
      fetchHistory(gameId)
    }
  }, [gameId, fetchHistory])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // 获取当前阶段的快捷问题
  const currentQuickQuestions = useMemo(() => {
    return QUICK_QUESTIONS.filter(q => q.phase.includes(currentPhase as GamePhase))
  }, [currentPhase])

  // 处理发送消息
  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim() || !gameId) return

    const messageToSend = inputMessage.trim()
    setInputMessage('')
    console.info('[WatsonChatDialog] 发送消息', { message: messageToSend })

    await sendMessage(gameId, messageToSend)
  }, [inputMessage, gameId, sendMessage])

  // 处理快捷问题点击
  const handleQuickQuestion = useCallback(async (question: string) => {
    if (!gameId) return

    console.info('[WatsonChatDialog] 快捷问题', { question })
    setInputMessage('')
    await sendMessage(gameId, question)
  }, [gameId, sendMessage])

  // 处理回车键发送
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }, [handleSendMessage])

  // 获取消息类型的显示名称
  const getMessageTypeName = (type: string) => {
    const names: Record<string, string> = {
      guidance: '指导',
      clue_discussion: '线索讨论',
      suspect_analysis: '嫌疑人分析',
      deduction_review: '推理梳理',
      knowledge: '知识',
      encouragement: '鼓励',
      general: '聊天',
    }
    return names[type] || type
  }

  return (
    <div
      ref={dragRef}
      className={`watson-dialog ${isDialogOpen ? 'watson-dialog--open' : ''} watson-dialog--chat watson-dialog--draggable ${isDragging ? 'watson-dialog--dragging' : ''}`}
      style={dragStyle}
    >
      {/* 对话框头部 */}
      <div className="watson-dialog__header" {...dragHandleProps}>
        <div className="watson-avatar">
          <span className="watson-avatar__icon">👨‍⚕️</span>
        </div>
        <div className="watson-info">
          <h4 className="watson-name">约翰·华生</h4>
          <span className="watson-status">
            {isLoading ? '正在思考...' : '在线'}
          </span>
        </div>
        <div className="watson-dialog__controls">
          <button
            className="watson-dialog__toggle-expand"
            onClick={(e) => {
              e.stopPropagation()
              setDialogExpanded(!isDialogExpanded)
            }}
            type="button"
            title={isDialogExpanded ? '收起' : '展开'}
          >
            {isDialogExpanded ? '−' : '□'}
          </button>
          <button
            className="watson-dialog__toggle"
            onClick={(e) => {
              e.stopPropagation()
              setDialogOpen(!isDialogOpen)
            }}
            type="button"
            title={isDialogOpen ? '最小化' : '打开'}
          >
            {isDialogOpen ? '−' : '+'}
          </button>
        </div>
      </div>

      {/* 对话框内容 */}
      {isDialogOpen && (
        <div className={`watson-dialog__content ${isDialogExpanded ? 'watson-dialog__content--expanded' : ''}`}>
          {/* 错误提示 */}
          {error && (
            <div className="watson-error">
              <span className="error-icon">⚠️</span>
              <span className="error-message">{error}</span>
            </div>
          )}

          {/* 消息列表 */}
          <div className="watson-messages">
            {messages.length === 0 ? (
              <div className="watson-welcome">
                <p>你好，老朋友！有什么想和我讨论的吗？随时问我问题，我会尽力帮助你。</p>
              </div>
            ) : (
              messages.map(msg => (
                <div
                  key={msg.id}
                  className={`watson-message watson-message--${msg.role} watson-message--type-${msg.messageType}`}
                >
                  <div className="watson-message__role">
                    {msg.role === 'user' ? '你' : '华生'}
                    {msg.role === 'watson' && (
                      <span className="watson-message__type">
                        ({getMessageTypeName(msg.messageType)})
                      </span>
                    )}
                  </div>
                  <div className="watson-message__content">{msg.content}</div>
                  <div className="watson-message__time">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))
            )}

            {/* 正在思考提示 */}
            {isLoading && (
              <div className="watson-typing">
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
              </div>
            )}

            {/* 自动滚动锚点 */}
            <div ref={messagesEndRef} />
          </div>

          {/* 快捷问题按钮 */}
          {currentQuickQuestions.length > 0 && (
            <div className="watson-quick-questions">
              <div className="quick-questions-label">快捷问题：</div>
              <div className="quick-questions-list">
                {currentQuickQuestions.map((q, index) => (
                  <button
                    key={index}
                    className="quick-question-btn"
                    onClick={() => handleQuickQuestion(q.message)}
                    disabled={isLoading}
                    type="button"
                  >
                    {q.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 输入区域 */}
          <div className="watson-input-area">
            <input
              type="text"
              className="watson-input"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="问华生任何问题..."
              disabled={isLoading}
            />
            <button
              className="watson-send-btn"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              type="button"
            >
              发送
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
