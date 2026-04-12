import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { GameState, Suspect } from '@/types/game'
import {
  gameApi,
  type ConversationMessage,
  type LieDetectionResult,
  type ContradictionResult,
  type GroupControlAction,
} from '@/services/api'

// 审讯模式
type InterrogationMode = 'private' | 'group'

// 华生消息类型
interface WatsonMessage {
  id: string
  content: string
  type: 'question' | 'hint' | 'observation' | 'encouragement'
  timestamp: Date
}

// 全体质询消息类型
interface GroupMessage {
  id: string
  role: 'user' | 'suspect' | 'watson' | 'system' | 'interjection'
  content: string
  suspectId?: string
  suspectName?: string
  timestamp: string
}

// 嫌疑人插话计数
interface InterjectionCount {
  [suspectId: string]: number
}

// @提及的嫌疑人
interface MentionedSuspect {
  id: string
  name: string
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

  // 全体质询相关状态
  const [groupMessages, setGroupMessages] = useState<GroupMessage[]>([])
  const [mentionedSuspects, setMentionedSuspects] = useState<MentionedSuspect[]>([])
  const [showMentionMenu, setShowMentionMenu] = useState(false)
  const [mentionMenuPosition, setMentionMenuPosition] = useState({ x: 0, y: 0 })
  const [contradictions, setContradictions] = useState<ContradictionResult[]>([])
  const [interjectionCounts, setInterjectionCounts] = useState<InterjectionCount>({})
  const [suspectStatements, setSuspectStatements] = useState<Record<string, string[]>>({})
  const [showContradictionAlert, setShowContradictionAlert] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const questionInputRef = useRef<HTMLTextAreaElement>(null)

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

  // 切换审讯模式
  const handleModeChange = (newMode: InterrogationMode) => {
    console.info('[InterrogationPage] 切换审讯模式', { from: mode, to: newMode })
    setMode(newMode)
    setConversationHistory([])
    setGroupMessages([])
    setLieDetection(null)
    setContradictions([])

    if (newMode === 'group') {
      setTimeout(() => {
        addWatsonMessage(
          '好的，现在我们把所有人都召集到一起。记住，你可以@某个嫌疑人来直接提问。注意观察他们之间的互动——矛盾往往就在其中。',
          'encouragement'
        )
      }, 300)
    }
  }

  // 滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversationHistory, groupMessages, watsonMessages])

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

  // 处理@提及
  const handleQuestionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setQuestion(value)

    // 检查是否输入了@
    const lastAtIndex = value.lastIndexOf('@')
    if (lastAtIndex !== -1 && lastAtIndex > value.lastIndexOf(' ')) {
      const searchText = value.substring(lastAtIndex + 1).toLowerCase()
      const matchingSuspects = gameState?.case?.suspects?.filter(s =>
        s.name.toLowerCase().includes(searchText)
      ) || []

      if (matchingSuspects.length > 0) {
        setMentionedSuspects(matchingSuspects.map(s => ({ id: s.id, name: s.name })))
        setShowMentionMenu(true)
        // 计算菜单位置
        if (questionInputRef.current) {
          const rect = questionInputRef.current.getBoundingClientRect()
          setMentionMenuPosition({ x: 10, y: rect.height - 100 })
        }
      } else {
        setShowMentionMenu(false)
      }
    } else {
      setShowMentionMenu(false)
    }
  }

  // 选择@的嫌疑人
  const handleMentionSelect = (suspect: MentionedSuspect) => {
    const lastAtIndex = question.lastIndexOf('@')
    const newQuestion = question.substring(0, lastAtIndex) + `@${suspect.name} `
    setQuestion(newQuestion)
    setShowMentionMenu(false)

    // 添加到提及列表（用于发送时）
    if (!mentionedSuspects.find(s => s.id === suspect.id)) {
      setMentionedSuspects(prev => [...prev, suspect])
    }

    // 聚焦输入框
    setTimeout(() => questionInputRef.current?.focus(), 0)
  }

  // 添加全体质询消息
  const addGroupMessage = (
    role: GroupMessage['role'],
    content: string,
    suspectId?: string,
    suspectName?: string
  ) => {
    const message: GroupMessage = {
      id: `group-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      role,
      content,
      suspectId,
      suspectName,
      timestamp: new Date().toISOString(),
    }
    console.info('[InterrogationPage] 全体质询消息', { role, content, suspectName })
    setGroupMessages(prev => [...prev, message])
  }

  // 记录嫌疑人陈述
  const recordSuspectStatement = (suspectId: string, statement: string) => {
    setSuspectStatements(prev => {
      const existing = prev[suspectId] || []
      return { ...prev, [suspectId]: [...existing, statement] }
    })
  }

  // 检查矛盾
  const checkForContradictions = useCallback(async () => {
    if (!gameId) return

    try {
      console.info('[InterrogationPage] 检查证词矛盾')
      const result = await gameApi.checkContradictions(gameId, [], suspectStatements)
      if (result.count > 0) {
        setContradictions(result.contradictions)
        setShowContradictionAlert(true)
        console.info('[InterrogationPage] 发现矛盾', result.contradictions)

        // 华生指出矛盾
        setTimeout(() => {
          addWatsonMessage(
            `等等！我发现了一个矛盾！${result.contradictions[0].description}`,
            'observation'
          )
        }, 500)
      }
    } catch (err) {
      console.error('[InterrogationPage] 检查矛盾失败', err)
    }
  }, [gameId, suspectStatements, addWatsonMessage])

  // 嫌疑人插话
  const triggerSuspectInterjection = useCallback(async (
    respondingSuspectId: string,
    otherSuspectId: string,
    context: string
  ) => {
    if (!gameId) return

    // 检查插话次数
    const currentCount = interjectionCounts[respondingSuspectId] || 0
    if (currentCount >= 2) {
      console.debug('[InterrogationPage] 嫌疑人插话次数已达上限', { respondingSuspectId })
      return
    }

    try {
      const result = await gameApi.getSuspectInterjection(
        gameId,
        respondingSuspectId,
        otherSuspectId,
        context
      )

      if (result.interjection) {
        const respondingSuspect = gameState?.case?.suspects?.find(s => s.id === respondingSuspectId)
        addGroupMessage('interjection', result.interjection, respondingSuspectId, respondingSuspect?.name)

        // 更新插话计数
        setInterjectionCounts(prev => ({
          ...prev,
          [respondingSuspectId]: (prev[respondingSuspectId] || 0) + 1
        }))
      }
    } catch (err) {
      console.error('[InterrogationPage] 获取嫌疑人插话失败', err)
    }
  }, [gameId, interjectionCounts, gameState])

  // 控场操作
  const handleGroupControl = async (action: GroupControlAction, targetSuspectId?: string) => {
    if (!gameId) return

    try {
      console.info('[InterrogationPage] 控场操作', { action, targetSuspectId })
      const result = await gameApi.groupControl(gameId, action, targetSuspectId)
      addGroupMessage('system', result.message)
    } catch (err) {
      console.error('[InterrogationPage] 控场操作失败', err)
    }
  }

  // 发送问题（支持单独审讯和全体质询）
  const handleSendQuestion = async () => {
    if (!gameId || !question.trim() || isProcessing) return

    // 单独审讯模式需要选择嫌疑人
    if (mode === 'private' && !selectedSuspect) return

    console.info('[InterrogationPage] 发送问题', { mode, question: question.substring(0, 50) })
    setIsProcessing(true)

    try {
      if (mode === 'private') {
        // 单独审讯模式
        await sendPrivateQuestion()
      } else {
        // 全体质询模式
        await sendGroupQuestion()
      }
    } catch (err) {
      console.error('[InterrogationPage] 发送问题失败', err)
      setError(err instanceof Error ? err.message : '发送问题失败')
    } finally {
      setIsProcessing(false)
    }
  }

  // 发送单独审讯问题
  const sendPrivateQuestion = async () => {
    if (!gameId || !selectedSuspect) return

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
      true,
      []
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
  }

  // 发送全体质询问题
  const sendGroupQuestion = async () => {
    if (!gameId || !gameState?.case?.suspects) return

    // 解析@提及的嫌疑人
    const mentionedSuspectIds: string[] = []
    let targetSuspect = gameState.case.suspects[0] // 默认第一个

    for (const suspect of gameState.case.suspects) {
      if (question.includes(`@${suspect.name}`)) {
        mentionedSuspectIds.push(suspect.id)
        targetSuspect = suspect
      }
    }

    // 添加用户消息
    addGroupMessage('user', question)

    // 调用API获取回复
    const otherSuspectIds = gameState.case.suspects
      .map(s => s.id)
      .filter(id => id !== targetSuspect.id)

    const response = await gameApi.askSuspectQuestion(
      gameId,
      targetSuspect.id,
      question,
      [], // 全体质询使用新的对话历史
      false,
      otherSuspectIds
    )

    // 添加嫌疑人回复
    addGroupMessage('suspect', response.response, targetSuspect.id, targetSuspect.name)

    // 记录陈述
    recordSuspectStatement(targetSuspect.id, response.response)

    // 检查矛盾
    setTimeout(() => {
      checkForContradictions()
    }, 500)

    // 随机触发其他嫌疑人插话
    if (otherSuspectIds.length > 0 && Math.random() > 0.4) {
      const randomSuspectId = otherSuspectIds[Math.floor(Math.random() * otherSuspectIds.length)]
      setTimeout(() => {
        triggerSuspectInterjection(randomSuspectId, targetSuspect.id, response.response)
      }, 1500)
    }

    // 华生评论
    if (Math.random() > 0.5) {
      setTimeout(() => {
        const comments = [
          '很好，继续观察他们的反应。',
          '注意他们之间的互动，这很有趣。',
          '我们来听听其他人怎么说。',
          '你觉得这个回答可信吗？',
        ]
        const randomIndex = Math.floor(Math.random() * comments.length)
        addWatsonMessage(comments[randomIndex], 'hint')
      }, 2000)
    }

    // 清空输入
    setQuestion('')
    setMentionedSuspects([])
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
                onClick={() => handleModeChange('group')}
                type="button"
              >
                圆桌对峙
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
          {/* 模式：单独审讯 */}
          {mode === 'private' && selectedSuspect && (
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
          )}

          {/* 模式：全体质询 */}
          {mode === 'group' && (
            <>
              {/* 全体嫌疑人展示 */}
              <div className="group-suspects-panel">
                <div className="panel-header">
                  <h3>在场嫌疑人</h3>
                  <span className="atmosphere-indicator">🌫️ 气氛紧张</span>
                </div>
                <div className="group-suspects-list">
                  {gameState.case?.suspects?.map(suspect => (
                    <div
                      key={suspect.id}
                      className={`group-suspect-item ${interjectionCounts[suspect.id] >= 2 ? 'group-suspect-item--quiet' : ''}`}
                    >
                      <div className="group-suspect-avatar">
                        {suspect.isGuilty ? '🔪' : '👤'}
                      </div>
                      <div className="group-suspect-info">
                        <div className="group-suspect-name">{suspect.name}</div>
                        <div className="group-suspect-status">
                          {interjectionCounts[suspect.id] >= 2 ? '（已安静）' : '（可插话）'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 矛盾检测警告 */}
              {showContradictionAlert && contradictions.length > 0 && (
                <div className="contradiction-alert" onClick={() => setShowContradictionAlert(false)}>
                  <div className="contradiction-alert__icon">⚠️</div>
                  <div className="contradiction-alert__content">
                    <div className="contradiction-alert__title">检测到证词矛盾！</div>
                    <div className="contradiction-alert__desc">
                      {contradictions[0].description}
                    </div>
                  </div>
                  <div className="contradiction-alert__close">×</div>
                </div>
              )}

              {/* 控场按钮 */}
              <div className="group-control-bar">
                <button
                  className="group-control-btn"
                  onClick={() => handleGroupControl('quiet')}
                  type="button"
                >
                  安静
                </button>
                <button
                  className="group-control-btn"
                  onClick={() => handleGroupControl('continue')}
                  type="button"
                >
                  继续
                </button>
              </div>

              {/* 全体质询对话区 */}
              <div className="conversation-area">
                <div className="conversation-messages">
                  {groupMessages.length === 0 ? (
                    <div className="no-messages">
                      <p>开始质询所有人吧！输入 @ 来提及特定嫌疑人。</p>
                    </div>
                  ) : (
                    groupMessages.map((msg) => (
                      <div key={msg.id} className={`message message--${msg.role}`}>
                        <div className="message-avatar">
                          {msg.role === 'user' ? '🔍' :
                           msg.role === 'watson' ? '👨‍⚕️' :
                           msg.role === 'system' ? '⚖️' :
                           msg.role === 'interjection' ? '💬' :
                           gameState.case?.suspects?.find(s => s.id === msg.suspectId)?.isGuilty ? '🔪' : '👤'}
                        </div>
                        <div className="message-content">
                          <div className="message-sender">
                            {msg.role === 'user' ? '你' :
                             msg.role === 'watson' ? '华生' :
                             msg.role === 'system' ? '系统' :
                             msg.role === 'interjection' ? `（${msg.suspectName}插话）` :
                             msg.suspectName}
                          </div>
                          <div className={`message-text ${msg.role === 'interjection' ? 'message-text--interjection' : ''}`}>
                            {msg.content}
                          </div>
                          <div className="message-time">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                  {isProcessing && (
                    <div className="message message--suspect">
                      <div className="message-avatar">👤</div>
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

                {/* 输入区 - 支持@提及 */}
                <div className="question-input-area question-input-area--group">
                  <div className="mention-input-wrapper">
                    <textarea
                      ref={questionInputRef}
                      className="question-input question-input--textarea"
                      placeholder="输入 @ 来提及嫌疑人，例如：@玛莎·佩恩 昨晚你在哪里？"
                      value={question}
                      onChange={handleQuestionChange}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSendQuestion()
                        }
                      }}
                      disabled={isProcessing}
                      rows={2}
                    />
                    {/* @提及菜单 */}
                    {showMentionMenu && mentionedSuspects.length > 0 && (
                      <div
                        className="mention-menu"
                        style={{
                          position: 'absolute',
                          bottom: mentionMenuPosition.y,
                          left: mentionMenuPosition.x,
                        }}
                      >
                        {mentionedSuspects.map(suspect => (
                          <div
                            key={suspect.id}
                            className="mention-menu-item"
                            onClick={() => handleMentionSelect(suspect)}
                          >
                            👤 {suspect.name}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
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
          )}

          {/* 未选择嫌疑人（仅单独审讯模式） */}
          {mode === 'private' && !selectedSuspect && (
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

        /* 全体质询 - 嫌疑人面板 */
        .group-suspects-panel {
          background: rgba(0, 0, 0, 0.4);
          border: 1px solid #333;
          border-radius: 8px;
          padding: 1rem;
        }

        .group-suspects-panel .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
          padding-bottom: 0.75rem;
          border-bottom: 1px solid #333;
        }

        .group-suspects-panel .panel-header h3 {
          color: #d4af37;
          font-size: 1.1rem;
        }

        .atmosphere-indicator {
          color: #ff9800;
          font-size: 0.9rem;
        }

        .group-suspects-list {
          display: flex;
          gap: 1rem;
          flex-wrap: wrap;
        }

        .group-suspect-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 1rem;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid #2a2a3a;
          border-radius: 6px;
          transition: all 0.3s ease;
        }

        .group-suspect-item--quiet {
          opacity: 0.5;
        }

        .group-suspect-avatar {
          width: 36px;
          height: 36px;
          background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.1rem;
        }

        .group-suspect-info {
          display: flex;
          flex-direction: column;
        }

        .group-suspect-name {
          color: #d4af37;
          font-weight: bold;
          font-size: 0.9rem;
        }

        .group-suspect-status {
          color: #666;
          font-size: 0.75rem;
        }

        /* 矛盾检测警告 */
        .contradiction-alert {
          background: rgba(255, 152, 0, 0.15);
          border: 2px solid rgba(255, 152, 0, 0.4);
          border-radius: 8px;
          padding: 1rem;
          display: flex;
          gap: 1rem;
          align-items: flex-start;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .contradiction-alert:hover {
          background: rgba(255, 152, 0, 0.2);
        }

        .contradiction-alert__icon {
          font-size: 1.5rem;
        }

        .contradiction-alert__content {
          flex: 1;
        }

        .contradiction-alert__title {
          color: #ff9800;
          font-weight: bold;
          font-size: 1rem;
          margin-bottom: 0.25rem;
        }

        .contradiction-alert__desc {
          color: #e8e8e8;
          font-size: 0.9rem;
          line-height: 1.5;
        }

        .contradiction-alert__close {
          color: #666;
          font-size: 1.25rem;
          cursor: pointer;
        }

        /* 控场按钮栏 */
        .group-control-bar {
          display: flex;
          gap: 0.75rem;
        }

        .group-control-btn {
          padding: 0.5rem 1rem;
          background: rgba(212, 175, 55, 0.1);
          border: 1px solid rgba(212, 175, 55, 0.3);
          color: #d4af37;
          border-radius: 6px;
          cursor: pointer;
          font-family: 'Georgia', serif;
          font-size: 0.9rem;
          transition: all 0.3s ease;
        }

        .group-control-btn:hover {
          background: rgba(212, 175, 55, 0.2);
          border-color: #d4af37;
        }

        /* 插话消息样式 */
        .message--interjection {
          opacity: 0.9;
        }

        .message-text--interjection {
          background: rgba(156, 39, 176, 0.1) !important;
          border-color: rgba(156, 39, 176, 0.3) !important;
          font-style: italic;
        }

        /* 全体质询输入区 */
        .question-input-area--group {
          position: relative;
        }

        .mention-input-wrapper {
          flex: 1;
          position: relative;
        }

        .question-input--textarea {
          resize: none;
          min-height: 60px;
          line-height: 1.5;
        }

        /* @提及菜单 */
        .mention-menu {
          position: absolute;
          background: #1a1a2e;
          border: 1px solid #d4af37;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
          z-index: 10;
          min-width: 200px;
        }

        .mention-menu-item {
          padding: 0.75rem 1rem;
          color: #e8e8e8;
          cursor: pointer;
          transition: background 0.2s ease;
        }

        .mention-menu-item:first-child {
          border-radius: 8px 8px 0 0;
        }

        .mention-menu-item:last-child {
          border-radius: 0 0 8px 8px;
        }

        .mention-menu-item:hover {
          background: rgba(212, 175, 55, 0.15);
        }

        .message--system .message-text {
          background: rgba(103, 58, 183, 0.1) !important;
          border-color: rgba(103, 58, 183, 0.3) !important;
          text-align: center;
        }

        .message--system .message-sender {
          display: none;
        }
      `}</style>
    </div>
  )
}
