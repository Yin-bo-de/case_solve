import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import type { Suspect, Witness, Expert } from '@/types/game'
import {
  gameApi,
  type ConversationMessage,
  type GroupControlAction,
} from '@/services/api'
import {
  useWatsonChatStore,
  useInterrogationStore,
  useCluesStore,
  useGameStore,
  type GroupMessage,
  type MentionedSuspect,
  type InterrogationMode,
} from '@/store'
import type { SelectedTab, ActorMessage } from '@/store/interrogationStore'
import { useGameSessionSync } from '@/hooks/useGameSessionSync'
import WatsonChatDialog from '@/components/WatsonChatDialog'
import { SelectableMessage } from '@/components/SelectableMessage'
import ExtractClueModal from '@/components/ExtractClueModal'
import WatsonTipsPanel from '@/components/WatsonTipsPanel'
import Toast from '@/components/Toast'
import ClueSelectorModal from '@/components/ClueSelectorModal'

export default function InterrogationPage() {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()

  const { gameState, isLoading, error, setError } = useGameStore()
  const { addWatsonMessage } = useWatsonChatStore()
  const { addClueFromBackend, clues } = useCluesStore()
  const {
    mode,
    setMode,
    selectedTab,
    setSelectedTab,
    conversationHistoryBySuspect,
    selectedSuspectId,
    getCurrentConversationHistory,
    addConversationMessage,
    lieDetection,
    setLieDetection,
    setSelectedSuspectId,
    groupMessages,
    addGroupMessage,
    mentionedSuspects,
    addMentionedSuspect,
    setMentionedSuspects,
    contradictions,
    setContradictions,
    interjectionCounts,
    updateInterjectionCount,
    suspectStatements,
    addSuspectStatement,
    setShowContradictionAlert,
    showContradictionAlert,
    watsonTips,
    watsonTipsLoading,
    fetchTips,
    extractClue,
    // witness
    selectedWitnessId,
    setSelectedWitnessId,
    witnessConversationsByWitnessId,
    addWitnessConversationMessage,
    witnessCredibilityCheck,
    setWitnessCredibilityCheck,
    witnessWatsonTips,
    witnessWatsonTipsLoading,
    fetchWitnessTips,
    // expert
    selectedExpertId,
    setSelectedExpertId,
    expertConversationsByExpertId,
    addExpertConversationMessage,
    expertReportLoadedById,
    markExpertReportLoaded,
    extractClueFromActor,
    // P2
    confrontLoading,
    confrontSuspectWithClue,
    // P3
    suspectStates,
  } = useInterrogationStore()

  const [selectedSuspect, setSelectedSuspect] = useState<Suspect | null>(null)
  const [selectedWitness, setSelectedWitness] = useState<Witness | null>(null)
  const [selectedExpert, setSelectedExpert] = useState<Expert | null>(null)
  const [question, setQuestion] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  // 记录当前正在生成回复的角色ID，防止切换角色后看到错误的打字动画
  const [processingActorId, setProcessingActorId] = useState<string | null>(null)
  const [pendingExtractText, setPendingExtractText] = useState<string | null>(null)
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('线索已成功提取！')
  const [showClueSelector, setShowClueSelector] = useState(false)

  // 全体质询相关UI状态（不需要持久化）
  const [showMentionMenu, setShowMentionMenu] = useState(false)
  const [mentionMenuPosition, setMentionMenuPosition] = useState({ x: 0, y: 0 })
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const questionInputRef = useRef<HTMLTextAreaElement>(null)

  console.debug('[InterrogationPage] 渲染审讯页面', { gameId, mode, selectedTab })

  // ---------- 初始化与恢复 ----------

  // gameState 就绪时初始化默认选中嫌疑人
  useEffect(() => {
    if (gameState?.case?.suspects && gameState.case.suspects.length > 0 && !selectedSuspect) {
      setSelectedSuspect(gameState.case.suspects[0])
      setSelectedSuspectId(gameState.case.suspects[0].id)
    }
  }, [gameState?.case?.suspects, selectedSuspect])

  // 从持久化的 selectedWitnessId 恢复 selectedWitness 对象
  useEffect(() => {
    if (selectedWitnessId && gameState?.case?.witnesses) {
      const found = gameState.case.witnesses.find(w => w.id === selectedWitnessId)
      if (found) setSelectedWitness(found)
    }
  }, [selectedWitnessId, gameState?.case?.witnesses])

  // 从持久化的 selectedExpertId 恢复 selectedExpert 对象
  useEffect(() => {
    if (selectedExpertId && gameState?.case?.experts) {
      const found = gameState.case.experts.find(e => e.id === selectedExpertId)
      if (found) setSelectedExpert(found)
    }
  }, [selectedExpertId, gameState?.case?.experts])

  // 切换到证人/专家 Tab 时自动选中第一个
  useEffect(() => {
    if (selectedTab === 'witnesses' && gameState?.case?.witnesses?.length) {
      const first = gameState.case.witnesses[0]
      setSelectedWitness(first)
      setSelectedWitnessId(first.id)
    } else if (selectedTab === 'experts' && gameState?.case?.experts?.length) {
      const first = gameState.case.experts[0]
      setSelectedExpert(first)
      setSelectedExpertId(first.id)
    }
  }, [selectedTab]) // eslint-disable-line react-hooks/exhaustive-deps

  // 专家 Tab 进入时自动加载初步法医报告
  useEffect(() => {
    if (selectedTab !== 'experts' || !selectedExpert || !gameId) return
    if (expertReportLoadedById[selectedExpert.id]) return

    const expertId = selectedExpert.id
    console.info('[InterrogationPage] 自动加载专家初步报告', { gameId, expertId })

    gameApi.getExpertPreliminaryReport(gameId, expertId)
      .then(data => {
        const reportMsg: ActorMessage = {
          role: 'expert',
          content: data.preliminaryReport,
          timestamp: new Date().toISOString(),
        }
        addExpertConversationMessage(reportMsg, expertId)
        markExpertReportLoaded(expertId)
        console.info('[InterrogationPage] 专家初步报告已加载', { expertId })
      })
      .catch(err => console.error('[InterrogationPage] 加载专家初步报告失败', err))
  }, [selectedTab, selectedExpert?.id, gameId, expertReportLoadedById]) // eslint-disable-line react-hooks/exhaustive-deps

  // 滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversationHistoryBySuspect, selectedSuspectId, groupMessages, witnessConversationsByWitnessId, expertConversationsByExpertId])

  // 重置 @ 菜单索引
  useEffect(() => {
    if (!showMentionMenu) setSelectedMentionIndex(0)
  }, [showMentionMenu])

  useGameSessionSync(gameId)

  // ---------- Tab 切换 ----------

  const handleTabChange = (tab: SelectedTab) => {
    // 切换到证人/专家时强制锁定为 private 模式
    if (tab !== 'suspects' && mode === 'group') {
      setMode('private')
      console.info('[InterrogationPage] 切换至非嫌疑人 Tab，强制锁定 private 模式')
    }
    setSelectedTab(tab)
  }

  // ---------- 审讯模式切换 ----------

  const handleModeChange = (newMode: InterrogationMode) => {
    console.info('[InterrogationPage] 切换审讯模式', { from: mode, to: newMode })
    setMode(newMode)

    if (newMode === 'group') {
      setTimeout(() => {
        addWatsonMessage(
          '好的，现在我们把所有人都召集到一起。记住，你可以@某个嫌疑人来直接提问。注意观察他们之间的互动——矛盾往往就在其中。',
          'encouragement'
        )
      }, 300)
    }
  }

  // ---------- 嫌疑人选择 ----------

  const handleSuspectSelect = (suspect: Suspect) => {
    console.debug('[InterrogationPage] 选择嫌疑人', { suspectId: suspect.id })
    setSelectedSuspect(suspect)
    setSelectedSuspectId(suspect.id)
    setLieDetection(null)

    if (Math.random() > 0.3) {
      const comments = [
        `让我们问问${suspect.name}昨晚在哪里。`,
        `或许我们应该了解一下${suspect.name}和死者的关系。`,
        `我很好奇${suspect.name}对这起案件有什么看法。`,
      ]
      addWatsonMessage(comments[Math.floor(Math.random() * comments.length)], 'suspect_analysis')
    }
  }

  // ---------- 证人选择 ----------

  const handleWitnessSelect = (witness: Witness) => {
    console.debug('[InterrogationPage] 选择证人', { witnessId: witness.id })
    setSelectedWitness(witness)
    setSelectedWitnessId(witness.id)
    setWitnessCredibilityCheck(null)
  }

  // ---------- 专家选择 ----------

  const handleExpertSelect = (expert: Expert) => {
    console.debug('[InterrogationPage] 选择专家', { expertId: expert.id })
    setSelectedExpert(expert)
    setSelectedExpertId(expert.id)
  }

  // ---------- @提及处理 ----------

  const handleQuestionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setQuestion(value)

    const lastAtIndex = value.lastIndexOf('@')
    if (lastAtIndex !== -1 && lastAtIndex > value.lastIndexOf(' ')) {
      const searchText = value.substring(lastAtIndex + 1).toLowerCase()
      const matchingSuspects = gameState?.case?.suspects?.filter(s =>
        s.name.toLowerCase().includes(searchText)
      ) || []

      if (matchingSuspects.length > 0) {
        setMentionedSuspects(matchingSuspects.map(s => ({ id: s.id, name: s.name })))
        setShowMentionMenu(true)
        setSelectedMentionIndex(0)
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

  const handleMentionSelect = (suspect: MentionedSuspect) => {
    const lastAtIndex = question.lastIndexOf('@')
    const newQuestion = question.substring(0, lastAtIndex) + `@${suspect.name} `
    setQuestion(newQuestion)
    setShowMentionMenu(false)
    setSelectedMentionIndex(0)
    addMentionedSuspect(suspect)
    setTimeout(() => questionInputRef.current?.focus(), 0)
  }

  // ---------- 全体质询辅助 ----------

  const createAndAddGroupMessage = (
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
    addGroupMessage(message)
  }

  const checkForContradictions = useCallback(async () => {
    if (!gameId) return
    try {
      const result = await gameApi.checkContradictions(gameId, [], suspectStatements)
      if (result.count > 0) {
        setContradictions(result.contradictions)
        setShowContradictionAlert(true)
        setTimeout(() => {
          addWatsonMessage(
            `等等！我发现了一个矛盾！${result.contradictions[0].description}`,
            'suspect_analysis'
          )
        }, 500)
      }
    } catch (err) {
      console.error('[InterrogationPage] 检查矛盾失败', err)
    }
  }, [gameId, suspectStatements, addWatsonMessage])

  const triggerSuspectInterjection = useCallback(async (
    respondingSuspectId: string,
    otherSuspectId: string,
    context: string
  ) => {
    if (!gameId) return
    const currentCount = interjectionCounts[respondingSuspectId] || 0
    if (currentCount >= 2) return

    try {
      const result = await gameApi.getSuspectInterjection(gameId, respondingSuspectId, otherSuspectId, context)
      if (result.interjection) {
        const respondingSuspect = gameState?.case?.suspects?.find(s => s.id === respondingSuspectId)
        createAndAddGroupMessage('interjection', result.interjection, respondingSuspectId, respondingSuspect?.name)
        updateInterjectionCount(respondingSuspectId, 1)
      }
    } catch (err) {
      console.error('[InterrogationPage] 获取嫌疑人插话失败', err)
    }
  }, [gameId, interjectionCounts, gameState])

  const handleGroupControl = async (action: GroupControlAction, targetSuspectId?: string) => {
    if (!gameId) return
    try {
      const result = await gameApi.groupControl(gameId, action, targetSuspectId)
      createAndAddGroupMessage('system', result.message)
    } catch (err) {
      console.error('[InterrogationPage] 控场操作失败', err)
    }
  }

  // ---------- 发送问题：嫌疑人（单独） ----------

  const sendPrivateQuestion = async () => {
    if (!gameId || !selectedSuspect) return
    const targetSuspectId = selectedSuspect.id
    const targetSuspectName = selectedSuspect.name
    setProcessingActorId(targetSuspectId)

    const userMessage: ConversationMessage = {
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    }
    addConversationMessage(userMessage, targetSuspectId)

    const historyBeforeApi = getCurrentConversationHistory(targetSuspectId)
    const response = await gameApi.askSuspectQuestion(
      gameId,
      targetSuspectId,
      question,
      historyBeforeApi,
      true,
      []
    )

    addConversationMessage(
      { role: 'suspect', content: response.response, timestamp: new Date().toISOString() },
      targetSuspectId
    )

    const newLieDetection = response.lieDetection ?? null
    setLieDetection(newLieDetection)

    if (newLieDetection?.lieDetected && newLieDetection.microexpression) {
      setTimeout(() => {
        addWatsonMessage(
          `你注意到了吗？${targetSuspectName}${newLieDetection.microexpression}。我觉得${newLieDetection.notes || '这里有点可疑'}。`,
          'suspect_analysis'
        )
      }, 800)
    } else if (Math.random() > 0.5) {
      setTimeout(() => {
        const comments = ['这回答有点意思。你怎么看？', '我不确定是否完全相信这个说法。', '我们应该继续追问这个话题。', '让我想想...这和我们知道的其他信息一致吗？']
        addWatsonMessage(comments[Math.floor(Math.random() * comments.length)], 'guidance')
      }, 1000)
    }

    setQuestion('')

    const currentHistory = getCurrentConversationHistory(targetSuspectId)
    fetchTips(gameId, targetSuspectId, [...currentHistory, { role: 'user', content: question }, { role: 'suspect', content: response.response }])
  }

  // ---------- 发送问题：嫌疑人（全体） ----------

  const sendGroupQuestion = async () => {
    if (!gameId || !gameState?.case?.suspects) return
    setProcessingActorId('group')

    const mentionedSuspectIds: string[] = []
    let targetSuspect = gameState.case.suspects[0]

    for (const suspect of gameState.case.suspects) {
      if (question.includes(`@${suspect.name}`)) {
        mentionedSuspectIds.push(suspect.id)
        targetSuspect = suspect
      }
    }

    createAndAddGroupMessage('user', question)

    const otherSuspectIds = gameState.case.suspects.map(s => s.id).filter(id => id !== targetSuspect.id)
    const response = await gameApi.askSuspectQuestion(gameId, targetSuspect.id, question, [], false, otherSuspectIds)

    createAndAddGroupMessage('suspect', response.response, targetSuspect.id, targetSuspect.name)
    addSuspectStatement(targetSuspect.id, response.response)

    setTimeout(() => checkForContradictions(), 500)

    if (otherSuspectIds.length > 0 && Math.random() > 0.4) {
      const randomSuspectId = otherSuspectIds[Math.floor(Math.random() * otherSuspectIds.length)]
      setTimeout(() => triggerSuspectInterjection(randomSuspectId, targetSuspect.id, response.response), 1500)
    }

    if (Math.random() > 0.5) {
      setTimeout(() => {
        const comments = ['很好，继续观察他们的反应。', '注意他们之间的互动，这很有趣。', '我们来听听其他人怎么说。', '你觉得这个回答可信吗？']
        addWatsonMessage(comments[Math.floor(Math.random() * comments.length)], 'guidance')
      }, 2000)
    }

    setQuestion('')
    setMentionedSuspects([])
  }

  // ---------- 发送问题：证人 ----------

  const sendWitnessQuestion = async () => {
    if (!gameId || !selectedWitness) return
    const witnessId = selectedWitness.id
    setProcessingActorId(witnessId)

    const userMsg: ActorMessage = { role: 'user', content: question, timestamp: new Date().toISOString() }
    addWitnessConversationMessage(userMsg, witnessId)

    const historyForApi = (witnessConversationsByWitnessId[witnessId] || []).map(m => ({
      role: m.role,
      content: m.content,
    })) as ConversationMessage[]

    const result = await gameApi.askWitnessQuestion(gameId, witnessId, question, historyForApi)

    addWitnessConversationMessage(
      { role: 'witness', content: result.response, timestamp: new Date().toISOString() },
      witnessId
    )
    setWitnessCredibilityCheck(result.credibilityCheck)

    // 获取证人审讯华生提示
    const updatedHistory = [
      ...(witnessConversationsByWitnessId[witnessId] || []),
      userMsg,
      { role: 'witness' as const, content: result.response },
    ]
    fetchWitnessTips(gameId, witnessId, updatedHistory)

    setQuestion('')
  }

  // ---------- 发送问题：专家 ----------

  const sendExpertQuestion = async () => {
    if (!gameId || !selectedExpert) return
    const expertId = selectedExpert.id
    setProcessingActorId(expertId)

    const userMsg: ActorMessage = { role: 'user', content: question, timestamp: new Date().toISOString() }
    addExpertConversationMessage(userMsg, expertId)

    const historyForApi = (expertConversationsByExpertId[expertId] || []).map(m => ({
      role: m.role,
      content: m.content,
    })) as ConversationMessage[]

    const result = await gameApi.askExpertQuestion(gameId, expertId, question, historyForApi)

    addExpertConversationMessage(
      { role: 'expert', content: result.response, timestamp: new Date().toISOString() },
      expertId
    )

    setQuestion('')
  }

  // ---------- 统一发送入口 ----------

  const handleSendQuestion = async () => {
    if (!gameId || !question.trim() || isProcessing) return
    if (selectedTab === 'suspects' && mode === 'private' && !selectedSuspect) return

    console.info('[InterrogationPage] 发送问题', { selectedTab, mode, question: question.substring(0, 50) })
    setIsProcessing(true)

    try {
      if (selectedTab === 'witnesses') {
        await sendWitnessQuestion()
      } else if (selectedTab === 'experts') {
        await sendExpertQuestion()
      } else if (mode === 'private') {
        await sendPrivateQuestion()
      } else {
        await sendGroupQuestion()
      }
    } catch (err) {
      console.error('[InterrogationPage] 发送问题失败', err)
      setError(err instanceof Error ? err.message : '发送问题失败')
    } finally {
      setIsProcessing(false)
      setProcessingActorId(null)
    }
  }

  // ---------- 提取线索（嫌疑人） ----------

  const handleExtractConfirm = async (userLabel: string) => {
    if (!gameId || !pendingExtractText) return
    try {
      let clue
      if (selectedTab === 'witnesses' && selectedWitness) {
        clue = await extractClueFromActor(gameId, {
          actorType: 'witness',
          actorId: selectedWitness.id,
          quotedText: pendingExtractText,
          contextMessages: witnessConversationsByWitnessId[selectedWitness.id] || [],
          userLabel,
        })
      } else if (selectedTab === 'experts' && selectedExpert) {
        clue = await extractClueFromActor(gameId, {
          actorType: 'expert',
          actorId: selectedExpert.id,
          quotedText: pendingExtractText,
          contextMessages: expertConversationsByExpertId[selectedExpert.id] || [],
          userLabel,
        })
      } else if (selectedSuspect) {
        clue = await extractClue(gameId, {
          suspectId: selectedSuspect.id,
          quotedText: pendingExtractText,
          contextMessages: getCurrentConversationHistory(selectedSuspect.id),
          userLabel,
        })
      }

      if (clue) {
        addClueFromBackend(clue)
        setToastMessage('线索已成功提取！')
        setShowToast(true)
      }
    } catch (err) {
      console.error('[InterrogationPage] 提取线索失败', err)
    } finally {
      setPendingExtractText(null)
    }
  }

  // ---------- 出示线索对质 ----------

  const handleConfrontClue = async (clueId: string, clueLabel: string) => {
    if (!gameId || !selectedSuspect) return
    setShowClueSelector(false)
    console.info('[InterrogationPage] 出示线索对质', { clueId, clueLabel, suspectId: selectedSuspect.id })

    const history = getCurrentConversationHistory(selectedSuspect.id)
    const result = await confrontSuspectWithClue(gameId, selectedSuspect.id, clueId, clueLabel, history)

    // P3: 状态迁移 Toast 提示
    const statusDelta = (result as any)?.statusDelta
    if (statusDelta && statusDelta.from !== statusDelta.to) {
      const stateLabels: Record<string, string> = {
        calm: '冷静',
        pressured: '承压',
        broken: '崩溃',
      }
      const fromLabel = stateLabels[statusDelta.from] || statusDelta.from
      const toLabel = stateLabels[statusDelta.to] || statusDelta.to
      setToastMessage(`${selectedSuspect.name} 的语气变了…… (${fromLabel} → ${toLabel})`)
      setShowToast(true)
    }
  }

  // ---------- 动态文案 ----------

  const headerTitle =
    selectedTab === 'experts' ? '法医咨询' :
    selectedTab === 'witnesses' ? '证人问询' :
    mode === 'private' ? '单独审讯' : '全体质询'

  const inputPlaceholder =
    selectedTab === 'witnesses' ? '询问目击者...' :
    selectedTab === 'experts' ? '询问法医...' :
    selectedSuspect ? `询问${selectedSuspect.name}...` : '请先选择嫌疑人...'

  // ---------- 可信度卡片（证人专用） ----------

  const renderCredibilityCard = () => {
    if (!witnessCredibilityCheck) return null
    const { credibilityConcern, concernType, confidence, microexpression, notes } = witnessCredibilityCheck
    const icon = concernType === 'bribery' ? '⚠️' : concernType === 'memory_gap' ? '🤔' : credibilityConcern ? '⚠️' : '✓'
    const title = !credibilityConcern ? '证词前后一致' :
      concernType === 'bribery' ? '证人有所保留' :
      concernType === 'fear' ? '证人流露出迟疑' : '证人存在记忆偏差'
    const variantClass = credibilityConcern ? 'credibility-check--warning' : 'credibility-check--ok'

    return (
      <div className={`credibility-check ${variantClass}`}>
        <div className="credibility-check__icon">{icon}</div>
        <div className="credibility-check__content">
          <div className="credibility-check__title">{title}</div>
          {microexpression && (
            <div className="credibility-check__microexpression">观察: {microexpression}</div>
          )}
          <div className="credibility-check__confidence">可信度参考: {(confidence * 100).toFixed(0)}%</div>
          {notes && <div className="credibility-check__notes">{notes}</div>}
        </div>
      </div>
    )
  }

  // ---------- 加载与错误状态 ----------

  if (isLoading) {
    return (
      <div className="interrogation-page interrogation-page--loading">
        <div className="loading-spinner"><p>正在进入审讯室...</p></div>
      </div>
    )
  }

  if (error || !gameState) {
    return (
      <div className="interrogation-page interrogation-page--error">
        <div className="error-message">
          <h2>出错了</h2>
          <p>{error || '无法加载游戏'}</p>
          <button onClick={() => navigate('/')} type="button">返回贝克街</button>
        </div>
      </div>
    )
  }

  const witnesses = gameState.case?.witnesses || []
  const experts = gameState.case?.experts || []
  const suspects = gameState.case?.suspects || []

  // ---------- JSX ----------

  return (
    <div className="interrogation-page">
      {/* 顶部导航栏 */}
      <header className="interrogation-header">
        <div className="header-content">
          <h1 className="header-title">{headerTitle}</h1>
          <div className="header-info">
            <span className="mode-toggle">
              <button
                className={`mode-button ${mode === 'private' ? 'mode-button--active' : ''}`}
                onClick={() => setMode('private')}
                disabled={selectedTab !== 'suspects'}
                type="button"
              >
                密室问话
              </button>
              <button
                className={`mode-button ${mode === 'group' ? 'mode-button--active' : ''}`}
                onClick={() => handleModeChange('group')}
                disabled={selectedTab !== 'suspects'}
                title={selectedTab !== 'suspects' ? '圆桌对峙仅限嫌疑人参与' : undefined}
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
        {/* 左栏：3 Tab 角色面板 */}
        <aside className="actors-panel">
          {/* Tab 切换 */}
          <div className="actor-tabs">
            <button
              className={`actor-tab ${selectedTab === 'suspects' ? 'actor-tab--active' : ''}`}
              onClick={() => handleTabChange('suspects')}
              type="button"
            >
              嫌疑人<span className="actor-tab__count">{suspects.length}</span>
            </button>
            <button
              className={`actor-tab ${selectedTab === 'witnesses' ? 'actor-tab--active' : ''}`}
              onClick={() => handleTabChange('witnesses')}
              type="button"
            >
              证人<span className="actor-tab__count">{witnesses.length}</span>
            </button>
            <button
              className={`actor-tab ${selectedTab === 'experts' ? 'actor-tab--active' : ''}`}
              onClick={() => handleTabChange('experts')}
              type="button"
            >
              专家<span className="actor-tab__count">{experts.length}</span>
            </button>
          </div>

          {/* 列表 */}
          <div className="panel-content">
            {/* 嫌疑人列表 */}
            {selectedTab === 'suspects' && (
              <ul className="suspect-list">
                {suspects.map(suspect => {
                  const state = suspectStates[suspect.id] || 'calm'
                  const stateBadgeClass = `suspect-state-badge--${state}`
                  const stateLabel = state === 'calm' ? '冷静' : state === 'pressured' ? '承压' : '崩溃'
                  return (
                    <li
                      key={suspect.id}
                      className={`suspect-item ${selectedSuspect?.id === suspect.id ? 'suspect-item--selected' : ''} suspect-item--${state}`}
                      onClick={() => handleSuspectSelect(suspect)}
                    >
                      <div className="suspect-avatar">{suspect.isGuilty ? '🔪' : '👤'}</div>
                      <div className="suspect-info">
                        <div className="suspect-name">
                          {suspect.name}
                          <span className={`suspect-state-badge ${stateBadgeClass}`}>{stateLabel}</span>
                        </div>
                        <div className="suspect-age">{suspect.age}岁</div>
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}

            {/* 证人列表 */}
            {selectedTab === 'witnesses' && (
              <ul className="suspect-list">
                {witnesses.length === 0 && (
                  <li className="actor-list-empty">暂无证人</li>
                )}
                {witnesses.map(witness => (
                  <li
                    key={witness.id}
                    className={`suspect-item ${selectedWitness?.id === witness.id ? 'suspect-item--selected' : ''}`}
                    onClick={() => handleWitnessSelect(witness)}
                  >
                    <div className="suspect-avatar witness-badge">👁️</div>
                    <div className="suspect-info">
                      <div className="suspect-name">{witness.name}</div>
                      <div className="suspect-age">{witness.occupation}</div>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            {/* 专家列表 */}
            {selectedTab === 'experts' && (
              <ul className="suspect-list">
                {experts.length === 0 && (
                  <li className="actor-list-empty">暂无专家</li>
                )}
                {experts.map(expert => (
                  <li
                    key={expert.id}
                    className={`suspect-item ${selectedExpert?.id === expert.id ? 'suspect-item--selected' : ''}`}
                    onClick={() => handleExpertSelect(expert)}
                  >
                    <div className="suspect-avatar expert-badge">🔬</div>
                    <div className="suspect-info">
                      <div className="suspect-name">{expert.name}</div>
                      <div className="suspect-age">{expert.title}</div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>

        {/* 审讯对话区 */}
        <section className="interrogation-room">

          {/* === 嫌疑人 Tab === */}
          {selectedTab === 'suspects' && (
            <>
              {/* 模式：单独审讯 */}
              {mode === 'private' && selectedSuspect && (
                <>
                  <div className="current-suspect">
                    <div className="suspect-header">
                      <div className="suspect-avatar-large">{selectedSuspect.isGuilty ? '🔪' : '👤'}</div>
                      <div className="suspect-details">
                        <h2>
                          {selectedSuspect.name}
                          {(() => {
                            const state = suspectStates[selectedSuspect.id] || 'calm'
                            const stateLabel = state === 'calm' ? '冷静' : state === 'pressured' ? '承压' : '崩溃'
                            return (
                              <span className={`suspect-state-badge suspect-state-badge--${state}`}>
                                {stateLabel}
                              </span>
                            )
                          })()}
                        </h2>
                        <p className="suspect-background">{selectedSuspect.background}</p>
                        <div className="suspect-tags">
                          {selectedSuspect.personalityTraits?.map((trait: string, i: number) => (
                            <span key={i} className="personality-tag">{trait}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="conversation-area conversation-area--with-tips">
                    {selectedSuspect?.timeline && (
                      <div className="actor-timeline-card">
                        <div className="actor-timeline-card__header">⏱ 时间线</div>
                        <div className="actor-timeline-card__body">
                          <div className="actor-timeline-card__bar" />
                          <p className="actor-timeline-card__text">{selectedSuspect.timeline}</p>
                        </div>
                      </div>
                    )}
                    <div className="conversation-messages">
                      {(() => {
                        const currentHistory = getCurrentConversationHistory()
                        return currentHistory.length === 0 ? (
                          <div className="no-messages"><p>开始询问{selectedSuspect.name}吧。</p></div>
                        ) : (
                          currentHistory.map((msg, idx) => (
                            <div key={idx} className={`message message--${msg.role}`}>
                              <div className="message-avatar">
                                {msg.role === 'user' ? '🔍' : selectedSuspect.isGuilty ? '🔪' : '👤'}
                              </div>
                              <div className="message-content">
                                {msg.role === 'suspect' ? (
                                  <SelectableMessage
                                    text={msg.content}
                                    senderName={selectedSuspect.name}
                                    onExtract={(text) => setPendingExtractText(text)}
                                  />
                                ) : msg.content.startsWith('【出示线索】') ? (
                                  <>
                                    <div className="message-sender">你</div>
                                    <div className="message-text message-text--clue-confront">
                                      {msg.content.replace('【出示线索】', '')}
                                    </div>
                                  </>
                                ) : (
                                  <>
                                    <div className="message-sender">你</div>
                                    <div className="message-text">{msg.content}</div>
                                  </>
                                )}
                                {msg.timestamp && (
                                  <div className="message-time">{new Date(msg.timestamp).toLocaleTimeString()}</div>
                                )}
                              </div>
                            </div>
                          ))
                        )
                      })()}
                      {lieDetection && (
                        <div className={`lie-detection lie-detection--${lieDetection.lie_detected ? 'warning' : 'ok'}`}>
                          <div className="lie-detection-icon">{lieDetection.lie_detected ? '⚠️' : '✓'}</div>
                          <div className="lie-detection-content">
                            <div className="lie-detection-title">
                              {lieDetection.lie_detected ? '检测到可能的谎言' : '言辞一致'}
                            </div>
                            {lieDetection.microexpression && (
                              <div className="lie-detection-microexpression">微表情: {lieDetection.microexpression}</div>
                            )}
                            <div className="lie-detection-confidence">置信度: {(lieDetection.confidence * 100).toFixed(0)}%</div>
                            <div className="lie-detection-notes">{lieDetection.notes}</div>
                          </div>
                        </div>
                      )}
                      {isProcessing && processingActorId === selectedSuspect?.id && (
                        <div className="message message--suspect">
                          <div className="message-avatar">{selectedSuspect.isGuilty ? '🔪' : '👤'}</div>
                          <div className="message-content">
                            <div className="suspect-typing">
                              <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
                            </div>
                          </div>
                        </div>
                      )}
                      <div ref={messagesEndRef} />
                    </div>

                    <div className="question-input-area">
                      <button
                        className="confront-clue-btn"
                        onClick={() => setShowClueSelector(true)}
                        disabled={isProcessing || confrontLoading}
                        type="button"
                        title="出示线索"
                      >
                        出示线索
                      </button>
                      <input
                        type="text"
                        className="question-input"
                        placeholder={inputPlaceholder}
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendQuestion() }
                        }}
                        disabled={isProcessing || confrontLoading}
                      />
                      <button
                        className="send-button"
                        onClick={handleSendQuestion}
                        disabled={!question.trim() || isProcessing || confrontLoading}
                        type="button"
                      >
                        发送
                      </button>
                    </div>
                  </div>

                  <WatsonTipsPanel tips={watsonTips} isLoading={watsonTipsLoading} />
                </>
              )}

              {/* 模式：全体质询 */}
              {mode === 'group' && (
                <>
                  <div className="group-suspects-panel">
                    <div className="panel-header">
                      <h3>在场嫌疑人</h3>
                      <span className="atmosphere-indicator">🌫️ 气氛紧张</span>
                    </div>
                    <div className="group-suspects-list">
                      {suspects.map(suspect => (
                        <div
                          key={suspect.id}
                          className={`group-suspect-item ${interjectionCounts[suspect.id] >= 2 ? 'group-suspect-item--quiet' : ''}`}
                        >
                          <div className="group-suspect-avatar">{suspect.isGuilty ? '🔪' : '👤'}</div>
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

                  {showContradictionAlert && contradictions.length > 0 && (
                    <div className="contradiction-alert" onClick={() => setShowContradictionAlert(false)}>
                      <div className="contradiction-alert__icon">⚠️</div>
                      <div className="contradiction-alert__content">
                        <div className="contradiction-alert__title">检测到证词矛盾！</div>
                        <div className="contradiction-alert__desc">{contradictions[0].description}</div>
                      </div>
                      <div className="contradiction-alert__close">×</div>
                    </div>
                  )}

                  <div className="group-control-bar">
                    <button className="group-control-btn" onClick={() => handleGroupControl('quiet')} type="button">安静</button>
                    <button className="group-control-btn" onClick={() => handleGroupControl('continue')} type="button">继续</button>
                  </div>

                  <div className="conversation-area">
                    <div className="conversation-messages">
                      {groupMessages.length === 0 ? (
                        <div className="no-messages"><p>开始质询所有人吧！输入 @ 来提及特定嫌疑人。</p></div>
                      ) : (
                        groupMessages.map((msg) => (
                          <div key={msg.id} className={`message message--${msg.role}`}>
                            <div className="message-avatar">
                              {msg.role === 'user' ? '🔍' :
                               msg.role === 'watson' ? '👨‍⚕️' :
                               msg.role === 'system' ? '⚖️' :
                               msg.role === 'interjection' ? '💬' :
                               suspects.find(s => s.id === msg.suspectId)?.isGuilty ? '🔪' : '👤'}
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
                              <div className="message-time">{new Date(msg.timestamp).toLocaleTimeString()}</div>
                            </div>
                          </div>
                        ))
                      )}
                      {isProcessing && processingActorId === 'group' && (
                        <div className="message message--suspect">
                          <div className="message-avatar">👤</div>
                          <div className="message-content">
                            <div className="suspect-typing">
                              <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
                            </div>
                          </div>
                        </div>
                      )}
                      <div ref={messagesEndRef} />
                    </div>

                    <div className="question-input-area question-input-area--group">
                      <div className="mention-input-wrapper">
                        <textarea
                          ref={questionInputRef}
                          className="question-input question-input--textarea"
                          placeholder="输入 @ 来提及嫌疑人，例如：@玛莎·佩恩 昨晚你在哪里？"
                          value={question}
                          onChange={handleQuestionChange}
                          onKeyDown={(e) => {
                            if (showMentionMenu && mentionedSuspects.length > 0) {
                              if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedMentionIndex((prev) => (prev + 1) % mentionedSuspects.length) }
                              else if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedMentionIndex((prev) => (prev - 1 + mentionedSuspects.length) % mentionedSuspects.length) }
                              else if (e.key === 'Enter') { e.preventDefault(); handleMentionSelect(mentionedSuspects[selectedMentionIndex]) }
                            } else if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendQuestion() }
                          }}
                          disabled={isProcessing}
                          rows={2}
                        />
                        {showMentionMenu && mentionedSuspects.length > 0 && (
                          <div className="mention-menu" style={{ position: 'absolute', bottom: mentionMenuPosition.y, left: mentionMenuPosition.x }}>
                            {mentionedSuspects.map((suspect, index) => (
                              <div
                                key={suspect.id}
                                className={`mention-menu-item ${index === selectedMentionIndex ? 'mention-menu-item--active' : ''}`}
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

              {mode === 'private' && !selectedSuspect && (
                <div className="no-suspect-selected"><p>请选择一个嫌疑人开始审讯</p></div>
              )}
            </>
          )}

          {/* === 证人 Tab === */}
          {selectedTab === 'witnesses' && (
            <>
              {selectedWitness ? (
                <>
                  <div className="current-suspect">
                    <div className="suspect-header">
                      <div className="suspect-avatar-large witness-badge">👁️</div>
                      <div className="suspect-details">
                        <h2>{selectedWitness.name}</h2>
                        <p className="suspect-background">{selectedWitness.relationshipToCase}</p>
                        <div className="suspect-tags">
                          <span className="personality-tag">{selectedWitness.occupation}</span>
                          {selectedWitness.personalityTraits?.map((trait, i) => (
                            <span key={i} className="personality-tag">{trait}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="conversation-area conversation-area--with-tips">
                    {selectedWitness?.timeline && (
                      <div className="actor-timeline-card">
                        <div className="actor-timeline-card__header">⏱ 时间线</div>
                        <div className="actor-timeline-card__body">
                          <div className="actor-timeline-card__bar" />
                          <p className="actor-timeline-card__text">{selectedWitness.timeline}</p>
                        </div>
                      </div>
                    )}
                    <div className="conversation-messages">
                      {(witnessConversationsByWitnessId[selectedWitness.id] || []).length === 0 ? (
                        <div className="no-messages"><p>开始询问证人{selectedWitness.name}。</p></div>
                      ) : (
                        (witnessConversationsByWitnessId[selectedWitness.id] || []).map((msg, idx) => (
                          <div key={idx} className={`message message--${msg.role === 'witness' ? 'suspect' : msg.role}`}>
                            <div className="message-avatar">
                              {msg.role === 'user' ? '🔍' : '👁️'}
                            </div>
                            <div className="message-content">
                              {msg.role === 'witness' ? (
                                <SelectableMessage
                                  text={msg.content}
                                  senderName={selectedWitness.name}
                                  onExtract={(text) => setPendingExtractText(text)}
                                />
                              ) : (
                                <>
                                  <div className="message-sender">你</div>
                                  <div className="message-text">{msg.content}</div>
                                </>
                              )}
                              {msg.timestamp && (
                                <div className="message-time">{new Date(msg.timestamp).toLocaleTimeString()}</div>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                      {renderCredibilityCard()}
                      {isProcessing && processingActorId === selectedWitness.id && (
                        <div className="message message--suspect">
                          <div className="message-avatar">👁️</div>
                          <div className="message-content">
                            <div className="suspect-typing">
                              <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
                            </div>
                          </div>
                        </div>
                      )}
                      <div ref={messagesEndRef} />
                    </div>

                    <div className="question-input-area">
                      <input
                        type="text"
                        className="question-input"
                        placeholder={inputPlaceholder}
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendQuestion() }
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

                  <WatsonTipsPanel tips={witnessWatsonTips} isLoading={witnessWatsonTipsLoading} />
                </>
              ) : (
                <div className="no-suspect-selected">
                  <p>{witnesses.length === 0 ? '本案暂无证人' : '请选择一位证人开始询问'}</p>
                </div>
              )}
            </>
          )}

          {/* === 专家 Tab === */}
          {selectedTab === 'experts' && (
            <>
              {selectedExpert ? (
                <>
                  {/* 专家信息栏 */}
                  <div className="current-suspect">
                    <div className="suspect-header">
                      <div className="suspect-avatar-large expert-badge">🔬</div>
                      <div className="suspect-details">
                        <h2>{selectedExpert.name}</h2>
                        <p className="suspect-background">{selectedExpert.title}</p>
                        <div className="suspect-tags">
                          {selectedExpert.expertise?.map((item, i) => (
                            <span key={i} className="personality-tag">{item}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 专家初步报告卡片 */}
                  {expertReportLoadedById[selectedExpert.id] && selectedExpert.preliminaryReport && (
                    <div className="expert-report-card">
                      <div className="expert-report-card__header">
                        <span className="expert-report-card__icon">📋</span>
                        <div>
                          <div className="expert-report-card__name">{selectedExpert.name}·初步报告</div>
                          <div className="expert-report-card__title">{selectedExpert.title}</div>
                        </div>
                      </div>
                      <div className="expert-report-card__body">{selectedExpert.preliminaryReport}</div>
                      {selectedExpert.keyFindings?.length > 0 && (
                        <div className="expert-report-card__findings">
                          {selectedExpert.keyFindings.map((f, i) => (
                            <div key={i} className="expert-report-card__finding-item">
                              <span className="finding-topic">{f.topic}：</span>
                              <span>{f.finding}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {selectedExpert.relatedClueIds?.length > 0 && (
                        <div className="expert-report-card__sources">
                          依据: {selectedExpert.relatedClueIds.join(', ')}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="conversation-area">
                    <div className="conversation-messages">
                      {(expertConversationsByExpertId[selectedExpert.id] || []).length === 0 && !expertReportLoadedById[selectedExpert.id] ? (
                        <div className="no-messages"><p>正在加载法医初步报告，请稍候...</p></div>
                      ) : (expertConversationsByExpertId[selectedExpert.id] || []).length === 0 ? (
                        <div className="no-messages"><p>向{selectedExpert.name}提出你的问题。</p></div>
                      ) : (
                        (expertConversationsByExpertId[selectedExpert.id] || []).map((msg, idx) => {
                          // 首条专家消息（初步报告）不再重复显示
                          if (idx === 0 && msg.role === 'expert' && expertReportLoadedById[selectedExpert.id]) return null
                          return (
                            <div key={idx} className={`message message--${msg.role === 'expert' ? 'suspect' : msg.role}`}>
                              <div className="message-avatar">
                                {msg.role === 'user' ? '🔍' : '🔬'}
                              </div>
                              <div className="message-content">
                                {msg.role === 'expert' ? (
                                  <SelectableMessage
                                    text={msg.content}
                                    senderName={selectedExpert.name}
                                    onExtract={(text) => setPendingExtractText(text)}
                                  />
                                ) : (
                                  <>
                                    <div className="message-sender">你</div>
                                    <div className="message-text">{msg.content}</div>
                                  </>
                                )}
                                {msg.timestamp && (
                                  <div className="message-time">{new Date(msg.timestamp).toLocaleTimeString()}</div>
                                )}
                              </div>
                            </div>
                          )
                        })
                      )}
                      {isProcessing && processingActorId === selectedExpert.id && (
                        <div className="message message--suspect">
                          <div className="message-avatar">🔬</div>
                          <div className="message-content">
                            <div className="suspect-typing">
                              <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
                            </div>
                          </div>
                        </div>
                      )}
                      <div ref={messagesEndRef} />
                    </div>

                    <div className="question-input-area">
                      <input
                        type="text"
                        className="question-input"
                        placeholder={inputPlaceholder}
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendQuestion() }
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
                  <p>{experts.length === 0 ? '本案暂无专家' : '请选择专家开始咨询'}</p>
                </div>
              )}
            </>
          )}

        </section>
      </main>

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
          <span>已审讯: {gameState.interviewedSuspectIds?.length || 0} / {suspects.length}</span>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to={`/deduction/${gameId}`} className="footer-button footer-button--secondary">
            推理板
          </Link>
          <Link to={`/conclusion/${gameId}`} className="footer-button footer-button--next">
            下一步: 结案
          </Link>
        </div>
      </footer>

      {/* 出示线索 Modal */}
      {showClueSelector && selectedTab === 'suspects' && mode === 'private' && (
        <ClueSelectorModal
          clues={clues}
          onSelect={handleConfrontClue}
          onClose={() => setShowClueSelector(false)}
        />
      )}

      {/* 提取线索 Modal */}
      {pendingExtractText && (
        <ExtractClueModal
          quotedText={pendingExtractText}
          onConfirm={handleExtractConfirm}
          onClose={() => setPendingExtractText(null)}
        />
      )}

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

        /* 角色面板（左栏，含 Tab） */
        .actors-panel {
          width: 280px;
          background: rgba(0, 0, 0, 0.4);
          border: 1px solid #333;
          border-radius: 8px;
          display: flex;
          flex-direction: column;
        }

        /* Tab 切换 */
        .actor-tabs {
          display: flex;
          border-bottom: 1px solid #333;
        }

        .actor-tab {
          flex: 1;
          padding: 0.65rem 0.25rem;
          background: transparent;
          border: none;
          color: #a0a0a0;
          cursor: pointer;
          font-family: 'Georgia', serif;
          font-size: 0.85rem;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.3rem;
        }

        .actor-tab:hover {
          color: #d4af37;
          background: rgba(212, 175, 55, 0.06);
        }

        .actor-tab--active {
          color: #d4af37;
          border-bottom: 2px solid #d4af37;
          background: rgba(212, 175, 55, 0.08);
        }

        .actor-tab__count {
          font-size: 0.75rem;
          background: rgba(212, 175, 55, 0.2);
          color: #d4af37;
          border-radius: 8px;
          padding: 0.1rem 0.4rem;
          min-width: 18px;
          text-align: center;
        }

        .panel-content {
          flex: 1;
          padding: 1rem;
          overflow-y: auto;
        }

        .actor-list-empty {
          color: #555;
          font-size: 0.9rem;
          text-align: center;
          padding: 1rem 0;
          list-style: none;
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

        /* 证人头像：蓝色系 */
        .witness-badge {
          background: linear-gradient(135deg, #6495ed 0%, #4169e1 100%) !important;
        }

        /* 专家头像：绿色系 */
        .expert-badge {
          background: linear-gradient(135deg, #3cb371 0%, #2e8b57 100%) !important;
        }

        .suspect-info {
          flex: 1;
          min-width: 0;
        }

        .suspect-name {
          color: #d4af37;
          font-weight: bold;
          font-size: 0.95rem;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .suspect-age {
          color: #666;
          font-size: 0.85rem;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        /* 审讯室 */
        .interrogation-room {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 1rem;
          min-width: 0;
        }

        .no-suspect-selected {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #666;
          font-size: 1.2rem;
        }

        /* 当前角色信息卡 */
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

        /* 专家初步报告卡片 */
        .expert-report-card {
          background: rgba(46, 139, 87, 0.08);
          border: 1px solid rgba(46, 139, 87, 0.4);
          border-radius: 8px;
          padding: 1.25rem;
          animation: messageSlideIn 0.3s ease;
        }

        .expert-report-card__header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 0.75rem;
        }

        .expert-report-card__icon {
          font-size: 1.5rem;
        }

        .expert-report-card__name {
          color: #3cb371;
          font-weight: bold;
          font-size: 0.95rem;
        }

        .expert-report-card__title {
          color: #666;
          font-size: 0.8rem;
        }

        .expert-report-card__body {
          color: #c8e6c9;
          line-height: 1.7;
          font-size: 0.95rem;
          margin-bottom: 0.75rem;
        }

        .expert-report-card__findings {
          border-top: 1px solid rgba(46, 139, 87, 0.3);
          padding-top: 0.75rem;
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }

        .expert-report-card__finding-item {
          font-size: 0.9rem;
          color: #a5d6a7;
        }

        .finding-topic {
          color: #3cb371;
          font-weight: bold;
        }

        .expert-report-card__sources {
          margin-top: 0.5rem;
          font-size: 0.75rem;
          color: #555;
          font-style: italic;
        }

        /* 角色时间线卡片（置顶于聊天框） */
        .actor-timeline-card {
          flex-shrink: 0;
          background: rgba(212, 175, 55, 0.04);
          border: 1px solid rgba(212, 175, 55, 0.2);
          border-radius: 6px;
          padding: 0.75rem 1rem;
          margin: 1rem 1.5rem 0;
        }

        .actor-timeline-card__header {
          font-size: 0.8rem;
          color: rgba(212, 175, 55, 0.8);
          margin-bottom: 0.5rem;
          letter-spacing: 0.05em;
        }

        .actor-timeline-card__body {
          display: flex;
          gap: 0.75rem;
          align-items: flex-start;
        }

        .actor-timeline-card__bar {
          flex-shrink: 0;
          width: 3px;
          min-height: 100%;
          align-self: stretch;
          background: linear-gradient(to bottom, rgba(212, 175, 55, 0.6), rgba(212, 175, 55, 0.15));
          border-radius: 2px;
          margin-top: 2px;
        }

        .actor-timeline-card__text {
          font-family: 'Courier New', 'Courier', monospace;
          font-size: 0.82rem;
          color: rgba(255, 255, 255, 0.7);
          line-height: 1.7;
          white-space: pre-wrap;
          margin: 0;
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
          max-height: calc(100vh - 400px);
          min-height: 400px;
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

        /* 打字动画 */
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

        .lie-detection-icon { font-size: 1.5rem; }
        .lie-detection-content { flex: 1; }

        .lie-detection-title {
          color: #ff9800;
          font-weight: bold;
          margin-bottom: 0.5rem;
        }

        .lie-detection--ok .lie-detection-title { color: #4caf50; }

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

        .lie-detection-notes { color: #a0a0a0; font-size: 0.9rem; }

        /* 证人可信度检测 */
        .credibility-check {
          display: flex;
          gap: 1rem;
          padding: 1rem;
          border-radius: 8px;
          margin-top: 0.5rem;
        }

        .credibility-check--warning {
          background: rgba(255, 152, 0, 0.1);
          border: 1px solid rgba(255, 152, 0, 0.3);
        }

        .credibility-check--ok {
          background: rgba(100, 149, 237, 0.1);
          border: 1px solid rgba(100, 149, 237, 0.3);
        }

        .credibility-check__icon { font-size: 1.5rem; }
        .credibility-check__content { flex: 1; }

        .credibility-check__title {
          color: #6495ed;
          font-weight: bold;
          margin-bottom: 0.5rem;
        }

        .credibility-check--warning .credibility-check__title { color: #ff9800; }

        .credibility-check__microexpression {
          color: #a0a0a0;
          font-style: italic;
          margin-bottom: 0.25rem;
        }

        .credibility-check__confidence {
          color: #888;
          font-size: 0.9rem;
          margin-bottom: 0.25rem;
        }

        .credibility-check__notes { color: #a0a0a0; font-size: 0.9rem; }

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

        .question-input::placeholder { color: #666; }

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

        .send-button:disabled { opacity: 0.4; cursor: not-allowed; }

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

        .footer-button--back:hover { border-color: #888; color: #fff; }

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

        .footer-button--secondary {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid #8b7355;
          color: #c9a962;
          text-decoration: none;
        }

        .footer-button--secondary:hover:not(:disabled) {
          background: rgba(139, 115, 85, 0.2);
          border-color: #a08060;
          transform: translateY(-1px);
        }

        .footer-button:disabled { opacity: 0.4; cursor: not-allowed; }

        .footer-progress { color: #a0a0a0; font-size: 1rem; }

        /* 全体质询 */
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

        .group-suspects-panel .panel-header h3 { color: #d4af37; font-size: 1.1rem; }
        .atmosphere-indicator { color: #ff9800; font-size: 0.9rem; }

        .group-suspects-list { display: flex; gap: 1rem; flex-wrap: wrap; }

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

        .group-suspect-item--quiet { opacity: 0.5; }

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

        .group-suspect-info { display: flex; flex-direction: column; }
        .group-suspect-name { color: #d4af37; font-weight: bold; font-size: 0.9rem; }
        .group-suspect-status { color: #666; font-size: 0.75rem; }

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

        .contradiction-alert:hover { background: rgba(255, 152, 0, 0.2); }
        .contradiction-alert__icon { font-size: 1.5rem; }
        .contradiction-alert__content { flex: 1; }

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

        .contradiction-alert__close { color: #666; font-size: 1.25rem; cursor: pointer; }

        /* 控场按钮栏 */
        .group-control-bar { display: flex; gap: 0.75rem; }

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

        .group-control-btn:hover { background: rgba(212, 175, 55, 0.2); border-color: #d4af37; }

        /* 插话消息 */
        .message--interjection { opacity: 0.9; }

        .message-text--interjection {
          background: rgba(156, 39, 176, 0.1) !important;
          border-color: rgba(156, 39, 176, 0.3) !important;
          font-style: italic;
        }

        /* 全体质询输入区 */
        .question-input-area--group { position: relative; }

        .mention-input-wrapper { flex: 1; position: relative; }

        .question-input--textarea { width: 100%; resize: none; min-height: 60px; line-height: 1.5; }

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

        .mention-menu-item:first-child { border-radius: 8px 8px 0 0; }
        .mention-menu-item:last-child { border-radius: 0 0 8px 8px; }
        .mention-menu-item:hover { background: rgba(212, 175, 55, 0.15); }
        .mention-menu-item--active { background: rgba(212, 175, 55, 0.2); border-left: 3px solid #d4af37; }

        .message--system .message-text {
          background: rgba(103, 58, 183, 0.1) !important;
          border-color: rgba(103, 58, 183, 0.3) !important;
          text-align: center;
        }

        .message--system .message-sender { display: none; }

        /* P2: 出示线索按钮 */
        .confront-clue-btn {
          padding: 0.75rem 1rem;
          background: rgba(212, 175, 55, 0.15);
          border: 1px solid rgba(212, 175, 55, 0.4);
          color: #d4af37;
          border-radius: 6px;
          font-size: 0.9rem;
          font-family: 'Georgia', serif;
          cursor: pointer;
          transition: all 0.3s ease;
          white-space: nowrap;
        }
        .confront-clue-btn:hover:not(:disabled) {
          background: rgba(212, 175, 55, 0.25);
          border-color: #d4af37;
        }
        .confront-clue-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        /* P2: 出示线索消息气泡 */
        .message-text--clue-confront {
          background: rgba(212, 175, 55, 0.12) !important;
          border-color: rgba(212, 175, 55, 0.5) !important;
          border-left: 4px solid #d4af37 !important;
          font-style: italic;
        }

        /* P3: 嫌疑人状态徽章 */
        .suspect-state-badge {
          font-size: 0.7rem;
          padding: 0.15rem 0.5rem;
          border-radius: 10px;
          margin-left: 0.5rem;
          white-space: nowrap;
          vertical-align: middle;
        }
        .suspect-state-badge--calm {
          background: rgba(160, 160, 160, 0.15);
          color: #a0a0a0;
          border: 1px solid rgba(160, 160, 160, 0.3);
        }
        .suspect-state-badge--pressured {
          background: rgba(255, 152, 0, 0.15);
          color: #ff9800;
          border: 1px solid rgba(255, 152, 0, 0.3);
        }
        .suspect-state-badge--broken {
          background: rgba(244, 67, 54, 0.15);
          color: #f44336;
          border: 1px solid rgba(244, 67, 54, 0.3);
        }

        /* P3: 嫌疑人列表项状态边框 */
        .suspect-item--broken {
          border-color: rgba(244, 67, 54, 0.5) !important;
          background: rgba(244, 67, 54, 0.06) !important;
        }

        /* P2: 线索选择器 Modal */
        .clue-selector-modal { max-width: 480px; }
        .clue-selector-modal__body { max-height: 360px; overflow-y: auto; }
        .clue-selector-empty { color: #888; text-align: center; padding: 2rem 0; }
        .clue-selector-list { list-style: none; display: flex; flex-direction: column; gap: 0.5rem; }
        .clue-selector-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.75rem 1rem;
          background: rgba(255,255,255,0.03);
          border: 1px solid #2a2a3a;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .clue-selector-item:hover { border-color: #d4af37; background: rgba(212,175,55,0.08); }
        .clue-selector-item--selected { border-color: #d4af37; background: rgba(212,175,55,0.12); }
        .clue-selector-item__label { color: #e8e8e8; font-size: 0.95rem; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 0.75rem; }

        /* P2: 线索状态徽章 */
        .clue-status-badge {
          font-size: 0.75rem;
          padding: 0.15rem 0.5rem;
          border-radius: 10px;
          white-space: nowrap;
        }
        .clue-status-badge--verified { background: rgba(76, 175, 80, 0.2); color: #4caf50; border: 1px solid rgba(76, 175, 80, 0.3); }
        .clue-status-badge--unverified { background: rgba(160, 160, 160, 0.15); color: #a0a0a0; border: 1px solid rgba(160, 160, 160, 0.3); }
        .clue-status-badge--refuted { background: rgba(244, 67, 54, 0.15); color: #f44336; border: 1px solid rgba(244, 67, 54, 0.3); }

        .clue-selector-modal__footer { display: flex; justify-content: flex-end; gap: 0.75rem; padding: 1rem; border-top: 1px solid #333; }
        .modal-btn {
          padding: 0.5rem 1.25rem;
          border-radius: 6px;
          font-family: 'Georgia', serif;
          font-size: 0.9rem;
          cursor: pointer;
          transition: all 0.2s ease;
          border: none;
        }
        .modal-btn--secondary { background: rgba(255,255,255,0.05); color: #a0a0a0; border: 1px solid #555; }
        .modal-btn--secondary:hover { border-color: #888; color: #fff; }
        .modal-btn--primary { background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%); color: #1a1a2e; font-weight: bold; }
        .modal-btn--primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(212,175,55,0.4); }
        .modal-btn:disabled { opacity: 0.4; cursor: not-allowed; }

        /* ─── 移动端响应式 ─── */
        @media (max-width: 1024px) {
          .interrogation-main {
            flex-direction: column !important;
            padding: 0.75rem;
          }

          .actors-panel {
            width: 100% !important;
            flex-direction: row !important;
            overflow: visible !important;
            flex-shrink: 0;
          }

          .actor-tabs {
            flex-direction: row !important;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            position: sticky;
            top: 0;
            z-index: 5;
            background: rgba(0, 0, 0, 0.4);
          }

          .actor-tab {
            flex: 0 0 auto !important;
            min-width: 80px;
          }

          .panel-content {
            display: none !important;
          }

          .tips-panel {
            display: none !important;
          }

          .interrogation-room {
            width: 100% !important;
          }
        }

        @media (max-width: 768px) {
          .interrogation-header {
            padding: 0.75rem 1rem;
          }

          .header-content {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 0.4rem;
          }

          .header-title {
            font-size: 1.2rem !important;
          }

          .mode-toggle {
            flex-wrap: wrap;
          }

          .mode-button {
            padding: 0.4rem 0.75rem;
            font-size: 0.85rem;
          }

          .conversation-area {
            min-height: calc(100dvh - 320px) !important;
            max-height: none !important;
          }

          .message-content {
            max-width: 85% !important;
          }

          .question-input-area {
            padding: 0.75rem 1rem !important;
            padding-bottom: max(0.75rem, env(safe-area-inset-bottom)) !important;
          }

          .question-input {
            font-size: 16px !important;
          }

          .interrogation-footer {
            flex-wrap: wrap !important;
            gap: 8px !important;
            padding: 0.75rem 1rem !important;
            padding-bottom: max(0.75rem, env(safe-area-inset-bottom)) !important;
          }

          .actor-timeline-card {
            margin: 0.5rem 0.75rem 0 !important;
          }

          .current-suspect {
            padding: 1rem !important;
          }

          .suspect-avatar-large {
            width: 56px !important;
            height: 56px !important;
            font-size: 1.75rem !important;
          }

          .suspect-details h2 {
            font-size: 1.25rem !important;
          }
        }
      `}</style>

      {/* 华生对话框 */}
      <WatsonChatDialog gameId={gameId!} />

      {showToast && (
        <Toast message={toastMessage} onDismiss={() => setShowToast(false)} />
      )}
    </div>
  )
}
